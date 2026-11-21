from __future__ import annotations

import unittest

from tools.architecture_profiles import (
    TARGETS,
    detect_inf_target_architectures,
    evaluate_driver_targets,
    normalize_architecture,
    current_host_profile,
)


class ArchitectureProfileTests(unittest.TestCase):
    def test_target_catalog_has_unique_profiles(self) -> None:
        self.assertEqual([item.key for item in TARGETS], ["x86", "amd64", "arm", "arm64", "ia64"])
        self.assertEqual(len({item.inf_decoration for item in TARGETS}), len(TARGETS))

    def test_normalizes_common_host_aliases(self) -> None:
        self.assertEqual(normalize_architecture("AMD64"), "amd64")
        self.assertEqual(normalize_architecture("x86_64"), "amd64")
        self.assertEqual(normalize_architecture("AArch64"), "arm64")
        self.assertIsNone(normalize_architecture("e2k"))

    def test_e2k_host_is_not_misclassified_as_a_windows_driver_target(self) -> None:
        profile = current_host_profile("e2k")
        self.assertEqual(profile["schema"], "oplage.host-platform.v1")
        self.assertEqual(profile["platform_family"], "MCST Elbrus")
        self.assertEqual(profile["architecture"], "e2k")
        self.assertIsNone(profile["windows_driver_target"])
        self.assertEqual(profile["windows_driver_match"], "not_applicable")
        self.assertEqual(profile["package_inspection"], "available")
        self.assertEqual(profile["pnp_inventory"], "windows_only")
        self.assertIsNone(normalize_architecture("e2k"))

    def test_extracts_decorated_inf_targets(self) -> None:
        content = """
        [Manufacturer]
        %Vendor%=Models,NTamd64.10.0...19041,NTarm64.10.0
        [Models.NTamd64]
        [Models.NTarm64]
        [Models.NTx86.6.1]
        """
        self.assertEqual(detect_inf_target_architectures(content), ["amd64", "arm64", "x86"])

    def test_reports_exact_explicit_match(self) -> None:
        result = evaluate_driver_targets("AMD64", ["amd64", "arm64"])
        self.assertEqual(result["schema"], "oplage.driver-target-analysis.v1")
        self.assertEqual(result["verdict"], "explicit_match")
        self.assertEqual(result["normalized_host"], "amd64")

    def test_unknown_and_nonmatch_are_not_silent_compatibility_claims(self) -> None:
        unknown = evaluate_driver_targets("e2k", ["amd64"])
        mismatch = evaluate_driver_targets("x86", ["amd64"])
        no_evidence = evaluate_driver_targets("arm64", [])
        self.assertEqual(unknown["verdict"], "unknown")
        self.assertEqual(mismatch["verdict"], "explicit_nonmatch")
        self.assertEqual(no_evidence["verdict"], "unknown")
        self.assertTrue(mismatch["limitations"])

    def test_rejects_invalid_input_and_limits(self) -> None:
        with self.assertRaises(TypeError):
            evaluate_driver_targets("amd64", "amd64")  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            evaluate_driver_targets("amd64", [""])
        with self.assertRaises(ValueError):
            detect_inf_target_architectures("x" * (8 * 1024 * 1024 + 1))


if __name__ == "__main__":
    unittest.main()
