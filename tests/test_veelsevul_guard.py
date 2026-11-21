import unittest

from veelsevul_guard import AppGuard


class AppGuardTests(unittest.TestCase):
    def setUp(self):
        self.findings = []
        self.guard = AppGuard(self.findings.append)

    def test_payload_ceiling_and_audit(self):
        self.assertTrue(self.guard.check_payload(
            128, 128, level_id=192, rule_id="A-11", object_id="driver-package"
        ))
        self.assertFalse(self.guard.check_payload(
            129, 128, level_id=192, rule_id="A-11", object_id="driver-package"
        ))
        self.assertEqual([x["decision"] for x in self.findings], ["allow", "deny"])
        self.assertEqual(self.findings[1]["level_id"], "L192")
        self.assertNotIn("secret", repr(self.findings).lower())

    def test_relative_archive_paths(self):
        self.assertTrue(self.guard.check_relative_path(
            "drivers/device/driver.inf", level_id=163, rule_id="A-12", object_id="archive-entry"
        ))
        self.assertTrue(self.guard.check_relative_path(
            "drivers/", level_id=163, rule_id="A-12", object_id="archive-directory"
        ))
        for bad in ("../outside.inf", "/etc/passwd", "C:\\Windows\\x.inf",
                    "a/../../b", "a//b", "a/./b", "a\\..\\b"):
            with self.subTest(path=bad):
                self.assertFalse(self.guard.check_relative_path(
                    bad, level_id=163, rule_id="A-12", object_id="archive-entry"
                ))

    def test_collection_limit(self):
        self.assertTrue(self.guard.check_collection(
            10, 10, level_id=167, rule_id="A-09", object_id="driver-archive"
        ))
        self.assertFalse(self.guard.check_collection(
            11, 10, level_id=167, rule_id="A-09", object_id="driver-archive"
        ))

    def test_bad_policy_context_fails_closed(self):
        self.assertFalse(self.guard.check_payload(
            1, 10, level_id=667, rule_id="A-09", object_id="package"
        ))
        self.assertFalse(self.guard.check_identifier(
            "device/driver", level_id=511, rule_id="A-13", object_id="plugin-id"
        ))

    def test_audit_sink_failure_fails_closed(self):
        def broken_sink(_finding):
            raise RuntimeError("audit sink unavailable")
        guard = AppGuard(broken_sink)
        self.assertFalse(guard.check_payload(
            1, 10, level_id=192, rule_id="A-11", object_id="package"
        ))


if __name__ == "__main__":
    unittest.main()
