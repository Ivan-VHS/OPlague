from __future__ import annotations

import hashlib
import unittest

from tools.device_graph import build_compatibility_graph
from tools.self_product import MAX_DEPTH, MAX_NODES, vertical_self_product


class VerticalGraphSelfProductTests(unittest.TestCase):
    def setUp(self) -> None:
        self.devices = [
            {"device_id": "device-a", "pnp_id": "PCI\\VEN_1234&DEV_ABCD", "name": "Adapter A"},
            {"device_id": "device-b", "pnp_id": "PCI\\VEN_1234&DEV_ABCD", "name": "Adapter B"},
        ]
        self.drivers = [{
            "driver_id": "driver-a",
            "hardware_ids": ["PCI\\VEN_1234&DEV_ABCD"],
            "architectures": ["x64"],
        }]

    def test_squared_graph_exposes_shared_exact_candidate_paths(self) -> None:
        graph = build_compatibility_graph(
            self.devices, self.drivers, host_architecture="x64"
        )
        report = vertical_self_product(graph, depth=1)
        layer = report["layers"][0]
        refs = {
            item["id"]: hashlib.sha256(
                (item["kind"] + "\0" + item["id"]).encode("utf-8")
            ).hexdigest()
            for item in graph["nodes"]
        }
        pairs = {
            (item["source_ref"], item["target_ref"])
            for item in layer["relations"]
        }
        self.assertEqual(report["schema"], "oplague.vertical-self-product.v1")
        self.assertEqual(layer["path_length"], 2)
        self.assertIn((refs["device-a"], refs["device-b"]), pairs)
        self.assertIn((refs["device-a"], refs["device-a"]), pairs)
        self.assertEqual(layer["diagonal_self_paths"], 3)
        self.assertFalse(report["safety"]["raw_node_identifiers_emitted"])
        self.assertFalse(report["safety"]["driver_installation_attempted"])
        self.assertNotIn("device-a", str(report))

    def test_architecture_mismatch_is_not_multiplied(self) -> None:
        graph = build_compatibility_graph(
            self.devices,
            [{**self.drivers[0], "architectures": ["arm64"]}],
            host_architecture="x64",
        )
        report = vertical_self_product(graph, depth=1)
        self.assertEqual(report["exact_candidate_edge_count"], 0)
        self.assertEqual(report["layers"][0]["ordered_pair_count"], 0)

    def test_vertical_depth_reports_even_path_lengths(self) -> None:
        graph = build_compatibility_graph(self.devices, self.drivers)
        report = vertical_self_product(graph, depth=2)
        self.assertEqual([layer["path_length"] for layer in report["layers"]], [2, 4])

    def test_rejects_invalid_schema_edges_and_bounds(self) -> None:
        with self.assertRaisesRegex(ValueError, "schema"):
            vertical_self_product({"schema": "wrong", "nodes": [], "edges": []})
        with self.assertRaisesRegex(ValueError, "unknown node"):
            vertical_self_product({
                "schema": "oplague.device-driver-graph.v1",
                "nodes": [{"id": "d", "kind": "device"}],
                "edges": [{"device_id": "d", "driver_id": "missing",
                           "status": "exact_identifier_candidate",
                           "matched_ids": ["PCI\\VEN_1"]}],
            })
        oversized = {
            "schema": "oplague.device-driver-graph.v1",
            "nodes": [{"id": f"n-{index}", "kind": "device"} for index in range(MAX_NODES + 1)],
            "edges": [],
        }
        with self.assertRaisesRegex(ValueError, "at most"):
            vertical_self_product(oversized)

    def test_depth_is_type_checked_and_bounded(self) -> None:
        graph = build_compatibility_graph(self.devices, self.drivers)
        with self.assertRaises(TypeError):
            vertical_self_product(graph, depth=True)
        with self.assertRaises(ValueError):
            vertical_self_product(graph, depth=0)
        with self.assertRaises(ValueError):
            vertical_self_product(graph, depth=MAX_DEPTH + 1)


if __name__ == "__main__":
    unittest.main()
