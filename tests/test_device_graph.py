from __future__ import annotations

import unittest

from tools.device_graph import (
    build_compatibility_graph,
    build_dry_run_plan,
    extract_inf_compatibility,
    normalize_hardware_id,
    summarize_candidate_coverage,
)


class DeviceGraphTests(unittest.TestCase):
    def test_extracts_only_model_ids_and_architecture(self):
        inf = """
[Version]
Class=Net
[Manufacturer]
%Vendor%=Models,NTamd64
[Models.NTamd64]
%Adapter%=Install, PCI\\VEN_1234&DEV_ABCD
%USB%=Install, USB\\VID_1234&PID_ABCD
[Install]
CopyFiles=Payload
"""
        result = extract_inf_compatibility(inf)
        self.assertEqual(result["architectures"], ["x64"])
        self.assertEqual(result["hardware_ids"], [
            "PCI\\VEN_1234&DEV_ABCD", "USB\\VID_1234&PID_ABCD"
        ])

    def test_exact_identifier_match_builds_candidate_edge(self):
        devices = [{"pnp_id": "PCI\\VEN_1234&DEV_ABCD", "name": "Network adapter"}]
        drivers = [{
            "driver_id": "network-package",
            "hardware_ids": ["pci\\ven_1234&dev_abcd"],
            "architectures": ["amd64"],
        }]
        graph = build_compatibility_graph(devices, drivers, host_architecture="AMD64")
        self.assertEqual(len(graph["edges"]), 1)
        self.assertEqual({node["kind"] for node in graph["nodes"]}, {"device", "driver"})
        self.assertEqual(graph["edges"][0]["status"], "exact_identifier_candidate")
        self.assertEqual(graph["edges"][0]["architecture_check"], "passed")

    def test_near_match_is_not_treated_as_compatible(self):
        graph = build_compatibility_graph(
            [{"pnp_id": "PCI\\VEN_1234&DEV_ABCD"}],
            [{"hardware_ids": ["PCI\\VEN_1234"]}],
        )
        self.assertEqual(graph["edges"], [])

    def test_architecture_mismatch_is_explicit(self):
        graph = build_compatibility_graph(
            [{"pnp_id": "USB\\VID_1234&PID_ABCD"}],
            [{"hardware_ids": ["USB\\VID_1234&PID_ABCD"], "architectures": ["arm64"]}],
            host_architecture="x64",
        )
        self.assertEqual(graph["edges"][0]["status"], "architecture_mismatch")

    def test_dry_run_never_proposes_side_effect(self):
        plan = build_dry_run_plan(
            [{"pnp_id": "USB\\VID_1234&PID_ABCD"}],
            [{"hardware_ids": ["USB\\VID_1234&PID_ABCD"]}],
        )
        self.assertEqual(plan["mode"], "dry_run")
        self.assertFalse(plan["install_attempted"])
        self.assertFalse(plan["system_modified"])
        self.assertEqual(plan["devices"][0]["proposed_operation"], "none")
        self.assertEqual(plan["summary"]["candidate_edges"], 1)
        self.assertEqual(plan["candidate_coverage"]["devices_with_candidates"], 1)


    def test_candidate_coverage_is_aggregated_without_ranking(self):
        graph = build_compatibility_graph(
            [
                {"device_id": "net-1", "pnp_id": "PCI\\\\VEN_1234&DEV_ABCD"},
                {"device_id": "net-2", "pnp_id": "PCI\\\\VEN_1234&DEV_ABCD"},
            ],
            [{
                "driver_id": "driver-a",
                "hardware_ids": ["PCI\\\\VEN_1234&DEV_ABCD"],
            }],
        )
        coverage = summarize_candidate_coverage(graph)
        self.assertEqual(coverage["candidate_edge_count"], 2)
        self.assertEqual(coverage["devices_with_candidates"], 2)
        self.assertEqual(coverage["drivers"][0]["candidate_device_count"], 2)
        self.assertIn("do not rank drivers", coverage["semantics"])

    def test_normalization_rejects_bad_ids(self):
        self.assertEqual(normalize_hardware_id(" pci/ven_1234 "), "PCI\\VEN_1234")
        self.assertEqual(normalize_hardware_id("../escape"), "")
        self.assertEqual(normalize_hardware_id(""), "")


if __name__ == "__main__":
    unittest.main()
