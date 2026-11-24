from __future__ import annotations

import math
import tempfile
import unittest
from pathlib import Path

from oplague.local_first import LocalFirstError, LocalFirstStore


class LocalFirstStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_wal_store_persists_across_restart(self) -> None:
        path = self.root / "state" / "evidence.sqlite3"
        with LocalFirstStore(path, "desktop-a") as store:
            store.put("workbench.layout", {"left": 240, "right": 760})
            self.assertEqual(store.get("workbench.layout")["left"], 240)
        with LocalFirstStore(path, "desktop-a") as reopened:
            self.assertEqual(reopened.get("workbench.layout"), {"left": 240, "right": 760})

    def test_offline_peers_converge_independent_of_merge_order(self) -> None:
        left = LocalFirstStore(self.root / "left.db", "alpha")
        right = LocalFirstStore(self.root / "right.db", "beta")
        self.addCleanup(left.close)
        self.addCleanup(right.close)
        left.put("theme", "noir")
        right.put("theme", "yellow")
        left_ops = left.export_operations()
        right_ops = right.export_operations()
        self.assertEqual(left.merge(right_ops), 1)
        self.assertEqual(right.merge(left_ops), 1)
        self.assertEqual(left.snapshot(), right.snapshot())
        self.assertEqual(left.get("theme"), "yellow")

    def test_repeated_delivery_is_idempotent(self) -> None:
        source = LocalFirstStore(self.root / "source.db", "source")
        target = LocalFirstStore(self.root / "target.db", "target")
        self.addCleanup(source.close)
        self.addCleanup(target.close)
        source.put("mode", "offline")
        batch = source.export_operations()
        self.assertEqual(target.merge(batch), 1)
        self.assertEqual(target.merge(batch), 0)
        self.assertEqual(target.get("mode"), "offline")

    def test_tombstones_replicate_and_remove_materialized_values(self) -> None:
        source = LocalFirstStore(self.root / "source.db", "source")
        target = LocalFirstStore(self.root / "target.db", "target")
        self.addCleanup(source.close)
        self.addCleanup(target.close)
        source.put("recent.project", "demo")
        source.delete("recent.project")
        target.merge(source.export_operations())
        self.assertIsNone(target.get("recent.project"))
        self.assertEqual(target.snapshot(), {})

    def test_same_operation_id_with_different_payload_is_rejected(self) -> None:
        source = LocalFirstStore(self.root / "source.db", "source")
        target = LocalFirstStore(self.root / "target.db", "target")
        self.addCleanup(source.close)
        self.addCleanup(target.close)
        operation = source.put("setting", True)
        target.merge([operation])
        tampered = dict(operation, value=False)
        with self.assertRaisesRegex(LocalFirstError, "conflicting payload"):
            target.merge([tampered])

    def test_equal_lamport_clock_has_deterministic_actor_tiebreak(self) -> None:
        alpha = LocalFirstStore(self.root / "alpha.db", "alpha")
        zeta = LocalFirstStore(self.root / "zeta.db", "zeta")
        self.addCleanup(alpha.close)
        self.addCleanup(zeta.close)
        alpha.put("active", "alpha")
        zeta.put("active", "zeta")
        operations = alpha.export_operations() + zeta.export_operations()
        alpha.merge(operations)
        zeta.merge(operations)
        self.assertEqual(alpha.get("active"), "zeta")
        self.assertEqual(alpha.snapshot(), zeta.snapshot())

    def test_invalid_json_and_unbounded_values_are_rejected(self) -> None:
        store = LocalFirstStore(self.root / "state.db", "desktop")
        self.addCleanup(store.close)
        with self.assertRaisesRegex(LocalFirstError, "finite JSON"):
            store.put("bad", math.nan)
        with self.assertRaisesRegex(LocalFirstError, "UTF-8 bytes"):
            store.put("large", "x" * (1024 * 1024 + 1))

    def test_malformed_remote_operations_are_rejected_atomically(self) -> None:
        store = LocalFirstStore(self.root / "state.db", "desktop")
        self.addCleanup(store.close)
        with self.assertRaisesRegex(LocalFirstError, "op_id"):
            store.merge([{
                "op_id": "remote:2", "actor": "remote", "counter": 1,
                "lamport": 1, "key": "valid", "value": 1, "deleted": False,
            }])
        self.assertEqual(store.snapshot(), {})

    def test_closed_store_rejects_reads(self) -> None:
        store = LocalFirstStore(self.root / "state.db", "desktop")
        store.close()
        with self.assertRaisesRegex(LocalFirstError, "closed"):
            store.snapshot()


if __name__ == "__main__":
    unittest.main()
