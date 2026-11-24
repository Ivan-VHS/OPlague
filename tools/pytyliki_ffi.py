"""Explicit-path ctypes bridge to Pytyliki C ABI v1 for Device Metric Lab.

Loading a shared library executes native code. Only trusted, caller-selected
absolute paths are accepted; no implicit DLL/SO search is performed.
"""
from __future__ import annotations

import ctypes
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

ABI_VERSION = 1
MAX_VECTOR_DIMENSION = 4096
_DOUBLE_POINTER = ctypes.POINTER(ctypes.c_double)
_METRIC_QUERY_TEXT_CAP = 257
_METRIC_QUERY_MAX_PAGE = 4096


class _MetricQueryV1(ctypes.Structure):
    _fields_ = [
        ("query", ctypes.c_char * _METRIC_QUERY_TEXT_CAP),
        ("category", ctypes.c_char * _METRIC_QUERY_TEXT_CAP),
        ("required_capabilities", ctypes.c_uint32),
        ("excluded_capabilities", ctypes.c_uint32),
        ("required_type_mask", ctypes.c_uint32),
        ("excluded_type_mask", ctypes.c_uint32),
        ("offset", ctypes.c_uint64),
        ("limit", ctypes.c_uint64),
    ]


class _MetricOperationV1(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("name", ctypes.c_char * 64),
        ("category", ctypes.c_char * 64),
        ("description", ctypes.c_char * 192),
        ("complexity", ctypes.c_char * 64),
        ("type_mask", ctypes.c_uint32),
        ("capabilities", ctypes.c_uint32),
    ]


class _MetricSearchResultV1(ctypes.Structure):
    _fields_ = [
        ("total_matches", ctypes.c_uint64),
        ("written", ctypes.c_uint64),
    ]


@lru_cache(maxsize=8)
def _library(explicit_path: str) -> ctypes.CDLL:
    path = Path(explicit_path).expanduser()
    if not path.is_absolute():
        raise ValueError("Pytyliki library path must be absolute and explicit")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"Pytyliki library does not exist: {path}") from error
    if not resolved.is_file():
        raise ValueError(f"Pytyliki library path is not a file: {resolved}")
    try:
        library = ctypes.CDLL(str(resolved))
    except OSError as error:
        raise ValueError(f"cannot load trusted Pytyliki library {resolved}: {error}") from error
    try:
        version = library.pytyliki_abi_version
        version.argtypes = []
        version.restype = ctypes.c_uint32
        actual = int(version())
    except (AttributeError, OSError) as error:
        raise ValueError("shared library does not expose pytyliki_abi_version") from error
    if actual != ABI_VERSION:
        raise ValueError(f"unsupported Pytyliki ABI version {actual}; expected {ABI_VERSION}")
    try:
        function = library.pytyliki_v1_distance_f64
    except AttributeError as error:
        raise ValueError("shared library is missing pytyliki_v1_distance_f64") from error
    function.argtypes = [_DOUBLE_POINTER, _DOUBLE_POINTER, ctypes.c_uint64, _DOUBLE_POINTER]
    function.restype = ctypes.c_int32
    return library


def _vector(values: Any, label: str) -> list[float]:
    if not isinstance(values, (list, tuple)):
        raise TypeError(f"{label} must be a list")
    if not 1 <= len(values) <= MAX_VECTOR_DIMENSION:
        raise ValueError(f"{label} must contain 1..{MAX_VECTOR_DIMENSION} values")
    result: list[float] = []
    for index, raw in enumerate(values):
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise TypeError(f"{label}[{index}] must be a real number")
        try:
            value = float(raw)
        except OverflowError as error:
            raise ValueError(f"{label}[{index}] exceeds the float64 range") from error
        if not math.isfinite(value):
            raise ValueError(f"{label}[{index}] must be finite")
        result.append(value)
    return result


def euclidean_distance(left: Any, right: Any, library_path: str) -> float:
    """Calculate a bounded Euclidean distance using the explicit C ABI library."""
    a, b = _vector(left, "left vector"), _vector(right, "right vector")
    if len(a) != len(b):
        raise ValueError("vectors must have the same dimension")
    library = _library(library_path)
    left_buffer = (ctypes.c_double * len(a))(*a)
    right_buffer = (ctypes.c_double * len(b))(*b)
    output = ctypes.c_double()
    status = int(library.pytyliki_v1_distance_f64(
        left_buffer, right_buffer, len(a), ctypes.byref(output)
    ))
    if status != 0:
        raise ValueError(f"Pytyliki ABI v1 distance failed with status {status}")
    if not math.isfinite(output.value):
        raise ValueError("Pytyliki ABI returned a non-finite distance")
    return float(output.value)


