"""Read-only OPlague snapshot and comparison interchange for Reaper."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import secrets
import json
import math
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Mapping, Sequence
from typing import Any

from tools.metric_analysis import analyze_device_profiles
from tools.udrv_inspector import PackageError, inspect_package

SNAPSHOT_SCHEMA = "oplage.device-snapshot.v1"
COMPARISON_SCHEMA = "oplage.device-audit.v1"
MAX_DEVICES = 10_000
MAX_JSON_BYTES = 16 * 1024 * 1024


class InventoryError(RuntimeError):
    """Raised when a safe read-only PnP inventory cannot be collected."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: str | os.PathLike[str]) -> Any:
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("JSON input must be a regular, non-symlink file")
    if source.stat().st_size > MAX_JSON_BYTES:
        raise ValueError(f"JSON file exceeds {MAX_JSON_BYTES} bytes")
    raw = source.read_bytes()
    if len(raw) > MAX_JSON_BYTES:
        raise ValueError(f"JSON file exceeds {MAX_JSON_BYTES} bytes")
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON number: {value}")))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid UTF-8 JSON: {error}") from error


def capture_pnp_devices(*, timeout_seconds: int = 30) -> list[dict[str, Any]]:
    """Run a fixed, non-mutating Get-PnpDevice query on Windows."""
    if os.name != "nt":
        raise InventoryError("PnP inventory is available only on Windows")
    executable = shutil.which("pwsh") or shutil.which("powershell")
    if not executable:
        raise InventoryError("PowerShell was not found; no device scan was run")
    # Static command: no caller-supplied text is interpolated into PowerShell.
    command = (
        "$ErrorActionPreference = 'Stop'; "
        "Import-Module PnpDevice -ErrorAction Stop; "
        "$rows = @(Get-PnpDevice -PresentOnly | "
        "Select-Object Status, Class, FriendlyName, InstanceId, Problem); "
        "ConvertTo-Json -InputObject $rows -Depth 3 -Compress"
    )
    kwargs: dict[str, Any] = {
        "capture_output": True, "text": True, "encoding": "utf-8",
        "errors": "replace", "timeout": timeout_seconds, "check": False,
    }
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    try:
        completed = subprocess.run(
            [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command],
            **kwargs,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise InventoryError(f"PowerShell PnP query could not complete: {error}") from error
    if completed.returncode != 0:
        detail = completed.stderr.strip()[:1000] or "PowerShell returned a failure code"
        raise InventoryError(f"read-only PnP query failed: {detail}")
    if len(completed.stdout.encode("utf-8")) > MAX_JSON_BYTES:
        raise InventoryError("PnP response exceeds the 16 MiB safety limit")
    try:
        records = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as error:
        raise InventoryError(f"PowerShell returned invalid JSON: {error}") from error
    if isinstance(records, dict):
        records = [records]
    if not isinstance(records, list) or len(records) > MAX_DEVICES:
        raise InventoryError(f"PnP response must contain at most {MAX_DEVICES} devices")
    if any(not isinstance(item, dict) for item in records):
        raise InventoryError("PnP response contains a non-object device record")
    return records


def _safe_text(value: Any, limit: int = 256) -> str:
    if value is None:
        return ""
    return str(value).strip()[:limit]


def _problem_code(value: Any) -> tuple[int | None, bool]:
    if value is None or value == "":
        return None, False
    if isinstance(value, bool):
        return None, value
    if isinstance(value, int):
        return value, value != 0
    if isinstance(value, str):
        text = value.strip()
        if text.isdecimal():
            number = int(text)
            return number, number != 0
        return None, True
    return None, True


def _normalize_devices(
    devices: Sequence[Mapping[str, Any]], *, identity_key: bytes
) -> list[dict[str, Any]]:
    if not isinstance(identity_key, bytes) or len(identity_key) < 32:
        raise ValueError("device identity key must contain at least 32 bytes")
    if not isinstance(devices, (list, tuple)) or len(devices) > MAX_DEVICES:
        raise ValueError(f"devices must be a list of at most {MAX_DEVICES} records")
    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(devices):
        if not isinstance(raw, Mapping):
            raise TypeError(f"devices[{index}] must be an object")
        instance_id = _safe_text(raw.get("InstanceId", raw.get("instance_id")), 2048)
        fingerprint = hmac.new(identity_key, b"oplage-device-id-v1\\0" + instance_id.encode("utf-8"), hashlib.sha256).hexdigest() if instance_id else ""
        if fingerprint and fingerprint in seen_ids:
            raise ValueError(f"duplicate PnP identity at devices[{index}]")
        if fingerprint:
            seen_ids.add(fingerprint)
        status = _safe_text(raw.get("Status", raw.get("status")), 64) or "Unknown"
        device_class = _safe_text(raw.get("Class", raw.get("class")), 128)
        friendly_name = _safe_text(raw.get("FriendlyName", raw.get("friendly_name")), 256)
        code, problem_reported = _problem_code(raw.get("Problem", raw.get("problem")))
        normalized.append({
            "identity_sha256": fingerprint, "friendly_name": friendly_name,
            "class": device_class, "status": status, "problem_code": code,
            "problem_reported": problem_reported,
        })
    return normalized


def build_device_snapshot(
    devices: Sequence[Mapping[str, Any]], *, packages: Sequence[Mapping[str, Any]] = (),
    captured_utc: str | None = None, provider: str = "windows-pnp",
    identity_key: bytes | None = None,
) -> dict[str, Any]:
    """Build a normalized snapshot; IDs are HMAC-pseudonymized, not plain hashes.

    Without a caller-managed key, each export gets a fresh ephemeral key so
    identifiers cannot be correlated across snapshots. Supplying the same
    protected key deliberately enables pseudonymous cross-snapshot matching.
    """
    key_scope = "caller_managed" if identity_key is not None else "snapshot_ephemeral"
    if identity_key is None:
        identity_key = secrets.token_bytes(32)
    if not isinstance(identity_key, bytes) or len(identity_key) < 32:
        raise ValueError("identity_key must contain at least 32 bytes")
    normalized = _normalize_devices(devices, identity_key=identity_key)
    if not isinstance(packages, (list, tuple)) or len(packages) > 256:
        raise ValueError("packages must contain at most 256 object records")
    if any(not isinstance(item, Mapping) for item in packages):
        raise TypeError("package records must be objects")
    total = len(normalized)
    ok_count = sum(item["status"].casefold() == "ok" and not item["problem_reported"] for item in normalized)
    problem_count = sum(item["problem_reported"] for item in normalized)
    class_count = sum(bool(item["class"]) for item in normalized)
    identity_count = sum(bool(item["identity_sha256"]) for item in normalized)
    package_count = len(packages)
    valid_packages = sum(item.get("valid") is True for item in packages)
    denominator = float(total) if total else 1.0
    package_denominator = float(package_count) if package_count else 1.0
    snapshot: dict[str, Any] = {
        "schema": SNAPSHOT_SCHEMA,
        "captured_utc": captured_utc or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": {"provider": provider, "mode": "read_only"},
        "identity_protection": {"algorithm": "HMAC-SHA-256", "key_scope": key_scope},
        "summary": {
            "total_devices": total, "ok_devices": ok_count,
            "problem_devices": problem_count, "other_status_devices": total - ok_count - problem_count,
            "devices_with_class": class_count, "devices_with_identity": identity_count,
            "audited_packages": package_count, "valid_packages": valid_packages,
        },
        "metrics": {
            "device_ok_ratio": ok_count / denominator if total else 0.0,
            "device_problem_free_ratio": (total - problem_count) / denominator if total else 0.0,
            "device_class_coverage_ratio": class_count / denominator if total else 0.0,
            "device_identity_coverage_ratio": identity_count / denominator if total else 0.0,
            "package_integrity_ratio": valid_packages / package_denominator if package_count else 0.0,
            "package_audit_coverage_ratio": 1.0 if package_count else 0.0,
        },
        "devices": normalized, "packages": [dict(item) for item in packages],
    }
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    snapshot["snapshot_sha256"] = hashlib.sha256(canonical).hexdigest()
    return snapshot


def load_identity_key(path: str | os.PathLike[str]) -> bytes:
    """Read a caller-managed pseudonymization key without following symlinks."""
    source = Path(path)
    if source.is_symlink() or not source.is_file():
        raise ValueError("identity key must be a regular, non-symlink file")
    if source.stat().st_size > 4096:
        raise ValueError("identity key file exceeds 4096 bytes")
    key = source.read_bytes()
    if len(key) < 32:
        raise ValueError("identity key file must contain at least 32 bytes")
    return key


def export_device_snapshot(
    devices: Sequence[Mapping[str, Any]], *, user_confirmed: bool,
    packages: Sequence[Mapping[str, Any]] = (), captured_utc: str | None = None,
    provider: str = "windows-pnp", identity_key: bytes | None = None,
) -> dict[str, Any]:
    """Export a snapshot only after an explicit operator confirmation."""
    if user_confirmed is not True:
        raise PermissionError(
            "device inventory export requires explicit user confirmation"
        )
    return build_device_snapshot(
        devices, packages=packages, captured_utc=captured_utc,
        provider=provider, identity_key=identity_key,
    )


_SNAPSHOT_REQUIRED_FIELDS = {
    "schema", "captured_utc", "source", "summary", "metrics",
    "devices", "packages", "snapshot_sha256",
}
_SNAPSHOT_SUMMARY_FIELDS = {
    "total_devices", "ok_devices", "problem_devices", "other_status_devices",
    "devices_with_class", "devices_with_identity", "audited_packages",
    "valid_packages",
}
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _validated_metrics(snapshot: Any, label: str) -> Mapping[str, float]:
    """Validate the complete v1 envelope, derived summary and canonical digest."""
    if not isinstance(snapshot, Mapping):
        raise TypeError(f"{label} must be a JSON object")
    keys = set(snapshot)
    allowed = _SNAPSHOT_REQUIRED_FIELDS | {"identity_protection"}
    missing = _SNAPSHOT_REQUIRED_FIELDS - keys
    extra = keys - allowed
    if missing or extra:
        raise ValueError(
            f"{label} fields are invalid; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    if snapshot.get("schema") != SNAPSHOT_SCHEMA:
        raise ValueError(f"{label} must use schema {SNAPSHOT_SCHEMA}")

    captured = snapshot.get("captured_utc")
    if not isinstance(captured, str):
        raise TypeError(f"{label}.captured_utc must be date-time text")
    try:
        captured_at = datetime.fromisoformat(captured.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label}.captured_utc must be an ISO 8601 date-time") from error
    if captured_at.tzinfo is None or captured_at.utcoffset() is None:
        raise ValueError(f"{label}.captured_utc must include a timezone")

    source = snapshot.get("source")
    if not isinstance(source, Mapping) or set(source) != {"provider", "mode"}:
        raise ValueError(f"{label}.source must contain provider and mode only")
    if not isinstance(source.get("provider"), str) or source.get("mode") != "read_only":
        raise ValueError(f"{label}.source must declare a provider and read_only mode")

    identity = snapshot.get("identity_protection")
    if identity is not None:
        if not isinstance(identity, Mapping) or set(identity) != {"algorithm", "key_scope"}:
            raise ValueError(f"{label}.identity_protection has an invalid shape")
        if identity.get("algorithm") != "HMAC-SHA-256" or identity.get("key_scope") not in {
            "snapshot_ephemeral", "caller_managed"
        }:
            raise ValueError(f"{label}.identity_protection is unsupported")

    summary = snapshot.get("summary")
    if not isinstance(summary, Mapping) or set(summary) != _SNAPSHOT_SUMMARY_FIELDS:
        raise ValueError(f"{label}.summary must contain the eight v1 counters")
    for name, value in summary.items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{label}.summary.{name} must be a non-negative integer")

    metrics = snapshot.get("metrics")
    if not isinstance(metrics, Mapping) or not 6 <= len(metrics) <= 128:
        raise ValueError(f"{label}.metrics must contain 6..128 normalized metrics")
    normalized: dict[str, float] = {}
    for name, raw in metrics.items():
        if not isinstance(name, str) or not name.strip() or len(name) > 128:
            raise ValueError(f"{label}.metrics contains an invalid name")
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise TypeError(f"{label}.metrics.{name} must be a real number")
        try:
            value = float(raw)
        except OverflowError as error:
            raise ValueError(f"{label}.metrics.{name} exceeds the float64 range") from error
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(f"{label}.metrics.{name} must be finite and within [0, 1]")
        normalized[name] = value

    devices = snapshot.get("devices")
    if not isinstance(devices, list) or len(devices) > MAX_DEVICES:
        raise ValueError(f"{label}.devices must contain at most {MAX_DEVICES} records")
    for index, device in enumerate(devices):
        required = {
            "identity_sha256", "friendly_name", "class", "status",
            "problem_code", "problem_reported",
        }
        if not isinstance(device, Mapping) or set(device) != required:
            raise ValueError(f"{label}.devices[{index}] has an invalid shape")
        identity_value = device.get("identity_sha256")
        if not isinstance(identity_value, str) or (
            identity_value and _SHA256_PATTERN.fullmatch(identity_value) is None
        ):
            raise ValueError(f"{label}.devices[{index}].identity_sha256 is invalid")
        for field, maximum in (("friendly_name", 256), ("class", 128), ("status", 64)):
            value = device.get(field)
            if not isinstance(value, str) or len(value) > maximum:
                raise ValueError(f"{label}.devices[{index}].{field} is invalid")
        problem_code = device.get("problem_code")
        if problem_code is not None and (
            isinstance(problem_code, bool) or not isinstance(problem_code, int)
        ):
            raise ValueError(f"{label}.devices[{index}].problem_code is invalid")
        if not isinstance(device.get("problem_reported"), bool):
            raise ValueError(f"{label}.devices[{index}].problem_reported must be boolean")

    packages = snapshot.get("packages")
    if not isinstance(packages, list) or len(packages) > 256:
        raise ValueError(f"{label}.packages must contain at most 256 records")
    if any(not isinstance(package, Mapping) for package in packages):
        raise ValueError(f"{label}.packages entries must be objects")

    total = len(devices)
    ok_count = sum(
        device["status"].casefold() == "ok" and not device["problem_reported"]
        for device in devices
    )
    problem_count = sum(device["problem_reported"] for device in devices)
    derived = {
        "total_devices": total,
        "ok_devices": ok_count,
        "problem_devices": problem_count,
        "other_status_devices": total - ok_count - problem_count,
        "devices_with_class": sum(bool(device["class"]) for device in devices),
        "devices_with_identity": sum(bool(device["identity_sha256"]) for device in devices),
        "audited_packages": len(packages),
        "valid_packages": sum(package.get("valid") is True for package in packages),
    }
    if dict(summary) != derived:
        raise ValueError(f"{label}.summary does not match its device/package records")

    declared_digest = snapshot.get("snapshot_sha256")
    if not isinstance(declared_digest, str) or _SHA256_PATTERN.fullmatch(declared_digest) is None:
        raise ValueError(f"{label}.snapshot_sha256 must be a lowercase SHA-256 digest")
    payload = dict(snapshot)
    payload.pop("snapshot_sha256")
    try:
        canonical = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{label} is not canonical JSON data: {error}") from error
    actual_digest = hashlib.sha256(canonical).hexdigest()
    if not hmac.compare_digest(declared_digest, actual_digest):
        raise ValueError(f"{label}.snapshot_sha256 fingerprint mismatch")

    return dict(sorted(normalized.items()))


def compare_device_snapshots(
    reference: Any, candidate: Any, pytyliki_library: str | None = None
) -> dict[str, Any]:
    """Compare snapshots and optionally cross-check distance through Pytyliki ABI v1."""
    reference_metrics = _validated_metrics(reference, "reference")
    candidate_metrics = _validated_metrics(candidate, "candidate")
    comparison = analyze_device_profiles(reference_metrics, candidate_metrics)
    result = {
        "schema": COMPARISON_SCHEMA, "mode": "read_only",
        "reference_snapshot_sha256": reference.get("snapshot_sha256"),
        "candidate_snapshot_sha256": candidate.get("snapshot_sha256"),
        "comparison": comparison,
    }
    if pytyliki_library is not None:
        from tools.pytyliki_ffi import euclidean_distance

        names = sorted(reference_metrics)
        native_distance = euclidean_distance(
            [reference_metrics[name] for name in names],
            [candidate_metrics[name] for name in names],
            pytyliki_library,
        )
        python_distance = float(comparison["euclidean_distance"])
        result["native_cross_check"] = {
            "backend": "pytyliki-c-abi-v1",
            "library": str(Path(pytyliki_library).expanduser().resolve()),
            "euclidean_distance": native_distance,
            "python_euclidean_distance": python_distance,
            "absolute_error": abs(native_distance - python_distance),
            "within_tolerance": math.isclose(native_distance, python_distance, rel_tol=1e-10, abs_tol=1e-12),
        }
    return result


def _package_reports(paths: Sequence[str]) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for package_path in paths:
        source = Path(package_path)
        try:
            report = inspect_package(source)
        except (PackageError, OSError, ValueError):
            reports.append({"file_name": source.name, "format": "UDRV", "valid": False})
        else:
            reports.append({"file_name": report.source, "format": "UDRV", "valid": True, **asdict(report)})
    return reports


def _emit(value: Any, output: str | None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if output:
        destination = Path(output)
        if not destination.parent.exists():
            raise ValueError(f"output directory does not exist: {destination.parent}")
        destination.write_text(text, encoding="utf-8", newline="\n")
    sys.stdout.write(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OPlague federated, read-only device snapshot and metric comparison")
    commands = parser.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot", help="capture current Windows PnP state and optional UDRV checks")
    snapshot.add_argument("--output", help="also write the JSON snapshot to this path")
    snapshot.add_argument("--confirm-inventory-export", action="store_true", help="explicitly acknowledge exporting this local device inventory")
    snapshot.add_argument("--identity-key-file", help="optional protected 32-byte-or-longer key for pseudonymous matching across exports")
    snapshot.add_argument("--package", action="append", default=[], help="UDRV directory or ZIP to inspect (repeatable)")
    compare = commands.add_parser("compare", help="compare two saved oplage.device-snapshot.v1 files")
    compare.add_argument("--reference", required=True)
    compare.add_argument("--candidate", required=True)
    compare.add_argument("--output", help="also write the JSON comparison to this path")
    compare.add_argument("--pytyliki-library", help="explicit absolute path to a trusted Pytyliki ABI v1 shared library")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "snapshot":
            if not args.confirm_inventory_export:
                raise PermissionError(
                    "snapshot export requires --confirm-inventory-export"
                )
            identity_key = load_identity_key(args.identity_key_file) if args.identity_key_file else None
            result = export_device_snapshot(
                capture_pnp_devices(), packages=_package_reports(args.package),
                user_confirmed=args.confirm_inventory_export,
                identity_key=identity_key,
            )
        else:
            result = compare_device_snapshots(
                _read_json(args.reference), _read_json(args.candidate),
                pytyliki_library=args.pytyliki_library,
            )
        _emit(result, args.output)
    except (InventoryError, OSError, ValueError, TypeError, PackageError, PermissionError) as error:
        print(f"OPlague federation: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
