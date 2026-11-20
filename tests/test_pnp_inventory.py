from __future__ import annotations
import unittest
from tools.pnp_inventory import normalize_pnp_devices

class PnpInventoryTests(unittest.TestCase):
    def test_normalizes_scalar_and_array_ids(self):
        rows = normalize_pnp_devices({
            "name": "Adapter", "instance_id": "PCI\\VEN_1234&DEV_5678",
            "hardware_ids": "PCI\\VEN_1234&DEV_5678", "compatible_ids": ["PCI\\VEN_1234", None],
            "problem_code": "28", "present": False,
        })
        self.assertEqual(rows[0]["hardware_ids"], [r"PCI\VEN_1234&DEV_5678"])
        self.assertEqual(rows[0]["compatible_ids"], [r"PCI\VEN_1234"])
        self.assertEqual(rows[0]["problem_code"], 28)
        self.assertFalse(rows[0]["present"])
        self.assertEqual(rows[0]["pnp_id"], rows[0]["instance_id"])

    def test_rejects_duplicate_instance_ids_and_bad_shapes(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            normalize_pnp_devices([{"instance_id": "PCI\\A"}, {"instance_id": "pci\\a"}])
        with self.assertRaisesRegex(ValueError, "object or array"):
            normalize_pnp_devices("bad")

if __name__ == "__main__":
    unittest.main()