def _query_text(value: Any, label: str) -> bytes:
    if value is None:
        return b""
    if not isinstance(value, str):
        raise TypeError(f"{label} must be text or None")
    if "\x00" in value:
        raise ValueError(f"{label} must not contain NUL")
    encoded = value.encode("utf-8")
    if len(encoded) >= _METRIC_QUERY_TEXT_CAP:
        raise ValueError(f"{label} must contain at most 256 UTF-8 bytes")
    return encoded


def _uint(value: Any, label: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise ValueError(f"{label} must be an integer in [0, {maximum}]")
    return value


def metric_registry_search(
    query: str | None,
    category: str | None,
    library_path: str,
    *,
    required_capabilities: int = 0,
    excluded_capabilities: int = 0,
    required_type_mask: int = 0,
    excluded_type_mask: int = 0,
    offset: int = 0,
    limit: int = 100,
    result_capacity: int | None = None,
) -> dict[str, Any]:
    """Search Pytyliki's static metric catalogue through the explicit C ABI.

    The result is metadata only. No metric operation is invoked and no pointers
    returned by the native library are retained.
    """
    encoded_query = _query_text(query, "query")
    encoded_category = _query_text(category, "category")
    masks = {
        "required_capabilities": required_capabilities,
        "excluded_capabilities": excluded_capabilities,
        "required_type_mask": required_type_mask,
        "excluded_type_mask": excluded_type_mask,
    }
    for name, value in masks.items():
        masks[name] = _uint(value, name, 0xFFFFFFFF)
    if masks["required_capabilities"] & masks["excluded_capabilities"]:
        raise ValueError("required and excluded capability masks must not overlap")
    if masks["required_type_mask"] & masks["excluded_type_mask"]:
        raise ValueError("required and excluded type masks must not overlap")
    offset_value = _uint(offset, "offset", 0xFFFFFFFFFFFFFFFF)
    limit_value = _uint(limit, "limit", _METRIC_QUERY_MAX_PAGE)
    if limit_value < 1:
        raise ValueError(f"limit must be in [1, {_METRIC_QUERY_MAX_PAGE}]")
    capacity_value = limit_value if result_capacity is None else _uint(
        result_capacity, "result_capacity", _METRIC_QUERY_MAX_PAGE
    )

    library = _library(library_path)
    try:
        function = library.pytyliki_v1_metric_registry_search
    except AttributeError as error:
        raise ValueError(
            "shared library does not expose pytyliki_v1_metric_registry_search"
        ) from error
    function.argtypes = [
        ctypes.POINTER(_MetricQueryV1),
        ctypes.POINTER(_MetricOperationV1),
        ctypes.c_uint64,
        ctypes.POINTER(_MetricSearchResultV1),
    ]
    function.restype = ctypes.c_int32

    native_query = _MetricQueryV1()
    native_query.query = encoded_query
    native_query.category = encoded_category
    native_query.required_capabilities = masks["required_capabilities"]
    native_query.excluded_capabilities = masks["excluded_capabilities"]
    native_query.required_type_mask = masks["required_type_mask"]
    native_query.excluded_type_mask = masks["excluded_type_mask"]
    native_query.offset = offset_value
    native_query.limit = limit_value

    native_results = (
        (_MetricOperationV1 * capacity_value)() if capacity_value else None
    )
    native_summary = _MetricSearchResultV1()
    status = int(function(
        ctypes.byref(native_query),
        native_results,
        capacity_value,
        ctypes.byref(native_summary),
    ))
    if status != 0:
        raise ValueError(
            f"Pytyliki ABI v1 metric search failed with status {status}"
        )
    if native_summary.written > capacity_value or native_summary.written > limit_value:
        raise ValueError("Pytyliki ABI returned a result count outside the supplied capacity")

    entries = []
    for index in range(int(native_summary.written)):
        item = native_results[index]
        entries.append({
            "id": int(item.id),
            "name": item.name.decode("utf-8", errors="strict"),
            "category": item.category.decode("utf-8", errors="strict"),
            "description": item.description.decode("utf-8", errors="strict"),
            "complexity": item.complexity.decode("utf-8", errors="strict"),
            "type_mask": int(item.type_mask),
            "capabilities": int(item.capabilities),
        })
    return {
        "schema": "pytyliki.metric-search.v1",
        "total_matches": int(native_summary.total_matches),
        "written": int(native_summary.written),
        "offset": offset_value,
        "limit": limit_value,
        "entries": entries,
        "executed": False,
    }
