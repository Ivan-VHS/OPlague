"""Evidence-based INF-to-device ID matching; no Windows rank emulation."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def _id_list(value: Any, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise TypeError(f"{label} must be a list of strings")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{label} contains an empty or non-string ID")
        normalized = item.strip()
        if len(normalized) > 1024:
            raise ValueError(f"{label} contains an ID that is too long")
        result.append(normalized)
    return result


def match_device_to_inf(device: Mapping[str, Any], inf: Mapping[str, Any]) -> dict[str, Any]:
    """Return the strongest explicit ID match and its source-order evidence.

    Hardware-ID equality outranks Compatible-ID equality. This is an evidence
    ranking only; Windows SetupAPI rank, signature score, OS decoration and
    policy are intentionally not inferred here.
    """
    hardware = _id_list(device.get("hardware_ids", []), "device.hardware_ids")
    compatible = _id_list(device.get("compatible_ids", []), "device.compatible_ids")
    declared = _id_list(inf.get("device_ids", []), "inf.device_ids")
    declared_map = {value.casefold(): value for value in declared}

    for category, identifiers, score in (
        ("hardware-id", hardware, 100),
        ("compatible-id", compatible, 70),
    ):
        for position, identifier in enumerate(identifiers):
            matched = declared_map.get(identifier.casefold())
            if matched is not None:
                return {
                    "schema": "oplage.compatibility-evidence.v1",
                    "matched": True,
                    "match_type": category,
                    "matched_device_id": identifier,
                    "matched_inf_id": matched,
                    "device_id_priority": position,
                    "evidence_score": score,
                    "confidence": "direct-id-equality",
                    "limitations": [
                        "Not a Windows SetupAPI driver rank",
                        "Does not evaluate OS decorations, architecture, signing, policy, or install sections",
                    ],
                }
    return {
        "schema": "oplage.compatibility-evidence.v1",
        "matched": False,
        "match_type": "none",
        "matched_device_id": None,
        "matched_inf_id": None,
        "device_id_priority": None,
        "evidence_score": 0,
        "confidence": "no-direct-id-evidence",
        "limitations": ["No direct Hardware ID or Compatible ID equality was found"],
    }


def rank_inf_candidates(device: Mapping[str, Any], packages: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Rank packages by match class and device ID order, preserving stable ties."""
    if not isinstance(packages, (list, tuple)):
        raise TypeError("packages must be a sequence")
    results: list[dict[str, Any]] = []
    for original_index, package in enumerate(packages):
        if not isinstance(package, Mapping):
            raise TypeError("each package must be a mapping")
        evidence = match_device_to_inf(device, package.get("inf_evidence", {}))
        results.append({"package": dict(package), "evidence": evidence, "input_order": original_index})
    results.sort(key=lambda row: (
        0 if row["evidence"]["match_type"] == "hardware-id" else
        1 if row["evidence"]["match_type"] == "compatible-id" else 2,
        row["evidence"]["device_id_priority"] if row["evidence"]["device_id_priority"] is not None else 1_000_000,
        row["input_order"],
    ))
    for rank, row in enumerate(results, start=1):
        row["evidence_rank"] = rank
    return results
