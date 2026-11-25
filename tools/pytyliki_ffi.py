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
