from __future__ import annotations

import asyncio
import unittest

from oplague.transactions import EvidenceConflict, EvidenceTransaction, EvidenceTransitionError


class EvidenceTransactionTests(unittest.TestCase):
    def test_commit_patch_remap_and_digest(self) -> None:
        events: list[tuple[str, int]] = []
        tx = EvidenceTransaction(
            {"device": {"status": "observed"}, "legacy_metric": 2.5},
            event_sink=lambda name, generation: events.append((name, generation)),
        )
        tx.patch(("device", "status"), "reviewed")
        tx.remap({"legacy_metric": "normalized_metric"})
        snapshot = tx.flash(0)
        self.assertEqual(snapshot.generation, 1)
        self.assertEqual(snapshot.data["device"]["status"], "reviewed")
        self.assertEqual(snapshot.data["normalized_metric"], 2.5)
        self.assertEqual(len(snapshot.sha256), 64)
        self.assertIn(("EVIDENCE_SNAPSHOT_COMMITTED", 1), events)

    def test_optimistic_conflict_and_rollback(self) -> None:
        tx = EvidenceTransaction({"score": 10})
        tx.patch(("score",), 11)
        tx.flash(0)
        tx.patch(("score",), 12)
        with self.assertRaises(EvidenceConflict):
            tx.flash(0)
        self.assertEqual(tx.rollback().data, {"score": 11})

    def test_migrate_hot_swap_and_schema_rollback(self) -> None:
        tx = EvidenceTransaction({"version": 1})
        tx.hot_swap({"version": 1, "records": []})
        tx.migrate(2, lambda value: {**value, "version": 2})
        tx.flash()
        self.assertEqual(tx.snapshot().schema_version, 2)
        tx.migrate(3, lambda value: {**value, "version": 3})
        restored = tx.rollback()
        self.assertEqual(restored.schema_version, 2)
        self.assertEqual(restored.data["version"], 2)

    def test_read_only_scope_helpers(self) -> None:
        self.assertEqual(EvidenceTransaction.return_value(5), 5)
        self.assertEqual(EvidenceTransaction.catch(EvidenceTransaction.throw, "blocked")[1], "blocked")
        with self.assertRaises(EvidenceTransitionError):
            EvidenceTransaction.assert_condition(False, "driver write prohibited")
        with self.assertRaisesRegex(EvidenceTransitionError, "guarded panic"):
            EvidenceTransaction.panic("unexpected state")

    def test_async_await_sync_and_checkpoint(self) -> None:
        async def run() -> None:
            tx = EvidenceTransaction({"ready": False})
            tx.patch(("ready",), True)
            task = asyncio.create_task(tx.async_flash(0))
            result = await EvidenceTransaction.await_result(task)
            self.assertTrue(result.data["ready"])
            self.assertEqual(tx.yield_checkpoint("before-report"), "before-report")
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
