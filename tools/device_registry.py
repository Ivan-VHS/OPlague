"""Versioned JSON registry, hardware snapshots, and deterministic snapshot diff."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

REGISTRY_SCHEMA = "oplage.device-registry"
REGISTRY_VERSION = 1
MAX_DEVICES = 100_000
MAX_PACKAGES = 100_000
MAX_SNAPSHOTS = 10_000


class RegistryError(ValueError):
    """Invalid, unsupported, or unsafe registry content."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise RegistryError(f"registry data is not JSON-safe: {error}") from error


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RegistryError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def new_registry() -> dict[str, Any]:
    return {
        "schema": REGISTRY_SCHEMA,
        "schema_version": REGISTRY_VERSION,
        "revision": 0,
        "updated_at": utc_now(),
        "devices": [],
        "packages": [],
        "snapshots": [],
    }


def validate_registry(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema") != REGISTRY_SCHEMA:
        raise RegistryError(f"expected registry schema {REGISTRY_SCHEMA}")
    if type(value.get("schema_version")) is not int or value["schema_version"] != REGISTRY_VERSION:
        raise RegistryError(f"unsupported registry schema version: {value.get('schema_version')!r}")
    if type(value.get("revision")) is not int or value["revision"] < 0:
        raise RegistryError("registry revision must be a non-negative integer")
    for field, limit in (("devices", MAX_DEVICES), ("packages", MAX_PACKAGES), ("snapshots", MAX_SNAPSHOTS)):
        records = value.get(field)
        if not isinstance(records, list) or len(records) > limit:
            raise RegistryError(f"{field} must be an array with at most {limit} entries")
        if any(not isinstance(record, dict) for record in records):
            raise RegistryError(f"every {field} entry must be an object")
    _assert_unique(value["devices"], lambda row: row.get("instance_id") or row.get("pnp_id"), "device instance ID")
    _assert_unique(value["packages"], lambda row: row.get("sha256") or row.get("package_id"), "package identity")
    _assert_unique(value["snapshots"], lambda row: row.get("snapshot_id"), "snapshot ID")
    for snapshot in value["snapshots"]:
        required = ("captured_at", "label", "devices", "packages", "metrics")
        if any(field not in snapshot for field in required):
            raise RegistryError("snapshot is missing one or more required fields")
        payload = {field: snapshot[field] for field in required}
        expected_id = hashlib.sha256(_canonical(payload)).hexdigest()
        if snapshot.get("snapshot_id") != expected_id:
            raise RegistryError("snapshot content digest mismatch")
    _canonical(value)
    return value


def _assert_unique(records: list[dict[str, Any]], key_fn: Any, label: str) -> None:
    seen: set[str] = set()
    for record in records:
        raw = key_fn(record)
        if raw is None:
            raise RegistryError(f"{label} is required")
        key = str(raw).strip().casefold()
        if not key or key in seen:
            raise RegistryError(f"missing or duplicate {label}: {raw!r}")
        seen.add(key)


def load_registry(path: str | os.PathLike[str]) -> dict[str, Any]:
    source = Path(path)
    if source.is_symlink():
        raise RegistryError("registry file cannot be a symbolic link")
    try:
        value = json.loads(source.read_text(encoding="utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=lambda token: (_ for _ in ()).throw(RegistryError(f"invalid JSON number: {token}")))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RegistryError(f"cannot read registry: {error}") from error
    return validate_registry(value)


def save_registry(path: str | os.PathLike[str], registry: Mapping[str, Any]) -> Path:
    value = validate_registry(dict(registry))
    destination = Path(path)
    if destination.is_symlink():
        raise RegistryError("registry destination cannot be a symbolic link")
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n"
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, destination)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
    return destination


def create_snapshot(devices: list[Mapping[str, Any]], packages: list[Mapping[str, Any]] | None = None,
                    metrics: Mapping[str, Any] | None = None, label: str = "", captured_at: str | None = None) -> dict[str, Any]:
    if not isinstance(devices, list) or len(devices) > MAX_DEVICES or any(not isinstance(row, Mapping) for row in devices):
        raise RegistryError("snapshot devices must be a bounded list of objects")
    package_rows = packages or []
    if not isinstance(package_rows, list) or len(package_rows) > MAX_PACKAGES or any(not isinstance(row, Mapping) for row in package_rows):
        raise RegistryError("snapshot packages must be a bounded list of objects")
    if not isinstance(label, str) or len(label) > 256:
        raise RegistryError("snapshot label must be a string of at most 256 characters")
    metric_values = dict(metrics or {})
    payload = {
        "captured_at": captured_at or utc_now(),
        "label": label,
        "devices": [dict(row) for row in devices],
        "packages": [dict(row) for row in package_rows],
        "metrics": metric_values,
    }
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    snapshot = {"snapshot_id": digest, **payload}
    _canonical(snapshot)
    return snapshot


def append_snapshot(registry: Mapping[str, Any], snapshot: Mapping[str, Any]) -> dict[str, Any]:
    result = json.loads(_canonical(dict(registry)).decode("utf-8"))
    validate_registry(result)
    candidate = dict(snapshot)
    if not isinstance(candidate.get("snapshot_id"), str) or len(candidate["snapshot_id"]) != 64:
        raise RegistryError("snapshot must contain a SHA-256 snapshot_id")
    required = ("captured_at", "label", "devices", "packages", "metrics")
    if any(field not in candidate for field in required):
        raise RegistryError("snapshot is missing one or more required fields")
    expected_id = hashlib.sha256(_canonical({field: candidate[field] for field in required})).hexdigest()
    if candidate["snapshot_id"] != expected_id:
        raise RegistryError("snapshot content digest mismatch")
    if any(row["snapshot_id"] == candidate["snapshot_id"] for row in result["snapshots"]):
        raise RegistryError("snapshot already exists in registry")
    result["snapshots"].append(candidate)
    for field in ("devices", "packages"):
        if field in candidate:
            rows = candidate[field]
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise RegistryError(f"snapshot {field} must be an array of objects")
            result[field] = [dict(row) for row in rows]
    result["revision"] += 1
    result["updated_at"] = utc_now()
    return validate_registry(result)


def _record_key(record: Mapping[str, Any], kind: str) -> str:
    fields = ("instance_id", "pnp_id", "device_id", "id") if kind == "device" else ("sha256", "package_id", "id")
    for field in fields:
        value = record.get(field)
        if value is not None and str(value).strip():
            return str(value).strip().casefold()
    raise RegistryError(f"{kind} record has no stable identity field ({', '.join(fields)})")


def _index_records(records: Any, kind: str) -> dict[str, Mapping[str, Any]]:
    if not isinstance(records, list):
        raise RegistryError(f"snapshot {kind}s must be an array")
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        if not isinstance(record, Mapping):
            raise RegistryError(f"snapshot {kind} entry must be an object")
        key = _record_key(record, kind)
        if key in result:
            raise RegistryError(f"duplicate {kind} identity in snapshot: {key}")
        result[key] = record
    return result


def _diff_records(before: dict[str, Mapping[str, Any]], after: dict[str, Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    added = [{"key": key, "record": dict(after[key])} for key in sorted(after.keys() - before.keys())]
    removed = [{"key": key, "record": dict(before[key])} for key in sorted(before.keys() - after.keys())]
    changed = []
    for key in sorted(before.keys() & after.keys()):
        left, right = before[key], after[key]
        fields = sorted(set(left) | set(right))
        changes = {field: {"before": left.get(field), "after": right.get(field)}
                   for field in fields if left.get(field) != right.get(field)}
        if changes:
            changed.append({"key": key, "changes": changes})
    return {"added": added, "removed": removed, "changed": changed}


def snapshot_diff(before: Mapping[str, Any], after: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise TypeError("before and after snapshots must be objects")
    devices = _diff_records(_index_records(before.get("devices", []), "device"),
                            _index_records(after.get("devices", []), "device"))
    packages = _diff_records(_index_records(before.get("packages", []), "package"),
                             _index_records(after.get("packages", []), "package"))
    left_metrics, right_metrics = before.get("metrics", {}), after.get("metrics", {})
    if not isinstance(left_metrics, Mapping) or not isinstance(right_metrics, Mapping):
        raise RegistryError("snapshot metrics must be objects")
    metric_deltas = {}
    for name in sorted(set(left_metrics) | set(right_metrics)):
        left, right = left_metrics.get(name), right_metrics.get(name)
        if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
            metric_deltas[name] = {"before": left, "after": right, "delta": right - left}
        elif left != right:
            metric_deltas[name] = {"before": left, "after": right, "delta": None}
    return {
        "schema": "oplage.snapshot-diff.v1",
        "before_snapshot_id": before.get("snapshot_id"),
        "after_snapshot_id": after.get("snapshot_id"),
        "devices": devices,
        "packages": packages,
        "metric_deltas": metric_deltas,
        "totals": {
            "devices_added": len(devices["added"]), "devices_removed": len(devices["removed"]),
            "devices_changed": len(devices["changed"]), "packages_added": len(packages["added"]),
            "packages_removed": len(packages["removed"]), "packages_changed": len(packages["changed"]),
        },
    }
