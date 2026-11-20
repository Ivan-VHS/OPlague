"""Read-only numerical comparison for normalized hardware metric profiles."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

MAX_METRICS = 128
MAX_SAMPLES = 1_000_000


def _finite_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _profile(values: Any, label: str) -> dict[str, float]:
    if not isinstance(values, Mapping):
        raise TypeError(f"{label} must be a JSON object of metric names and values")
    if not 1 <= len(values) <= MAX_METRICS:
        raise ValueError(f"{label} must contain 1..{MAX_METRICS} metrics")
    result: dict[str, float] = {}
    for raw_name, raw_value in values.items():
        if not isinstance(raw_name, str) or not raw_name.strip() or len(raw_name) > 128:
            raise ValueError(f"{label} contains an invalid metric name")
        name = raw_name.strip()
        if name in result:
            raise ValueError(f"{label} contains a duplicate metric name: {name}")
        number = _finite_number(raw_value, f"{label}.{name}")
        if not 0.0 <= number <= 1.0:
            raise ValueError(f"{label}.{name} must be normalized to [0, 1]")
        result[name] = number
    return result


def analyze_device_profiles(
    reference: Mapping[str, Any],
    candidate: Mapping[str, Any],
    weights: Mapping[str, Any] | None = None,
    *,
    orthogonality_tolerance: float = 1e-12,
) -> dict[str, Any]:
    """Compare same-dimension, higher-is-better profiles normalized to [0, 1]."""
    left, right = _profile(reference, "reference"), _profile(candidate, "candidate")
    if left.keys() != right.keys():
        missing = sorted(left.keys() - right.keys())
        extra = sorted(right.keys() - left.keys())
        raise ValueError(f"profile dimensions differ; candidate missing={missing}, extra={extra}")
    names = sorted(left)
    tolerance = _finite_number(orthogonality_tolerance, "orthogonality_tolerance")
    if not 0.0 <= tolerance <= 1.0:
        raise ValueError("orthogonality_tolerance must be between 0 and 1")

    weight_map: dict[str, float] = {name: 1.0 for name in names}
    if weights is not None:
        if not isinstance(weights, Mapping):
            raise TypeError("weights must be a JSON object")
        for raw_name, raw_value in weights.items():
            if raw_name not in weight_map:
                raise ValueError(f"weight supplied for unknown metric: {raw_name}")
            number = _finite_number(raw_value, f"weights.{raw_name}")
            if number < 0.0:
                raise ValueError(f"weights.{raw_name} cannot be negative")
            weight_map[raw_name] = number

    a = [left[name] for name in names]
    b = [right[name] for name in names]
    delta = [y - x for x, y in zip(a, b)]
    dot = math.fsum(x * y for x, y in zip(a, b))
    norm_a, norm_b = math.hypot(*a), math.hypot(*b)
    cosine = None if norm_a == 0.0 or norm_b == 0.0 else dot / (norm_a * norm_b)
    distance = math.hypot(*delta)
    quadratic = math.fsum(weight_map[name] * delta[index] ** 2 for index, name in enumerate(names))
    if quadratic < 0.0 or not math.isfinite(quadratic):
        raise ValueError("weighted quadratic form is outside the finite numeric range")
    components = {
        name: {
            "reference": left[name],
            "candidate": right[name],
            "difference": right[name] - left[name],
            "weighted_squared_difference": weight_map[name] * (right[name] - left[name]) ** 2,
        }
        for name in names
    }
    return {
        "schema": "oplage.device-metric-comparison.v1",
        "dimensions": names,
        "dimension_count": len(names),
        "euclidean_distance": distance,
        "weighted_distance": math.sqrt(quadratic),
        "quadratic_form": quadratic,
        "dot_product": dot,
        "cosine_similarity": cosine,
        "angle_radians": None if cosine is None else math.acos(max(-1.0, min(1.0, cosine))),
        "orthogonal": None if cosine is None else abs(cosine) <= tolerance,
        "reference_energy": math.fsum(value * value for value in a),
        "candidate_energy": math.fsum(value * value for value in b),
        "difference_energy": math.fsum(value * value for value in delta),
        "components": components,
        "normalization": "all dimensions are expected to use [0, 1], higher-is-better values",
    }


def summarize_repeated_measurements(samples: Sequence[Any]) -> dict[str, float | int]:
    """Return count, mean, sample variance and sample deviation for repeated runs."""
    if not isinstance(samples, (list, tuple)) or not 1 <= len(samples) <= MAX_SAMPLES:
        raise ValueError(f"samples must contain 1..{MAX_SAMPLES} measurements")
    values = [_finite_number(value, f"samples[{index}]") for index, value in enumerate(samples)]
    mean = math.fsum(values) / len(values)
    variance = (
        math.fsum((value - mean) ** 2 for value in values) / (len(values) - 1)
        if len(values) > 1 else 0.0
    )
    return {
        "count": len(values),
        "mean": mean,
        "sample_variance": variance,
        "sample_standard_deviation": math.sqrt(variance),
        "minimum": min(values),
        "maximum": max(values),
    }


def parseval_energy(coefficients: Sequence[Any]) -> float:
    """Sum squared coefficients; orthonormal-basis semantics are caller-owned."""
    if not isinstance(coefficients, (list, tuple)) or not 1 <= len(coefficients) <= MAX_SAMPLES:
        raise ValueError(f"coefficients must contain 1..{MAX_SAMPLES} values")
    values = [_finite_number(value, f"coefficients[{index}]") for index, value in enumerate(coefficients)]
    result = math.fsum(value * value for value in values)
    if not math.isfinite(result):
        raise ValueError("coefficient energy overflowed")
    return result


def combine_uncorrelated_variances(components: Sequence[Any]) -> float:
    """Add variance components only when their pairwise covariances are zero."""
    if not isinstance(components, (list, tuple)) or not 1 <= len(components) <= MAX_METRICS:
        raise ValueError(f"components must contain 1..{MAX_METRICS} values")
    values = [_finite_number(value, f"components[{index}]") for index, value in enumerate(components)]
    if any(value < 0.0 for value in values):
        raise ValueError("variance components cannot be negative")
    return math.fsum(values)
