"""Validated, read-only history analysis for OPlague device snapshots."""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from tools.federation import _read_json, _validated_metrics

MAX_HISTORY = 5_000


def _timestamp(snapshot: Mapping[str, Any], label: str) -> datetime:
    value = snapshot.get("captured_utc")
    if not isinstance(value, str):
        raise ValueError(f"{label}.captured_utc must be date-time text")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{label}.captured_utc must be ISO 8601") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{label}.captured_utc must include a timezone")
    if parsed.utcoffset() != timedelta(0):
        raise ValueError(f"{label}.captured_utc must be normalized to UTC")
    return parsed


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a real number")
    try:
        number = float(value)
    except OverflowError as error:
        raise ValueError(f"{label} exceeds the float64 range") from error
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    return number


def analyze_snapshot_history(
    snapshots: Sequence[Mapping[str, Any]],
    *,
    expected_interval_seconds: Any | None = None,
    tolerance_ratio: Any = 0.25,
) -> dict[str, Any]:
    """Validate snapshots and describe device-metric stability and capture cadence."""
    if not isinstance(snapshots, (list, tuple)) or not 3 <= len(snapshots) <= MAX_HISTORY:
        raise ValueError(f"snapshots must contain 3..{MAX_HISTORY} records")

    timestamps: list[datetime] = []
    profiles: list[dict[str, float]] = []
    digests: list[str] = []
    for index, snapshot in enumerate(snapshots):
        label = f"snapshots[{index}]"
        metrics = _validated_metrics(snapshot, label)
        timestamp = _timestamp(snapshot, label)
        if timestamps and timestamp <= timestamps[-1]:
            raise ValueError("snapshots must be supplied in strictly increasing capture-time order")
        timestamps.append(timestamp)
        profiles.append(dict(metrics))
        digests.append(str(snapshot["snapshot_sha256"]))

    dimensions = sorted(profiles[0])
    expected_dimensions = set(dimensions)
    for index, profile in enumerate(profiles[1:], start=1):
        if set(profile) != expected_dimensions:
            raise ValueError(f"snapshots[{index}] metric dimensions differ from snapshots[0]")

    intervals = [
        (timestamps[index] - timestamps[index - 1]).total_seconds()
        for index in range(1, len(timestamps))
    ]
    if any(not math.isfinite(value) or value <= 0.0 for value in intervals):
        raise ValueError("capture intervals must be positive and finite")

    if expected_interval_seconds is None:
        expected_interval = float(statistics.median(intervals))
    else:
        expected_interval = _finite_number(expected_interval_seconds, "expected_interval_seconds")
    tolerance = _finite_number(tolerance_ratio, "tolerance_ratio")
    if not 1e-6 <= expected_interval <= 365 * 24 * 60 * 60:
        raise ValueError("expected_interval_seconds is outside supported bounds")
    if not 0.0 < tolerance <= 1.0:
        raise ValueError("tolerance_ratio must be within (0, 1]")

    mean_interval = math.fsum(intervals) / len(intervals)
    variance = (
        math.fsum((value - mean_interval) ** 2 for value in intervals) / (len(intervals) - 1)
        if len(intervals) > 1 else 0.0
    )
    deviation = math.sqrt(variance)
    coefficient = deviation / mean_interval
    bias = (mean_interval - expected_interval) / expected_interval
    split = len(intervals) // 2
    first_mean = math.fsum(intervals[:split]) / split
    second_mean = math.fsum(intervals[split:]) / (len(intervals) - split)
    drift = (second_mean - first_mean) / expected_interval
    cadence_penalty = coefficient + abs(bias) + 0.5 * abs(drift)
    cadence_score = 100.0 * (1.0 - min(1.0, cadence_penalty / tolerance))
    if not all(math.isfinite(value) for value in (mean_interval, variance, deviation, coefficient, bias, drift, cadence_score)):
        raise ValueError("capture cadence calculation exceeded the finite numeric range")

    metric_stability: dict[str, dict[str, float | int]] = {}
    stability_scores = []
    for name in dimensions:
        values = [profile[name] for profile in profiles]
        mean = math.fsum(values) / len(values)
        metric_variance = math.fsum((value - mean) ** 2 for value in values) / (len(values) - 1)
        span = max(values) - min(values)
        score = 100.0 * (1.0 - min(1.0, span))
        metric_stability[name] = {
            "count": len(values),
            "mean": mean,
            "sample_standard_deviation": math.sqrt(metric_variance),
            "minimum": min(values),
            "maximum": max(values),
            "range": span,
            "first_to_last_delta": values[-1] - values[0],
            "stability_score": score,
        }
        stability_scores.append(score)

    average_stability = math.fsum(stability_scores) / len(stability_scores)
    overall_score = math.sqrt(max(0.0, cadence_score) * max(0.0, average_stability))
    return {
        "schema": "oplage.snapshot-history-analysis.v1",
        "mode": "read_only",
        "snapshot_count": len(snapshots),
        "first_captured_utc": timestamps[0].isoformat(),
        "last_captured_utc": timestamps[-1].isoformat(),
        "snapshot_sha256": digests,
        "capture_cadence": {
            "interval_count": len(intervals),
            "expected_interval_seconds": expected_interval,
            "mean_interval_seconds": mean_interval,
            "sample_standard_deviation_seconds": deviation,
            "coefficient_of_variation": coefficient,
            "relative_bias": bias,
            "relative_drift": drift,
            "cadence_score": cadence_score,
        },
        "metric_stability": metric_stability,
        "average_metric_stability_score": average_stability,
        "overall_descriptive_score": overall_score,
        "semantics": (
            "Descriptive history analysis only. Stable metrics do not establish "
            "driver authenticity, compatibility, safety or a recommended action."
        ),
    }


def _write_report_atomically(destination: Path, rendered: str) -> None:
    """Replace a report atomically without following or overwriting a symlink."""
    if destination.is_symlink():
        raise ValueError(f"refusing to write through a symbolic link: {destination}")
    if destination.exists() and not destination.is_file():
        raise ValueError(f"report destination must be a regular file: {destination}")
    if not destination.parent.is_dir():
        raise ValueError(f"output directory does not exist: {destination.parent}")

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{destination.name}.",
            suffix=".tmp",
            dir=destination.parent,
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        if os.name == "posix":
            temporary_path.chmod(0o600)
        os.replace(temporary_path, destination)
        temporary_path = None
        if os.name == "posix":
            directory_fd = os.open(destination.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and analyze a chronological series of OPlague snapshots"
    )
    parser.add_argument("--snapshot", action="append", required=True, help="snapshot JSON path; provide at least three in chronological order")
    parser.add_argument("--expected-interval-seconds", type=float, help="expected capture interval; defaults to the observed median")
    parser.add_argument("--tolerance-ratio", type=float, default=0.25)
    parser.add_argument("--output", help="also write the report to this path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        snapshots = [_read_json(path) for path in args.snapshot]
        report = analyze_snapshot_history(
            snapshots,
            expected_interval_seconds=args.expected_interval_seconds,
            tolerance_ratio=args.tolerance_ratio,
        )
        rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            destination = Path(args.output)
            _write_report_atomically(destination, rendered)
        sys.stdout.write(rendered)
    except (OSError, ValueError, TypeError, OverflowError) as error:
        print(f"OPlague snapshot history: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
