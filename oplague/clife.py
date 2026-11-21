"""CLife evidence checkpoints for OPlague's read-only driver workbench.

Only reports/manifests are preserved. No device, driver, registry or kernel state is changed.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, math, os, tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

SCHEMA = "clife.oplague-evidence.v1"
MAX_PAYLOAD_BYTES = 64 * 1024 * 1024
ARTIFACT_KINDS = frozenset({"inventory_report", "package_manifest", "metric_report", "inspection_notes"})

class ClifeError(ValueError): pass
class FaultType(str, Enum):
    EVIDENCE_READ_FAILURE = "evidence_read_failure"
    CHECKSUM_MISMATCH = "checksum_mismatch"
    RESOURCE_PRESSURE = "resource_pressure"
    INSPECTION_INTERRUPTED = "inspection_interrupted"
class RecoveryBranch(str, Enum):
    RESUME_READ_ONLY = "resume_read_only"
    EXPORT_VERIFIED_EVIDENCE = "export_verified_evidence"
    HOLD_FOR_REVIEW = "hold_for_review"
    SAFE_STOP = "safe_stop"

def _validate(project_id: Any, artifact_kind: Any, generation: Any, payload: Any) -> None:
    if not isinstance(project_id, str) or not project_id.strip() or len(project_id) > 128:
        raise ClifeError("project_id must be non-empty text of at most 128 characters")
    if artifact_kind not in ARTIFACT_KINDS: raise ClifeError("unsupported evidence artifact kind")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
        raise ClifeError("generation must be a non-negative integer")
    if not isinstance(payload, bytes) or len(payload) > MAX_PAYLOAD_BYTES:
        raise ClifeError("payload must be bytes within the 64 MiB limit")

@dataclass(frozen=True, slots=True)
class EvidenceSnapshot:
    project_id: str
    artifact_kind: str
    generation: int
    payload: bytes
    checksum_sha256: str
    schema: str = SCHEMA

    @classmethod
    def capture(cls, project_id: str, artifact_kind: str, generation: int, payload: bytes) -> "EvidenceSnapshot":
        _validate(project_id, artifact_kind, generation, payload)
        return cls(project_id, artifact_kind, generation, payload, hashlib.sha256(payload).hexdigest())

    def verify(self) -> bool:
        try:
            _validate(self.project_id, self.artifact_kind, self.generation, self.payload)
            return self.schema == SCHEMA and self.checksum_sha256 == hashlib.sha256(self.payload).hexdigest()
        except (ClifeError, TypeError): return False

    def to_dict(self) -> dict[str, Any]:
        if not self.verify(): raise ClifeError("refusing to serialize invalid evidence")
        return {"schema": self.schema, "project_id": self.project_id, "artifact_kind": self.artifact_kind,
                "generation": self.generation, "payload_encoding": "base64", "payload": base64.b64encode(self.payload).decode("ascii"),
                "checksum_algorithm": "sha256", "checksum": self.checksum_sha256,
                "execution_policy": "data_only_never_execute"}

    @classmethod
    def from_dict(cls, value: Any) -> "EvidenceSnapshot":
        if not isinstance(value, dict) or value.get("schema") != SCHEMA: raise ClifeError("unsupported evidence checkpoint schema")
        if value.get("payload_encoding") != "base64" or value.get("checksum_algorithm") != "sha256": raise ClifeError("unsupported encoding or checksum")
        if value.get("execution_policy") != "data_only_never_execute": raise ClifeError("checkpoint execution policy is missing or invalid")
        encoded, checksum = value.get("payload"), value.get("checksum")
        if not isinstance(encoded, str) or len(encoded) > ((MAX_PAYLOAD_BYTES + 2) // 3) * 4: raise ClifeError("invalid or oversized payload")
        if not isinstance(checksum, str) or len(checksum) != 64: raise ClifeError("invalid SHA-256 field")
        try: payload = base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error) as exc: raise ClifeError("invalid base64 payload") from exc
        snap = cls(value.get("project_id"), value.get("artifact_kind"), value.get("generation"), payload, checksum)
        if not snap.verify(): raise ClifeError("evidence checksum or metadata verification failed")
        return snap

def save_evidence(snapshot: EvidenceSnapshot, path: str | Path) -> Path:
    if not snapshot.verify(): raise ClifeError("refusing to persist unverified evidence")
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    content = (json.dumps(snapshot.to_dict(), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=target.parent, prefix=f".{target.name}.", suffix=".tmp", delete=False) as stream:
            temporary = stream.name; stream.write(content); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, target)
    except OSError as exc:
        if temporary:
            try: os.unlink(temporary)
            except OSError: pass
        raise ClifeError(f"atomic evidence write failed: {exc}") from exc
    return target

def load_evidence(path: str | Path) -> EvidenceSnapshot:
    source = Path(path)
    try:
        if source.stat().st_size > MAX_PAYLOAD_BYTES * 2: raise ClifeError("evidence checkpoint exceeds the size limit")
        raw = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc: raise ClifeError(f"cannot read evidence checkpoint: {exc}") from exc
    return EvidenceSnapshot.from_dict(raw)

def export_evidence(snapshot: EvidenceSnapshot, expected_project_id: str, expected_kind: str) -> bytes:
    if not snapshot.verify(): raise ClifeError("evidence verification failed")
    if snapshot.project_id != expected_project_id or snapshot.artifact_kind != expected_kind:
        raise ClifeError("project or evidence-kind binding mismatch")
    return bytes(snapshot.payload)

@dataclass(slots=True)
class WorkbenchState:
    project_id: str
    artifact_integrity: float = 1.0
    resource_health: float = 1.0
    inspection_health: float = 1.0
    generation: int = 0
    review_lock: bool = False

@dataclass(slots=True)
class FaultEvent:
    fault_type: FaultType
    severity: float
    mitigated: bool = False

def _unit(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ClifeError(f"{name} must be finite and in 0..1")
    return float(value)

def choose_recovery(state: WorkbenchState, snapshot: EvidenceSnapshot | None, threat: float = 0.0) -> RecoveryBranch:
    threat = _unit(threat, "threat")
    integrity = _unit(state.artifact_integrity, "artifact_integrity")
    resources = _unit(state.resource_health, "resource_health")
    inspection = _unit(state.inspection_health, "inspection_health")
    viability = 0.5 * integrity + 0.25 * resources + 0.25 * inspection
    valid = bool(snapshot and snapshot.verify() and snapshot.project_id == state.project_id and snapshot.generation <= state.generation)
    if threat > 0.85 and viability < 0.70:
        state.review_lock = True; return RecoveryBranch.SAFE_STOP
    if viability >= 0.95 and inspection >= 0.95:
        state.review_lock = False; return RecoveryBranch.RESUME_READ_ONLY
    if valid and viability >= 0.55:
        state.review_lock = False; return RecoveryBranch.EXPORT_VERIFIED_EVIDENCE
    state.review_lock = True; return RecoveryBranch.HOLD_FOR_REVIEW

def handle_fault(state: WorkbenchState, fault: FaultEvent, snapshot: EvidenceSnapshot | None = None, threat: float = 0.0) -> RecoveryBranch:
    severity = _unit(fault.severity, "severity")
    adjustments = {FaultType.EVIDENCE_READ_FAILURE: ("resource_health", 0.30), FaultType.CHECKSUM_MISMATCH: ("artifact_integrity", 0.50),
                   FaultType.RESOURCE_PRESSURE: ("resource_health", 0.45), FaultType.INSPECTION_INTERRUPTED: ("inspection_health", 0.50)}
    if not isinstance(fault.fault_type, FaultType): raise ClifeError("unknown fault type")
    field, scale = adjustments[fault.fault_type]
    setattr(state, field, max(0.0, _unit(getattr(state, field), field) - severity * scale))
    branch = choose_recovery(state, snapshot, threat)
    fault.mitigated = branch in (RecoveryBranch.RESUME_READ_ONLY, RecoveryBranch.EXPORT_VERIFIED_EVIDENCE)
    return branch

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CLife offline evidence checkpointing; device and driver state is never changed.")
    sub = parser.add_subparsers(dest="action", required=True)
    capture = sub.add_parser("capture"); capture.add_argument("source", type=Path); capture.add_argument("destination", type=Path)
    capture.add_argument("--project-id", required=True); capture.add_argument("--artifact-kind", choices=sorted(ARTIFACT_KINDS), required=True); capture.add_argument("--generation", type=int, required=True)
    verify = sub.add_parser("verify"); verify.add_argument("checkpoint", type=Path)
    export = sub.add_parser("export"); export.add_argument("checkpoint", type=Path); export.add_argument("destination", type=Path)
    export.add_argument("--project-id", required=True); export.add_argument("--artifact-kind", choices=sorted(ARTIFACT_KINDS), required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "capture":
            if args.source.stat().st_size > MAX_PAYLOAD_BYTES: raise ClifeError("source file exceeds 64 MiB")
            snap = EvidenceSnapshot.capture(args.project_id, args.artifact_kind, args.generation, args.source.read_bytes())
            save_evidence(snap, args.destination); print(json.dumps({"status": "captured", "artifact_kind": snap.artifact_kind, "checksum": snap.checksum_sha256}))
        elif args.action == "verify":
            snap = load_evidence(args.checkpoint); print(json.dumps({"status": "verified", "artifact_kind": snap.artifact_kind, "bytes": len(snap.payload)}))
        else:
            snap = load_evidence(args.checkpoint); payload = export_evidence(snap, args.project_id, args.artifact_kind)
            args.destination.parent.mkdir(parents=True, exist_ok=True); args.destination.write_bytes(payload)
            print(json.dumps({"status": "exported_evidence", "bytes": len(payload)}))
        return 0
    except (ClifeError, OSError) as exc: parser.exit(2, f"oplague-clife: {exc}\n")
    return 2

if __name__ == "__main__": raise SystemExit(main())
