from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "report_envelope.py"
SPEC = importlib.util.spec_from_file_location("report_envelope", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
report_envelope = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(report_envelope)


class ReportEnvelopeTests(unittest.TestCase):
    def test_builds_shared_envelope_and_preserves_tool_result(self):
        result = {"frames": 128, "peak_dbfs": -1.0}
        report = report_envelope.build_envelope(
            tool="ventusample",
            version="2.1.0",
            commit="ABCDEF012345678",
            result=result,
            created="2026-11-22T06:00:00Z",
            os_name="linux",
            architecture="x86_64",
        )
        self.assertEqual(report["envelope"], "ivan-vhs.report.v1")
        self.assertEqual(report["tool"]["commit"], "abcdef012345678")
        self.assertEqual(report["result"], result)
        self.assertIn("processing is offline", report["limitations"])
        self.assertEqual(report["input"], {"kind": "none", "sha256": None})

    def test_hashes_input_without_disclosing_its_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private-source.bin"
            path.write_bytes(b"local source bytes")
            digest = report_envelope.sha256_file(path)
            report = report_envelope.build_envelope(
                tool="oplague",
                version="1.0",
                commit=None,
                result={"observations": []},
                input_kind="file",
                input_sha256=digest,
                created="2026-11-22T06:00:00Z",
            )
        self.assertEqual(report["input"]["sha256"], digest)
        self.assertNotIn("private-source.bin", json.dumps(report))

    def test_hash_input_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bin"
            source.write_bytes(b"safe")
            linked = root / "linked.bin"
            try:
                linked.symlink_to(source)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are not available on this host")
            with self.assertRaisesRegex(report_envelope.EnvelopeError, "symbolic link"):
                report_envelope.sha256_file(linked)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are POSIX-only")
    def test_hash_input_rejects_fifo_without_blocking(self):
        with tempfile.TemporaryDirectory() as directory:
            pipe = Path(directory) / "input.pipe"
            os.mkfifo(pipe)
            with self.assertRaisesRegex(report_envelope.EnvelopeError, "regular file"):
                report_envelope.sha256_file(pipe)

    def test_hash_input_enforces_actual_read_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "growing.bin"
            source.write_bytes(b"12345")
            previous = report_envelope.MAX_HASH_FILE_BYTES
            report_envelope.MAX_HASH_FILE_BYTES = 4
            try:
                with self.assertRaisesRegex(report_envelope.EnvelopeError, "4-byte limit"):
                    report_envelope.sha256_file(source)
            finally:
                report_envelope.MAX_HASH_FILE_BYTES = previous

    def test_nesting_scanner_ignores_brackets_inside_json_strings(self):
        payload = '{"text":"' + ("[{" * 1000) + '"}'
        self.assertEqual(report_envelope._read_result(io.StringIO(payload))["text"], "[{" * 1000)

    def test_rejects_invalid_commit_and_hash(self):
        with self.assertRaises(report_envelope.EnvelopeError):
            report_envelope.build_envelope(
                tool="reaper", version="1", commit="not-a-hash", result={}
            )
        with self.assertRaises(report_envelope.EnvelopeError):
            report_envelope.build_envelope(
                tool="pytyliki", version="1", commit=None, result={}, input_sha256="123"
            )

    def test_rejects_non_utc_timestamp_and_empty_limitations(self):
        with self.assertRaises(report_envelope.EnvelopeError):
            report_envelope.build_envelope(
                tool="pytyliki", version="1", commit=None, result={},
                created="2026-11-22T06:00:00+02:00",
            )
        with self.assertRaises(report_envelope.EnvelopeError):
            report_envelope.build_envelope(
                tool="pytyliki", version="1", commit=None, result={}, limitations=["  "]
            )

    def test_timestamp_must_be_a_real_iso8601_utc_datetime(self):
        with self.assertRaisesRegex(report_envelope.EnvelopeError, "valid ISO-8601"):
            report_envelope.build_envelope(
                tool="oplague", version="1", commit=None, result={},
                created="not-a-timestampZ",
            )

    def test_result_limit_counts_utf8_bytes_not_characters(self):
        previous_limit = report_envelope.MAX_RESULT_BYTES
        report_envelope.MAX_RESULT_BYTES = 4
        try:
            self.assertEqual(report_envelope._read_result(io.StringIO('"é"')), "é")
            with self.assertRaisesRegex(report_envelope.EnvelopeError, "4-byte limit"):
                report_envelope._read_result(io.StringIO('"éé"'))
        finally:
            report_envelope.MAX_RESULT_BYTES = previous_limit

    def test_json_result_rejects_duplicate_keys_at_any_depth(self):
        with self.assertRaisesRegex(report_envelope.EnvelopeError, "duplicate object key"):
            report_envelope._read_result(io.StringIO('{"outer":{"value":1,"value":2}}'))

    def test_json_result_rejects_non_standard_non_finite_numbers(self):
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(report_envelope.EnvelopeError, "non-finite"):
                    report_envelope._read_result(io.StringIO('{"metric":' + value + "}"))

    def test_json_result_rejects_exponent_overflow(self):
        with self.assertRaisesRegex(report_envelope.EnvelopeError, "non-finite"):
            report_envelope._read_result(io.StringIO('{"metric":1e999}'))

    def test_json_result_bounds_integer_token_length(self):
        oversized = "1" * (report_envelope.MAX_JSON_INTEGER_DIGITS + 1)
        with self.assertRaisesRegex(report_envelope.EnvelopeError, "digit limit"):
            report_envelope._read_result(io.StringIO('{"count":' + oversized + "}"))

    def test_json_result_translates_excessive_nesting(self):
        deeply_nested = "[" * (report_envelope.MAX_JSON_NESTING_DEPTH + 1) + "0" + "]" * (report_envelope.MAX_JSON_NESTING_DEPTH + 1)
        with self.assertRaisesRegex(report_envelope.EnvelopeError, "nesting"):
            report_envelope._read_result(io.StringIO(deeply_nested))

    def test_programmatic_envelope_rejects_non_finite_result_values(self):
        with self.assertRaisesRegex(report_envelope.EnvelopeError, "finite JSON-compatible"):
            report_envelope.build_envelope(
                tool="oplague", version="1", commit=None,
                result={"metric": float("inf")},
            )

    def test_project_limitations_are_added_once(self):
        report = report_envelope.build_envelope(
            tool="oplague", version="1", commit=None, result={},
            limitations=["analysis is read-only", "local review only"],
        )
        self.assertEqual(report["limitations"].count("analysis is read-only"), 1)
        self.assertIn("local review only", report["limitations"])


if __name__ == "__main__":
    unittest.main()
