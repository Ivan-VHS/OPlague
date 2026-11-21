"""Deterministic composition of read-only OPlague package inspection reports."""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from typing import Any

MAX_REPORTS = 256
MAX_TOTAL_REPORTED_BYTES = 64 * 1024 * 1024 * 1024
MAX_METADATA_FIELDS = 64
MAX_METADATA_VALUE_LENGTH = 4096
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _count(value: Any, field: str, *, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    if value < 0 or (maximum is not None and value > maximum):
        raise ValueError(f"{field} is outside the permitted range")
    return value


def _safe_name(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a string")
    value = value.strip()
    if not value or len(value) > 512 or "\x00" in value:
        raise ValueError(f"{field} is empty or too long")
    return value


def _metadata(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise TypeError("INF metadata must be a mapping")
    if len(value) > MAX_METADATA_FIELDS:
        raise ValueError("INF metadata contains too many fields")
    result: dict[str, str] = {}
    for key, item in value.items():
        safe_key = _safe_name(key, "INF metadata key")
        safe_value = _safe_name(item, f"INF metadata value for {safe_key}")
        if len(safe_value) > MAX_METADATA_VALUE_LENGTH:
            raise ValueError(f"INF metadata value is too long: {safe_key}")
        result[safe_key] = safe_value
    return dict(sorted(result.items(), key=lambda pair: pair[0].casefold()))


def _archive_names(value: Any, field: str, *, dictionaries: bool = False) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{field} must be a list")
    if len(value) > 10_000:
        raise ValueError(f"{field} contains too many entries")
    result: list[str] = []
    for item in value:
        if dictionaries:
            if not isinstance(item, Mapping):
                raise TypeError(f"{field} entries must be mappings")
            item = item.get("file")
        result.append(_safe_name(item, f"{field} entry"))
    return result


def compose_inspection_reports(reports: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Compose already-inspected report dictionaries into a canonical summary.

    The input sequence is kept in its supplied order. Duplicate package digests
    are rejected to prevent accidentally double-counting the same inspected file.
    The bundle digest fingerprints this summary; it is not a vendor signature.
    """
    packages: list[dict[str, Any]] = []
    seen_digests: set[str] = set()
    total_bytes = 0
    total_entries = 0
    total_expanded = 0
    total_inf_files = 0
    total_catalogs = 0

    for report in reports:
        if len(packages) >= MAX_REPORTS:
            raise ValueError(f"inspection bundle exceeds MAX_REPORTS={MAX_REPORTS}")
        if not isinstance(report, Mapping):
            raise TypeError("each inspection report must be a mapping")

        file_name = _safe_name(report.get("file_name"), "file_name")
        file_format = _safe_name(report.get("format"), "format").upper()
        if file_format not in {"INF", "ZIP"}:
            raise ValueError(f"unsupported report format: {file_format}")
        size_bytes = _count(report.get("size_bytes"), "size_bytes")
        digest = _safe_name(report.get("sha256"), "sha256").lower()
        if not _SHA256_RE.fullmatch(digest):
            raise ValueError(f"invalid SHA-256 digest for {file_name}")
        if digest in seen_digests:
            raise ValueError(f"duplicate package digest: {digest}")
        seen_digests.add(digest)

        package: dict[str, Any] = {
            "file_name": file_name,
            "format": file_format,
            "size_bytes": size_bytes,
            "sha256": digest,
        }
        if file_format == "INF":
            package["inf_metadata"] = _metadata(report.get("inf_metadata"))
            inf_count = 1
            catalog_names: list[str] = []
            entry_count = 0
            expanded_bytes = 0
        else:
            entry_count = _count(report.get("entry_count", 0), "entry_count", maximum=10_000)
            expanded_bytes = _count(
                report.get("expanded_size_bytes", 0),
                "expanded_size_bytes",
                maximum=2 * 1024 * 1024 * 1024,
            )
            inf_names = _archive_names(report.get("inf_files"), "inf_files", dictionaries=True)
            catalog_names = _archive_names(report.get("catalog_files"), "catalog_files")
            package["entry_count"] = entry_count
            package["expanded_size_bytes"] = expanded_bytes
            package["inf_files"] = inf_names
            package["catalog_files"] = catalog_names
            inf_count = len(inf_names)

        total_bytes += size_bytes
        total_entries += entry_count
        total_expanded += expanded_bytes
        total_inf_files += inf_count
        total_catalogs += len(catalog_names)
        if total_bytes > MAX_TOTAL_REPORTED_BYTES:
            raise ValueError("inspection bundle exceeds the total reported-byte limit")
        if total_expanded > MAX_REPORTS * 2 * 1024 * 1024 * 1024:
            raise ValueError("inspection bundle exceeds the total expanded-byte limit")
        packages.append(package)

    if not packages:
        raise ValueError("at least one inspection report is required")

    bundle: dict[str, Any] = {
        "schema": "oplage.inspection-bundle.v1",
        "packages": packages,
        "totals": {
            "packages": len(packages),
            "reported_bytes": total_bytes,
            "archive_entries": total_entries,
            "expanded_bytes": total_expanded,
            "inf_files": total_inf_files,
            "catalog_files": total_catalogs,
        },
    }
    canonical = json.dumps(
        bundle, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    bundle["bundle_sha256"] = hashlib.sha256(canonical).hexdigest()
    return bundle
