"""Read-only validator for atomic-quantum simulation evidence.

OPlague accepts explicitly supplied reports; this module never reads or mutates host devices.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

CATALOGUE_PATH = Path(__file__).resolve().parents[1] / "schemas" / "atomic-quantum-functions.v1.json"
REPORT_SCHEMA = "ivan-vhs.atomic-quantum-report.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

class AtomicQuantumEvidenceError(ValueError):
    """Invalid catalogue or simulation evidence."""

def load_catalogue() -> dict[str, Any]:
    try:
        data = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AtomicQuantumEvidenceError(f"cannot read the atomic quantum catalogue: {error}") from error
    items = data.get("functions")
    if data.get("function_count") != 133 or not isinstance(items, list) or len(items) != 133:
        raise AtomicQuantumEvidenceError("catalogue must contain exactly 133 function records")
    ids = [item.get("id") for item in items if isinstance(item, dict)]
    if len(ids) != 133 or len(set(ids)) != 133:
        raise AtomicQuantumEvidenceError("catalogue IDs must be 133 unique strings")
    return data

def known_function(function_id: str) -> bool:
    if not isinstance(function_id, str):
        return False
    return any(item["id"] == function_id for item in load_catalogue()["functions"])

def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise AtomicQuantumEvidenceError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise AtomicQuantumEvidenceError(f"{label} must be finite")
    return result

def validate_report(report: Any) -> dict[str, Any]:
    """Validate a detached report without promoting simulated data to observed evidence."""
    if not isinstance(report, dict) or report.get("schema") != REPORT_SCHEMA:
        raise AtomicQuantumEvidenceError(f"report schema must be {REPORT_SCHEMA}")
    function_id = report.get("function_id")
    if not known_function(function_id):
        raise AtomicQuantumEvidenceError(f"unknown function_id: {function_id!r}")
    quality = report.get("quality")
    if quality not in {"simulated", "estimated", "observed"}:
        raise AtomicQuantumEvidenceError("quality must be simulated, estimated, or observed")
    source_hash = report.get("source_sha256")
    if not isinstance(source_hash, str) or not _SHA256.fullmatch(source_hash):
        raise AtomicQuantumEvidenceError("source_sha256 must be a 64-character lowercase SHA-256 digest")
    start = report.get("window_start_epoch")
    end = report.get("window_end_epoch")
    if isinstance(start, bool) or not isinstance(start, int) or isinstance(end, bool) or not isinstance(end, int):
        raise AtomicQuantumEvidenceError("time window endpoints must be integer Unix timestamps")
    if start < 0 or end < start:
        raise AtomicQuantumEvidenceError("time window must be non-negative and ordered")
    sample_count = report.get("sample_count")
    if isinstance(sample_count, bool) or not isinstance(sample_count, int) or sample_count < 1:
        raise AtomicQuantumEvidenceError("sample_count must be a positive integer")
    metrics = report.get("metrics")
    if not isinstance(metrics, dict) or not metrics:
        raise AtomicQuantumEvidenceError("metrics must be a non-empty object")
    normalized: dict[str, dict[str, Any]] = {}
    for name, item in metrics.items():
        if not isinstance(name, str) or not name.strip() or not isinstance(item, dict):
            raise AtomicQuantumEvidenceError("each metric needs a non-empty name and object value")
        unit = item.get("unit")
        if not isinstance(unit, str) or not unit.strip():
            raise AtomicQuantumEvidenceError(f"metric {name!r} requires a unit")
        value = _finite_number(item.get("value"), f"{name}.value")
        uncertainty = _finite_number(item.get("absolute_uncertainty"), f"{name}.absolute_uncertainty")
        if uncertainty < 0:
            raise AtomicQuantumEvidenceError(f"{name}.absolute_uncertainty cannot be negative")
        normalized[name] = {"value": value, "unit": unit, "absolute_uncertainty": uncertainty}
    return {
        "schema": REPORT_SCHEMA,
        "function_id": function_id,
        "quality": quality,
        "source_sha256": source_hash,
        "window_start_epoch": start,
        "window_end_epoch": end,
        "sample_count": sample_count,
        "metrics": normalized,
        "read_only": True,
        "evidence_class": quality,
    }

def summarize_report(report: Any) -> dict[str, Any]:
    clean = validate_report(report)
    values = [row["value"] for row in clean["metrics"].values()]
    uncertainties = [row["absolute_uncertainty"] for row in clean["metrics"].values()]
    return {
        "function_id": clean["function_id"],
        "quality": clean["quality"],
        "metric_count": len(values),
        "mean_value": math.fsum(values) / len(values),
        "max_absolute_uncertainty": max(uncertainties),
        "sample_count": clean["sample_count"],
        "read_only": True,
        "advisory_only": True,
    }

def compare_metric_records(left: Any, right: Any, metric: str) -> dict[str, Any]:
    """Compare equivalent, disjoint-source evidence records; never compares unlike windows."""
    a, b = validate_report(left), validate_report(right)
    if a["source_sha256"] == b["source_sha256"]:
        raise AtomicQuantumEvidenceError("comparison requires distinct source digests")
    keys = ("quality", "window_start_epoch", "window_end_epoch")
    if any(a[key] != b[key] for key in keys):
        raise AtomicQuantumEvidenceError("reports must have equal quality and exact time windows")
    try:
        x, y = a["metrics"][metric], b["metrics"][metric]
    except KeyError as error:
        raise AtomicQuantumEvidenceError(f"metric not present in both reports: {metric}") from error
    if x["unit"] != y["unit"]:
        raise AtomicQuantumEvidenceError("metric units must match")
    delta = y["value"] - x["value"]
    combined = x["absolute_uncertainty"] + y["absolute_uncertainty"]
    return {
        "metric": metric,
        "unit": x["unit"],
        "delta": delta,
        "combined_absolute_uncertainty": combined,
        "uncertainty_envelopes_disjoint": abs(delta) > combined,
        "quality": a["quality"],
        "advisory_only": True,
    }

__all__ = [
    "AtomicQuantumEvidenceError", "load_catalogue", "known_function",
    "validate_report", "summarize_report", "compare_metric_records",
]
