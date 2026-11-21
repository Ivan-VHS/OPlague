from __future__ import annotations

import ctypes
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import reaper_ffi


class _Function:
    def __init__(self, callback):
        self.callback = callback
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.callback(*args)


class _Library:
    def __init__(self, version: int = 1):
        self.reaper_abi_version = _Function(lambda: version)
        self.reaper_v1_eval_i64 = _Function(
            lambda source, length, output, error, capacity:
                self._evaluate(source, length, output)
        )
        self.reaper_v1_selfhood_lookup = _Function(
            lambda identity, ordinal: self._lookup(identity, ordinal)
        )

    @staticmethod
    def _evaluate(source, length, output):
        value = 42 if source[:length] == b"6 * 7" else 0
        output._obj.value = value
        return 0

    @staticmethod
    def _lookup(identity, ordinal):
        if identity == "Сам".encode("utf-8"):
            ordinal._obj.value = 2
            return 0
        return -10


class ReaperFfiTests(unittest.TestCase):
    def setUp(self):
        reaper_ffi._library.cache_clear()

    def tearDown(self):
        reaper_ffi._library.cache_clear()

    def test_requires_explicit_absolute_regular_file(self):
        with self.assertRaisesRegex(ValueError, "absolute"):
            reaper_ffi._library("libreaper_ffi.so")
        with tempfile.TemporaryDirectory() as directory:
            library_path = Path(directory) / "reaper.so"
            library_path.write_bytes(b"test fixture")
            with patch("tools.reaper_ffi.ctypes.CDLL", return_value=_Library()):
                self.assertEqual(reaper_ffi.evaluate_i64("6 * 7", library_path), 42)

    def test_rejects_nul_and_oversized_source_before_loading_library(self):
        with patch("tools.reaper_ffi.ctypes.CDLL") as loader:
            with self.assertRaisesRegex(ValueError, "NUL"):
                reaper_ffi.evaluate_i64("1\x002", "/absolute/reaper.so")
            with self.assertRaisesRegex(ValueError, "UTF-8 bytes"):
                reaper_ffi.evaluate_i64("x" * (reaper_ffi.MAX_SOURCE_BYTES + 1),
                                         "/absolute/reaper.so")
            loader.assert_not_called()

    def test_version_and_exact_selfhood_lookup(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reaper.so"
            path.write_bytes(b"fixture")
            fake = _Library()
            with patch("tools.reaper_ffi.ctypes.CDLL", return_value=fake):
                self.assertEqual(reaper_ffi.lookup_selfhood("Сам", path), 2)
                with self.assertRaises(KeyError):
                    reaper_ffi.lookup_selfhood("unknown", path)
            # A mismatched version is checked before symbol use.
            reaper_ffi._library.cache_clear()
            with patch("tools.reaper_ffi.ctypes.CDLL", return_value=_Library(2)):
                with self.assertRaisesRegex(ValueError, "expected 1"):
                    reaper_ffi._library(str(path))

    def test_rejects_invalid_input_types(self):
        with self.assertRaises(TypeError):
            reaper_ffi.evaluate_i64(42, "/absolute/reaper.so")
        with self.assertRaises(TypeError):
            reaper_ffi.lookup_selfhood(42, "/absolute/reaper.so")


if __name__ == "__main__":
    unittest.main()
