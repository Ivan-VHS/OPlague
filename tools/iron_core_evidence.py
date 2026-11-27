"""Read-only validation for Pytyliki Iron Core structural AST evidence.

This module validates a caller-supplied AST envelope. It does not parse or
execute Pytyliki source and does not treat source-authored seals as CI proof.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping

SCHEMA_ID = "pytyliki.iron-core-ast.v1"
MAX_SOURCE_BYTES = 1024 * 1024
MAX_BLOCKS = 64
LABEL_RE = re.compile(r"^[A-Za-z0-9_.-]{1,95}$")

MARKERS = {
    "module.begin": "begin iron )",
    "core.context": "() core --",
    "system.context": "[ system ]-",
    "block.end": "stop option ;",
    "level.context": "] level .",
    "selection.filter": "{ selective /",
    "operation.unit": "} operation P)-",
    "work.massive": "?? massive <>",
    "startup.plan": "< start >?",
    "work.spawn.plan": "grown new-work >/",
    "implementation.binding": "> concrete //*",
    "utility.helper": "## utility _",
    "layout.unify": "# unify TAB",
    "branchpass.plan": "setup brachpass ^^",
    "tournament.rank": "!+ hyper tournament ^",
    "consistency.rules": "CC based rules ^^^",
    "execution.jump.plan": "level jump to run *(",
    "logic.true_connective": "TRUE connective *+",
    "module.version": "verison ///. *",
    "source.verification_claim": "verificated /// !!",
}
BLOCK_IDS = {
    "core.context", "system.context", "level.context", "selection.filter",
    "operation.unit", "work.massive", "startup.plan", "work.spawn.plan",
    "implementation.binding", "utility.helper", "layout.unify",
    "branchpass.plan", "tournament.rank", "execution.jump.plan",
    "logic.true_connective",
}
TOP_LEVEL_KEYS = {
    "schema", "source_bytes", "root_seen", "version", "version_declarations",
    "policy_declarations", "source_seal_asserted", "verification_claim",
    "verification_claims_are_ci_evidence", "semantic_validation_performed",
    "execution_performed", "hardware_access_performed", "blocks", "marker_counts",
}
BLOCK_KEYS = {
    "marker", "semantic_id", "start_offset", "body_offset", "body_length",
    "end_offset", "line", "closed",
}


class IronCoreEvidenceError(ValueError):
    """The supplied AST is not a valid, bounded Iron Core v1 envelope."""


@dataclass(frozen=True)
class IronCoreEvidence:
    version: str
    source_bytes: int
    block_count: int
    semantic_ids: tuple[str, ...]
    source_claim: str
    ci_verified: bool = False
    hardware_effects_performed: bool = False
    provenance: str = "caller-supplied-untrusted-json"


def _integer(value: Any, label: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise IronCoreEvidenceError(f"{label} must be an integer >= {minimum}")
    return value


def _label(value: Any, label: str) -> str:
    if not isinstance(value, str) or not LABEL_RE.fullmatch(value):
        raise IronCoreEvidenceError(f"{label} is not a valid Iron Core identifier")
    return value


def validate_iron_core_ast(payload: Mapping[str, Any]) -> IronCoreEvidence:
    """Validate the Pytyliki structural AST and return a read-only evidence record."""
    if not isinstance(payload, Mapping):
        raise IronCoreEvidenceError("AST root must be an object")
    if set(payload.keys()) != TOP_LEVEL_KEYS:
        raise IronCoreEvidenceError("AST keys do not match the v1 contract")
    if payload["schema"] != SCHEMA_ID:
        raise IronCoreEvidenceError("unsupported Iron Core AST schema")
    if payload["root_seen"] is not True:
        raise IronCoreEvidenceError("Iron Core root marker is missing")

    source_bytes = _integer(payload["source_bytes"], "source_bytes", 1)
    if source_bytes > MAX_SOURCE_BYTES:
        raise IronCoreEvidenceError("source_bytes exceeds the one-megabyte limit")
    version = _label(payload["version"], "version")
    claim = _label(payload["verification_claim"], "verification_claim")

    version_count = _integer(payload["version_declarations"], "version_declarations", 1)
    policy_count = _integer(payload["policy_declarations"], "policy_declarations", 1)
    if payload["source_seal_asserted"] is not True:
        raise IronCoreEvidenceError("source verification claim is absent")
    if payload["verification_claims_are_ci_evidence"] is not False:
        raise IronCoreEvidenceError("source claims must never be promoted to CI evidence")
    for field in ("semantic_validation_performed", "execution_performed", "hardware_access_performed"):
        if payload[field] is not False:
            raise IronCoreEvidenceError(f"{field} must remain false for structural AST v1")

    blocks = payload["blocks"]
    if not isinstance(blocks, list) or not 1 <= len(blocks) <= MAX_BLOCKS:
        raise IronCoreEvidenceError("blocks must contain between 1 and 64 entries")

    counts = payload["marker_counts"]
    if not isinstance(counts, Mapping) or set(counts.keys()) != set(MARKERS):
        raise IronCoreEvidenceError("marker_counts must contain the complete v1 marker catalogue")
    normalized_counts = {
        marker_id: _integer(counts[marker_id], f"marker_counts.{marker_id}")
        for marker_id in MARKERS
    }
    if normalized_counts["module.begin"] != 1:
        raise IronCoreEvidenceError("exactly one module root is required")
    if normalized_counts["module.version"] != version_count:
        raise IronCoreEvidenceError("version declaration count does not match the marker catalogue")
    if normalized_counts["consistency.rules"] != policy_count:
        raise IronCoreEvidenceError("policy declaration count does not match the marker catalogue")
    if normalized_counts["source.verification_claim"] < 1:
        raise IronCoreEvidenceError("verification claim marker is absent")

    semantic_ids: list[str] = []
    previous_start = -1
    for index, block in enumerate(blocks):
        if not isinstance(block, Mapping) or set(block.keys()) != BLOCK_KEYS:
            raise IronCoreEvidenceError(f"block {index} does not match the v1 block contract")
        semantic_id = block["semantic_id"]
        if semantic_id not in BLOCK_IDS or MARKERS.get(semantic_id) != block["marker"]:
            raise IronCoreEvidenceError(f"block {index} has an unknown marker or semantic ID")
        start = _integer(block["start_offset"], f"blocks[{index}].start_offset")
        body = _integer(block["body_offset"], f"blocks[{index}].body_offset")
        length = _integer(block["body_length"], f"blocks[{index}].body_length")
        end = _integer(block["end_offset"], f"blocks[{index}].end_offset")
        line = _integer(block["line"], f"blocks[{index}].line", 1)
        if block["closed"] is not True:
            raise IronCoreEvidenceError(f"block {index} is not closed")
        if start < previous_start or not start <= body <= end <= source_bytes:
            raise IronCoreEvidenceError(f"block {index} has an invalid or unordered source range")
        if body + length != end:
            raise IronCoreEvidenceError(f"block {index} body length does not match its end offset")
        previous_start = start
        semantic_ids.append(semantic_id)

    block_marker_total = sum(normalized_counts[marker_id] for marker_id in BLOCK_IDS)
    if block_marker_total != len(blocks):
        raise IronCoreEvidenceError("block records do not match the opener marker counts")
    if normalized_counts["block.end"] != len(blocks):
        raise IronCoreEvidenceError("each block must have one closing marker")

    return IronCoreEvidence(
        version=version,
        source_bytes=source_bytes,
        block_count=len(blocks),
        semantic_ids=tuple(semantic_ids),
        source_claim=claim,
    )
