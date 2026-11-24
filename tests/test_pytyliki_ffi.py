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
        self.pytyliki_v1_metric_registry_search = FakeFunction(self.metric_search)

    @staticmethod
    def distance(left, right, count, output):
        output._obj.value = sum((left[index] - right[index]) ** 2 for index in range(count)) ** 0.5
        return 0

    @staticmethod
    def metric_search(query, results, capacity, output):
        request = query._obj
        output._obj.total_matches = 4
        count = min(int(capacity), int(request.limit))
        output._obj.written = count
        names = [b"vector.norm.l2", b"vector.norm.l1", b"vector.norm.linf", b"vector.dot"]
        for index in range(count):
            results[index].id = 1002 + index
            results[index].name = names[index]
            results[index].category = b"vector-algebra"
            results[index].description = b"bounded native metric"
            results[index].complexity = b"O(n) time, O(1) extra"
            results[index].type_mask = 1
            results[index].capabilities = 5
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

    def test_explicit_native_metric_registry_search(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "libpytyliki.so"
            path.touch()
            with patch("tools.pytyliki_ffi.ctypes.CDLL", return_value=FakeLibrary()):
                result = pytyliki_ffi.metric_registry_search(
                    "vector",
                    "vector-algebra",
                    str(path),
                    required_capabilities=1,
                    excluded_capabilities=8,
                    required_type_mask=1,
                    offset=1,
                    limit=2,
                )
        self.assertEqual(result["schema"], "pytyliki.metric-search.v1")
        self.assertEqual(result["total_matches"], 4)
        self.assertEqual(result["written"], 2)
        self.assertEqual(result["entries"][0]["name"], "vector.norm.l2")
        self.assertFalse(result["executed"])

    def test_metric_registry_search_validates_all_query_parameters(self):
        with self.assertRaisesRegex(ValueError, "UTF-8 bytes"):
            pytyliki_ffi._query_text("x" * 257, "query")
        with self.assertRaisesRegex(ValueError, "overlap"):
            pytyliki_ffi.metric_registry_search(
                "vector", None, "/not/loaded",
                required_capabilities=1, excluded_capabilities=1,
            )
        with self.assertRaisesRegex(ValueError, "limit"):
            pytyliki_ffi.metric_registry_search(
                "vector", None, "/not/loaded", limit=0,
            )


if __name__ == "__main__":
    unittest.main()
