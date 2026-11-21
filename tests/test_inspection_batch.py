from pathlib import Path
import tempfile
import unittest

from tools.inspection_batch import BatchInspectionBudget, inspect_batch


class BoundedBatchInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.first = self.root / "first.inf"
        self.second = self.root / "second.zip"
        self.first.write_bytes(b"first")
        self.second.write_bytes(b"second")

    def tearDown(self):
        self.temp.cleanup()

    def test_preflights_all_sources_before_inspecting(self):
        called = []
        outside = self.root / "too-large.inf"
        outside.write_bytes(b"123456")
        budget = BatchInspectionBudget(max_packages=4, max_package_bytes=10,
                                       max_total_source_bytes=10)
        with self.assertRaisesRegex(ValueError, "aggregate batch byte budget"):
            inspect_batch([self.first, self.second, outside],
                          lambda path: called.append(path), budget=budget)
        self.assertEqual(called, [])

    def test_preserves_order_and_uses_one_inspector_call_per_source(self):
        observed = []
        reports = inspect_batch(
            [self.second, self.first],
            lambda path: observed.append(Path(path).name) or {"name": Path(path).name},
        )
        self.assertEqual(observed, ["second.zip", "first.inf"])
        self.assertEqual([report["name"] for report in reports], observed)

    def test_package_count_limit(self):
        with self.assertRaisesRegex(ValueError, "more than 1 packages"):
            inspect_batch([self.first, self.second], lambda path: {},
                          budget=BatchInspectionBudget(max_packages=1))

    def test_symlinks_are_rejected(self):
        link = self.root / "linked.inf"
        try:
            link.symlink_to(self.first)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")
        with self.assertRaisesRegex(ValueError, "symbolic-link"):
            inspect_batch([link], lambda path: {})

    def test_non_package_extension_is_rejected(self):
        unknown = self.root / "payload.bin"
        unknown.write_bytes(b"bytes")
        with self.assertRaisesRegex(ValueError, "unsupported package extension"):
            inspect_batch([unknown], lambda path: {})

    def test_missing_file_is_rejected(self):
        with self.assertRaises(FileNotFoundError):
            inspect_batch([self.root / "missing.inf"], lambda path: {})


if __name__ == "__main__":
    unittest.main()
