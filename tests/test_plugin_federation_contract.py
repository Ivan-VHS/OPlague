import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_plugin_federation import validate


class PluginFederationContractTests(unittest.TestCase):
    def test_catalog_and_host_contract_match(self):
        validate()


if __name__ == "__main__":
    unittest.main()
