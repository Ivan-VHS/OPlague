from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import pytyliki_ffi


class FakeFunction:
    def __init__(self, callback):
        self.callback = callback
        self.argtypes = None
        self.restype = None

    def __call__(self, *args):
        return self.callback(*args)


class FakeLibrary:
    def __init__(self, version=1):
        self.pytyliki_abi_version = FakeFunction(lambda: version)
        self.pytyliki_v1_distance_f64 = FakeFunction(self.distance)

    @staticmethod
    def distance(left, right, count, output):
        output._obj.value = sum((left[index] - right[index]) ** 2 for index in range(count)) ** 0.5
        return 0


class PytylikiFfiTests(unittest.TestCase):
    def setUp(self):
        pytyliki_ffi._library.cache_clear()

    def tearDown(self):
        pytyliki_ffi._library.cache_clear()

    def test_explicit_native_distance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            with patch("tools.pytyliki_ffi.ctypes.CDLL", return_value=FakeLibrary()) as loader:
                result = pytyliki_ffi.euclidean_distance([3, 4], [0, 0], str(path))
                self.assertEqual(result, 5.0)
                self.assertEqual(loader.call_count, 1)

    def test_rejects_implicit_path_and_abi_mismatch(self):
        with self.assertRaisesRegex(ValueError, "absolute"):
            pytyliki_ffi.euclidean_distance([1], [0], "pytyliki_ffi.dll")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            with self.assertRaisesRegex(ValueError, "unsupported Pytyliki ABI"):
                with patch("tools.pytyliki_ffi.ctypes.CDLL", return_value=FakeLibrary(2)):
                    pytyliki_ffi.euclidean_distance([1], [0], str(path))

    def test_rejects_nonfinite_and_mismatched_vectors(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            pytyliki_ffi._vector([float("nan")], "vector")
        with self.assertRaisesRegex(ValueError, "same dimension"):
            pytyliki_ffi.euclidean_distance([1, 2], [1], "/no/such/library")


if __name__ == "__main__":
    unittest.main()
