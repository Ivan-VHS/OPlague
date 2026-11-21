from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from oplague.clife import ClifeError, EvidenceSnapshot, FaultEvent, FaultType, RecoveryBranch, WorkbenchState, choose_recovery, export_evidence, handle_fault, load_evidence, save_evidence

class OPlagueClifeTests(unittest.TestCase):
    def test_evidence_checkpoint_round_trip(self):
        snap = EvidenceSnapshot.capture("oplague", "inventory_report", 2, b"sanitized report")
        with tempfile.TemporaryDirectory() as folder: loaded = load_evidence(save_evidence(snap, Path(folder) / "evidence.json"))
        self.assertEqual(export_evidence(loaded, "oplague", "inventory_report"), b"sanitized report")
    def test_artifact_kind_and_project_binding(self):
        snap = EvidenceSnapshot.capture("oplague", "package_manifest", 1, b"manifest")
        with self.assertRaises(ClifeError): export_evidence(snap, "other", "package_manifest")
        with self.assertRaises(ClifeError): export_evidence(snap, "oplague", "inventory_report")
    def test_corruption_is_detected(self):
        snap = EvidenceSnapshot.capture("oplague", "metric_report", 1, b"metrics")
        changed = EvidenceSnapshot(snap.project_id, snap.artifact_kind, snap.generation, b"changed", snap.checksum_sha256)
        self.assertFalse(changed.verify())
    def test_unknown_artifact_kind_is_rejected(self):
        with self.assertRaises(ClifeError): EvidenceSnapshot.capture("oplague", "driver_binary", 1, b"no")
    def test_healthy_state_resumes_read_only(self):
        self.assertEqual(choose_recovery(WorkbenchState("oplague"), None), RecoveryBranch.RESUME_READ_ONLY)
    def test_verified_report_is_exportable_after_recoverable_fault(self):
        state = WorkbenchState("oplague", generation=4, artifact_integrity=0.8)
        snap = EvidenceSnapshot.capture("oplague", "inventory_report", 3, b"report")
        event = FaultEvent(FaultType.CHECKSUM_MISMATCH, 0.1)
        self.assertEqual(handle_fault(state, event, snap), RecoveryBranch.EXPORT_VERIFIED_EVIDENCE)
        self.assertTrue(event.mitigated)
    def test_foreign_evidence_requires_review(self):
        state = WorkbenchState("oplague", artifact_integrity=0.3)
        foreign = EvidenceSnapshot.capture("other", "inventory_report", 0, b"x")
        self.assertEqual(choose_recovery(state, foreign), RecoveryBranch.HOLD_FOR_REVIEW)
        self.assertTrue(state.review_lock)
    def test_high_threat_safe_stops(self):
        state = WorkbenchState("oplague", artifact_integrity=0.2, resource_health=0.3, inspection_health=0.2)
        self.assertEqual(choose_recovery(state, None, 0.95), RecoveryBranch.SAFE_STOP)

if __name__ == "__main__": unittest.main()
