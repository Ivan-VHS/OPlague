"""DRIVE-LENS: privacy-preserving driver evidence ledger.

This module reconciles already-inspected metadata. It does not extract or run
packages, identify publishers, select a driver, or decide compatibility.
Raw device identifiers are consumed only to derive keyed pseudonyms.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
import unicodedata
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

LEDGER_SCHEMA = "oplage.driver-evidence-ledger.v1"
MAX_OBSERVATIONS = 20_000
MAX_ATTRIBUTE_LENGTH = 64
MAX_VALUE_LENGTH = 1024
MAX_LOCATOR_LENGTH = 256
_SOURCE_KINDS = {"pnp_inventory", "inf_metadata", "udrv_manifest", "catalog_metadata", "operator_note"}
_ATTR_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LOCATOR_RE = re.compile(r"^[A-Za-z0-9_.$:/#@+-]{1,256}$")
_ID_ATTRIBUTES = {"hardware_id", "instance_id", "device_instance_id", "serial", "serial_number"}


class DriverEvidenceError(ValueError):
    """Invalid or unsafe driver evidence input."""


def _text(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be text")
    result = unicodedata.normalize("NFC", value.strip())
    if not result or len(result) > maximum or "\x00" in result:
        raise ValueError(f"{field} is empty or exceeds {maximum} characters")
    return result


def _sha256(value: Any, field: str) -> str:
    result = _text(value, field, 64).lower()
    if not _SHA256_RE.fullmatch(result):
        raise ValueError(f"{field} must be a SHA-256 hex digest")
    return result


def _utc(value: Any, field: str) -> str:
    raw = _text(value, field, 64)
    try:
        parsed = datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _scalar(value: Any, attribute: str, key: bytes) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > 9_007_199_254_740_991:
            raise ValueError("integer evidence values must be within the exact JSON integer range")
        normalized: Any = value
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("evidence numeric values must be finite")
        normalized = value
    elif isinstance(value, str):
        normalized = _text(value, "evidence value", MAX_VALUE_LENGTH)
    else:
        raise TypeError("evidence value must be a scalar string, number or boolean")

    # Device and hardware identifiers can be matched without persisting their
    # raw value. The keyed digest is domain-separated by attribute name.
    sensitive = attribute in _ID_ATTRIBUTES or attribute.endswith("_id")
    if sensitive:
        if not isinstance(normalized, str):
            raise TypeError(f"{attribute} evidence must be supplied as text")
        digest = hmac.new(
            key,
            b"oplage-driver-attribute-v1\0" + attribute.encode("utf-8")
            + b"\0" + normalized.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {"pseudonym": "hmac-sha256:" + digest}
    return normalized


def _window(item: Mapping[str, Any]) -> tuple[str | None, str | None]:
    start = item.get("period_start_utc")
    end = item.get("period_end_utc")
    if (start is None) != (end is None):
        raise ValueError("period_start_utc and period_end_utc must be supplied together")
    if start is None:
        return None, None
    normalized_start = _utc(start, "period_start_utc")
    normalized_end = _utc(end, "period_end_utc")
    if normalized_start >= normalized_end:
        raise ValueError("evidence time window must have positive duration")
    return normalized_start, normalized_end


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise DriverEvidenceError(f"evidence cannot be represented as canonical JSON: {error}") from error


def build_driver_evidence_ledger(
    observations: Sequence[Mapping[str, Any]],
    *,
    identity_key: bytes,
    generated_at_utc: str,
) -> dict[str, Any]:
    """Build a bounded, deterministic evidence ledger from inspected metadata.

    Each observation must include a raw local device InstanceId, an attribute,
    scalar value, source kind, exact source artifact SHA-256, locator and UTC
    capture time. Raw InstanceId and ID-valued attributes are HMAC-pseudonymized
    and never copied into the returned ledger.
    """
    if not isinstance(identity_key, bytes) or len(identity_key) < 32:
        raise ValueError("identity_key must contain at least 32 bytes")
    if not isinstance(observations, (list, tuple)) or not 1 <= len(observations) <= MAX_OBSERVATIONS:
        raise ValueError(f"observations must contain 1..{MAX_OBSERVATIONS} records")
    generated = _utc(generated_at_utc, "generated_at_utc")

    evidence: list[dict[str, Any]] = []
    seen_evidence: set[str] = set()
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)

    for index, raw in enumerate(observations):
        if not isinstance(raw, Mapping):
            raise TypeError(f"observations[{index}] must be an object")
        instance_id = _text(
            raw.get("instance_id", raw.get("InstanceId")),
            f"observations[{index}].instance_id", 2048,
        )
        attribute = _text(raw.get("attribute"), f"observations[{index}].attribute", MAX_ATTRIBUTE_LENGTH)
        if not _ATTR_RE.fullmatch(attribute):
            raise ValueError(f"observations[{index}].attribute must be a normalized identifier")
        source_kind = _text(raw.get("source_kind"), f"observations[{index}].source_kind", 32)
        if source_kind not in _SOURCE_KINDS:
            raise ValueError(f"unsupported source_kind: {source_kind}")
        source_sha = _sha256(raw.get("source_sha256"), f"observations[{index}].source_sha256")
        captured = _utc(raw.get("captured_at_utc"), f"observations[{index}].captured_at_utc")
        locator = _text(raw.get("locator"), f"observations[{index}].locator", MAX_LOCATOR_LENGTH)
        if not _LOCATOR_RE.fullmatch(locator) or ".." in locator or locator.startswith("/"):
            raise ValueError(f"observations[{index}].locator must be a safe relative metadata locator")
        start, end = _window(raw)
        subject = hmac.new(
            identity_key,
            b"oplage-driver-subject-v1\0" + instance_id.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        normalized_value = _scalar(raw.get("value"), attribute, identity_key)

        item: dict[str, Any] = {
            "subject_ref": "hmac-sha256:" + subject,
            "attribute": attribute,
            "value": normalized_value,
            "source_kind": source_kind,
            "source_sha256": source_sha,
            "locator": locator,
            "captured_at_utc": captured,
            "period_start_utc": start,
            "period_end_utc": end,
        }
        item["evidence_id"] = hashlib.sha256(_canonical(item)).hexdigest()
        if item["evidence_id"] in seen_evidence:
            raise ValueError(f"duplicate evidence observation at index {index}")
        seen_evidence.add(item["evidence_id"])
        evidence.append(item)
        group_key = (item["subject_ref"], attribute, start, end)
        groups[group_key].append(item)

    group_records: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for key in sorted(groups, key=lambda value: tuple("" if item is None else str(item) for item in value)):
        rows = groups[key]
        values_by_digest: dict[str, Any] = {}
        for row in rows:
            values_by_digest.setdefault(hashlib.sha256(_canonical(row["value"])).hexdigest(), row["value"])
        distinct_values = [values_by_digest[digest] for digest in sorted(values_by_digest)]
        sources = sorted({row["source_sha256"] for row in rows})
        state = (
            "conflicted" if len(distinct_values) > 1
            else "multi_source_consistent" if len(sources) > 1
            else "single_source"
        )
        group_id = hashlib.sha256(_canonical({
            "subject_ref": key[0], "attribute": key[1],
            "period_start_utc": key[2], "period_end_utc": key[3],
        })).hexdigest()
        group = {
            "group_id": group_id,
            "subject_ref": key[0],
            "attribute": key[1],
            "period_start_utc": key[2],
            "period_end_utc": key[3],
            "state": state,
            "observation_count": len(rows),
            "source_count": len(sources),
            "evidence_ids": sorted(row["evidence_id"] for row in rows),
            "distinct_values": distinct_values,
        }
        group_records.append(group)
        if state == "conflicted":
            conflicts.append({
                "group_id": group_id,
                "subject_ref": key[0],
                "attribute": key[1],
                "evidence_ids": group["evidence_ids"],
                "distinct_value_count": len(distinct_values),
                "resolution": "unresolved; no source is selected automatically",
            })

    evidence.sort(key=lambda item: (item["subject_ref"], item["attribute"], item["captured_at_utc"], item["evidence_id"]))
    payload: dict[str, Any] = {
        "schema": LEDGER_SCHEMA,
        "generated_at_utc": generated,
        "identity_protection": {
            "algorithm": "HMAC-SHA-256",
            "key_scope": "caller_managed",
            "raw_identifiers_exported": False,
        },
        "mode": "read_only",
        "evidence": evidence,
        "groups": group_records,
        "conflicts": conflicts,
        "summary": {
            "subjects": len({item["subject_ref"] for item in evidence}),
            "observations": len(evidence),
            "groups": len(group_records),
            "conflicted_groups": len(conflicts),
            "multi_source_consistent_groups": sum(group["state"] == "multi_source_consistent" for group in group_records),
        },
        "semantics": {
            "matching": "exact pseudonymous subject, attribute and exact time window",
            "multi_source_consistent_is_not_independent_verification": True,
            "conflicts_are_never_auto_resolved": True,
            "compatibility_verdict": False,
        },
    }
    payload["ledger_sha256"] = hashlib.sha256(_canonical(payload)).hexdigest()
    return payload
