"""Explicit-path bridge to Reaper's versioned native C17 expression ABI.

Loading a shared library executes native code. Only a caller-selected absolute
regular file is accepted; this module never searches PATH or environment variables.
"""
from __future__ import annotations

import ctypes
from functools import lru_cache
from pathlib import Path
from typing import Any

ABI_VERSION = 1
MAX_SOURCE_BYTES = 1_048_576
_CHAR_POINTER = ctypes.POINTER(ctypes.c_char)
_INT64_POINTER = ctypes.POINTER(ctypes.c_int64)
_UINT64_POINTER = ctypes.POINTER(ctypes.c_uint64)


@lru_cache(maxsize=8)
def _library(explicit_path: str) -> ctypes.CDLL:
    path = Path(explicit_path).expanduser()
    if not path.is_absolute():
        raise ValueError("Reaper library path must be absolute and explicit")
    if path.is_symlink():
        raise ValueError("Reaper library path must not be a symlink")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ValueError(f"Reaper library does not exist: {path}") from error
    if not resolved.is_file():
        raise ValueError(f"Reaper library path is not a regular file: {resolved}")
    try:
        library = ctypes.CDLL(str(resolved))
    except OSError as error:
        raise ValueError(f"cannot load trusted Reaper library {resolved}: {error}") from error

    try:
        version = library.reaper_abi_version
        version.argtypes = []
        version.restype = ctypes.c_uint32
        actual = int(version())
    except (AttributeError, OSError, TypeError) as error:
        raise ValueError("library does not expose reaper_abi_version") from error
    if actual != ABI_VERSION:
        raise ValueError(f"unsupported Reaper ABI version {actual}; expected {ABI_VERSION}")

    try:
        evaluate = library.reaper_v1_eval_i64
        evaluate.argtypes = [
            ctypes.c_char_p, ctypes.c_uint64, _INT64_POINTER,
            _CHAR_POINTER, ctypes.c_uint64,
        ]
        evaluate.restype = ctypes.c_int32
        lookup = library.reaper_v1_selfhood_lookup
        lookup.argtypes = [ctypes.c_char_p, _UINT64_POINTER]
        lookup.restype = ctypes.c_int32
    except (AttributeError, OSError) as error:
        raise ValueError(f"Reaper ABI v1 symbol is missing: {error}") from error
    return library


def evaluate_i64(expression: str, library_path: str | Path) -> int:
    """Evaluate one bounded signed-i64 Reaper expression."""
    if not isinstance(expression, str):
        raise TypeError("expression must be text")
    if "\x00" in expression:
        raise ValueError("expression must not contain NUL")
    try:
        source = expression.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("expression must be valid UTF-8 text") from error
    if not source or len(source) > MAX_SOURCE_BYTES:
        raise ValueError(f"expression must contain 1..{MAX_SOURCE_BYTES} UTF-8 bytes")
    library = _library(str(library_path))
    output = ctypes.c_int64()
    error = ctypes.create_string_buffer(512)
    status = int(library.reaper_v1_eval_i64(
        source, len(source), ctypes.byref(output), error, len(error)
    ))
    if status != 0:
        detail = error.value.decode("utf-8", errors="replace")
        raise ValueError(detail or f"Reaper ABI v1 evaluation failed with status {status}")
    return int(output.value)


def lookup_selfhood(identity: str, library_path: str | Path) -> int:
    """Return the stable 1-based ordinal of an exact Reaper identity term."""
    if not isinstance(identity, str):
        raise TypeError("identity must be text")
    if not identity or "\x00" in identity:
        raise ValueError("identity must be non-empty text without NUL")
    try:
        encoded = identity.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError("identity must be valid UTF-8 text") from error
    library = _library(str(library_path))
    ordinal = ctypes.c_uint64()
    status = int(library.reaper_v1_selfhood_lookup(encoded, ctypes.byref(ordinal)))
    if status == -10:
        raise KeyError(f"unknown Reaper selfhood identity: {identity!r}")
    if status != 0:
        raise ValueError(f"Reaper ABI v1 selfhood lookup failed with status {status}")
    return int(ordinal.value)
