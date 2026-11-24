"""Evidence-only device/driver matching and deployment dry-run planning.

An exact Plug and Play identifier match is a candidate, never an installation
or safety verdict. This module has no privileged operations.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
import re
from typing import Any

MAX_DEVICES = 20_000
MAX_DRIVERS = 5_000
MAX_IDS_PER_RECORD = 256
MAX_CANDIDATE_EDGES = 100_000
_ID_PREFIXES = (
    "PCI\\", "USB\\", "ACPI\\", "ROOT\\", "HID\\", "SWD\\",
    "BTH\\", "DISPLAY\\", "SCSI\\", "IDE\\", "VMBUS\\",
)
_ARCH_ALIASES = {
    "amd64": "x64", "x86_64": "x64", "x64": "x64",
    "i386": "x86", "i686": "x86", "x86": "x86",
    "aarch64": "arm64", "arm64": "arm64",
}


def normalize_hardware_id(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    normalized = value.strip().replace("/", "\\").upper()
    if not normalized or len(normalized) > 512 or "\\x00" in normalized:
        return ""
    if not normalized.startswith(_ID_PREFIXES):
        return ""
    if any(part == ".." for part in normalized.split("\\")):
        return ""
    return normalized


def _as_ids(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple)):
        values = value
    else:
        return []
    if len(values) > MAX_IDS_PER_RECORD:
        return []
    result = []
    for item in values:
        normalized = normalize_hardware_id(item)
        if normalized:
            result.append(normalized)
    return sorted(set(result))


def normalize_architecture(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    raw = value.strip().casefold()
    return _ARCH_ALIASES.get(raw, raw)


def extract_inf_compatibility(content: str) -> dict[str, Any]:
    """Collect IDs and target architectures from INF Models sections."""
    if not isinstance(content, str):
        raise TypeError("INF content must be text")
    if len(content) > 2 * 1024 * 1024:
        raise ValueError("INF content exceeds the 2 MiB inspection limit")

    section = ""
    ids: set[str] = set()
    architectures: set[str] = set()
    for raw in content.lstrip("\ufeff").splitlines():
        line = raw.strip()
        if not line or line.startswith((";", "#")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().casefold()
            if section == "models":
                architectures.add("any")
            elif section.startswith("models."):
                suffix = section.split(".", 1)[1]
                target = suffix.split(".", 1)[0].removeprefix("nt")
                target = normalize_architecture(target)
                if target in {"x64", "x86", "arm64"}:
                    architectures.add(target)
            continue
        if not section.startswith("models") or "=" not in line:
            continue
        _, rhs = line.split("=", 1)
        for candidate in rhs.split(","):
            token = candidate.strip().strip('"')
            normalized = normalize_hardware_id(token)
            if normalized.startswith(_ID_PREFIXES):
                ids.add(normalized)

    return {
        "hardware_ids": sorted(ids)[:MAX_IDS_PER_RECORD],
        "architectures": sorted(architectures) or ["unspecified"],
        "evidence": "INF Models section; identifiers only",
    }


def build_compatibility_graph(
    devices: Sequence[Mapping[str, Any]],
    drivers: Sequence[Mapping[str, Any]],
    *,
    host_architecture: str | None = None,
) -> dict[str, Any]:
    """Build a bipartite exact-ID candidate graph; never infer compatibility from names."""
    if not isinstance(devices, (list, tuple)) or len(devices) > MAX_DEVICES:
        raise ValueError(f"devices must contain at most {MAX_DEVICES} records")
    if not isinstance(drivers, (list, tuple)) or len(drivers) > MAX_DRIVERS:
        raise ValueError(f"drivers must contain at most {MAX_DRIVERS} records")

    host_arch = normalize_architecture(host_architecture)
    nodes: list[dict[str, str]] = []
    edges: list[dict[str, Any]] = []
    normalized_drivers: list[dict[str, Any]] = []
    seen_driver_ids: set[str] = set()

    for driver_index, driver in enumerate(drivers):
        if not isinstance(driver, Mapping):
            raise TypeError("driver records must be mappings")
        driver_id = str(
            driver.get("driver_id") or driver.get("package_sha256") or f"driver-{driver_index}"
        )
        if not driver_id or len(driver_id) > 512:
            raise ValueError("driver_id must contain 1..512 characters")
        if driver_id in seen_driver_ids:
            raise ValueError(f"duplicate driver_id: {driver_id}")
        seen_driver_ids.add(driver_id)

        compatibility = (
            driver.get("compatibility")
            if isinstance(driver.get("compatibility"), Mapping)
            else {}
        )
        driver_ids = _as_ids(
            driver.get("hardware_ids", compatibility.get("hardware_ids", []))
        )
        raw_arches = driver.get(
            "architectures", compatibility.get("architectures", ["unspecified"])
        )
        if isinstance(raw_arches, str):
            raw_arches = [raw_arches]
        elif not isinstance(raw_arches, (list, tuple, set)):
            raw_arches = ["unspecified"]
        arches = {
            normalize_architecture(item)
            for item in raw_arches
            if isinstance(item, str)
        }
        if not arches:
            arches = {"unspecified"}

        package_name = str(driver.get("package_name") or driver_id)
        nodes.append({
            "id": driver_id,
            "kind": "driver",
            "name": package_name[:512],
        })
        normalized_drivers.append({
            "driver_id": driver_id,
            "hardware_ids": driver_ids,
            "architectures": arches,
        })

    # Index exact hardware IDs once. The previous device×driver scan was
    # quadratic even when most pairs shared no identifiers.
    driver_indexes_by_id: dict[str, list[int]] = {}
    for driver_index, driver in enumerate(normalized_drivers):
        for hardware_id in driver["hardware_ids"]:
            driver_indexes_by_id.setdefault(hardware_id, []).append(driver_index)

    seen_device_ids: set[str] = set()
    for index, device in enumerate(devices):
        if not isinstance(device, Mapping):
            raise TypeError("device records must be mappings")
        device_id = str(
            device.get("device_id") or device.get("pnp_id") or f"device-{index}"
        )
        if not device_id or len(device_id) > 512:
            raise ValueError("device_id must contain 1..512 characters")
        if device_id in seen_device_ids:
            raise ValueError(f"duplicate device_id: {device_id}")
        seen_device_ids.add(device_id)

        raw_device_ids: list[Any] = []
        for field in ("pnp_id", "hardware_ids", "compatible_ids"):
            value = device.get(field)
            if isinstance(value, str):
                raw_device_ids.append(value)
            elif isinstance(value, (list, tuple)):
                raw_device_ids.extend(value[:MAX_IDS_PER_RECORD])
        device_ids = _as_ids(raw_device_ids)
        device_name = str(device.get("name") or device_id)
        nodes.append({
            "id": device_id,
            "kind": "device",
            "name": device_name[:512],
        })

        matched_by_driver: dict[int, set[str]] = {}
        for hardware_id in device_ids:
            for driver_index in driver_indexes_by_id.get(hardware_id, ()):
                matched_by_driver.setdefault(driver_index, set()).add(hardware_id)

        # Keep deterministic candidate order even when source hardware IDs arrive
        # in a different sequence.
        for driver_index in sorted(
            matched_by_driver,
            key=lambda item: normalized_drivers[item]["driver_id"],
        ):
            driver = normalized_drivers[driver_index]
            matched = sorted(matched_by_driver[driver_index])
            arch_ok = (
                not host_arch
                or "any" in driver["architectures"]
                or "unspecified" in driver["architectures"]
                or host_arch in driver["architectures"]
            )
            if len(edges) >= MAX_CANDIDATE_EDGES:
                raise ValueError(
                    f"candidate graph exceeds the {MAX_CANDIDATE_EDGES}-edge limit"
                )
            edges.append({
                "device_id": device_id,
                "driver_id": driver["driver_id"],
                "matched_ids": matched,
                "status": (
                    "exact_identifier_candidate"
                    if arch_ok else "architecture_mismatch"
                ),
                "architecture_check": (
                    "not_requested" if not host_arch
                    else "passed" if arch_ok else "failed"
                ),
            })

    return {
        "schema": "oplague.device-driver-graph.v1",
        "host_architecture": host_arch or None,
        "nodes": nodes,
        "edges": edges,
        "semantics": (
            "Bipartite exact identifier candidates only; an edge is not a "
            "compatibility, ranking, signature or safety verdict."
        ),
    }

def build_dry_run_plan(
    devices: Sequence[Mapping[str, Any]],
    drivers: Sequence[Mapping[str, Any]],
    *,
    host_architecture: str | None = None,
) -> dict[str, Any]:
    """Produce an auditable plan without changing device or driver state."""
    graph = build_compatibility_graph(
        devices, drivers, host_architecture=host_architecture
    )
    by_device: dict[str, list[dict[str, Any]]] = {}
    for edge in graph["edges"]:
        by_device.setdefault(edge["device_id"], []).append(edge)

    planned = []
    for node in graph["nodes"]:
        if node["kind"] != "device":
            continue
        candidates = by_device.get(node["id"], [])
        planned.append({
            "device_id": node["id"],
            "device_name": node["name"],
            "candidate_drivers": candidates,
            "decision": "manual_review_required" if candidates else "no_exact_match_found",
            "proposed_operation": "none",
        })

    return {
        "schema": "oplague.driver-dry-run.v1",
        "mode": "dry_run",
        "install_attempted": False,
        "system_modified": False,
        "requires_manual_review": True,
        "graph": graph,
        "candidate_coverage": summarize_candidate_coverage(graph),
        "devices": planned,
        "summary": {
            "devices": len(planned),
            "candidate_edges": len(graph["edges"]),
            "devices_with_candidates": sum(bool(item["candidate_drivers"]) for item in planned),
            "devices_without_candidates": sum(not item["candidate_drivers"] for item in planned),
        },
        "safety_notes": [
            "No driver was installed, staged, removed, loaded, or downloaded.",
            "Exact PnP identifier matching is discovery evidence, not a compatibility guarantee.",
            "Validate OS build, architecture, INF decoration, catalog signature, rank, policy, and vendor provenance before any future privileged workflow.",
        ],
    }


def summarize_candidate_coverage(graph: Mapping[str, Any]) -> dict[str, Any]:
    """Aggregate exact-ID graph coverage without ranking or approving candidates."""
    if not isinstance(graph, Mapping) or graph.get("schema") != "oplague.device-driver-graph.v1":
        raise ValueError("graph must be an OPlague device-driver graph")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise ValueError("graph nodes and edges must be lists")
    device_ids = {
        node.get("id") for node in nodes
        if isinstance(node, Mapping) and node.get("kind") == "device"
        and isinstance(node.get("id"), str)
    }
    driver_ids = {
        node.get("id") for node in nodes
        if isinstance(node, Mapping) and node.get("kind") == "driver"
        and isinstance(node.get("id"), str)
    }
    devices_by_driver: dict[str, set[str]] = {driver_id: set() for driver_id in driver_ids}
    matched_ids_by_driver: dict[str, set[str]] = {driver_id: set() for driver_id in driver_ids}
    for edge in edges:
        if not isinstance(edge, Mapping):
            raise ValueError("graph edges must contain objects")
        device_id, driver_id = edge.get("device_id"), edge.get("driver_id")
        if device_id not in device_ids or driver_id not in driver_ids:
            raise ValueError("graph edge references an unknown node")
        if edge.get("status") != "exact_identifier_candidate":
            continue
        devices_by_driver[driver_id].add(device_id)
        matched = edge.get("matched_ids", [])
        if isinstance(matched, list):
            matched_ids_by_driver[driver_id].update(
                value for value in matched if isinstance(value, str)
            )
    covered_devices = set().union(*devices_by_driver.values()) if driver_ids else set()
    rows = [
        {
            "driver_id": driver_id,
            "candidate_device_count": len(devices_by_driver[driver_id]),
            "matched_identifier_count": len(matched_ids_by_driver[driver_id]),
        }
        for driver_id in sorted(driver_ids)
    ]
    return {
        "schema": "oplague.driver-candidate-coverage.v1",
        "driver_count": len(driver_ids),
        "device_count": len(device_ids),
        "candidate_edge_count": sum(len(values) for values in devices_by_driver.values()),
        "devices_with_candidates": len(covered_devices),
        "devices_without_candidates": len(device_ids - covered_devices),
        "drivers": rows,
        "semantics": (
            "Exact identifier discovery coverage only; counts do not rank drivers, "
            "prove compatibility, verify signatures or authorize installation."
        ),
    }
