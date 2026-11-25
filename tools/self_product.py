"""Read-only vertical self-products for OPlague's exact-candidate graph."""
from __future__ import annotations

from collections.abc import Mapping
import hashlib
from typing import Any

GRAPH_SCHEMA = "oplague.device-driver-graph.v1"
SELF_PRODUCT_SCHEMA = "oplague.vertical-self-product.v1"
MAX_NODES = 256
MAX_EDGES = 32_768
MAX_DEPTH = 8
MAX_REPORTED_PAIRS = 4_096


def _node_ref(kind: str, identifier: str) -> str:
    """Return a stable pseudonymous reference without exposing PnP identifiers."""
    payload = (kind + "\0" + identifier).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def vertical_self_product(graph: Any, *, depth: int = 2) -> dict[str, Any]:
    """Repeatedly square an exact-ID bipartite graph using boolean arithmetic.

    Each level computes A(k+1) = A(k) × A(k), where multiplication is AND
    and accumulation is OR. Only exact_identifier_candidate edges participate;
    architecture-mismatch and other non-candidate edges are excluded. The
    output reports path reachability, not driver compatibility or approval.
    """
    if isinstance(depth, bool) or not isinstance(depth, int):
        raise TypeError("depth must be an integer")
    if not 1 <= depth <= MAX_DEPTH:
        raise ValueError(f"depth must be between 1 and {MAX_DEPTH}")
    if not isinstance(graph, Mapping) or graph.get("schema") != GRAPH_SCHEMA:
        raise ValueError(f"graph schema must be {GRAPH_SCHEMA}")

    raw_nodes = graph.get("nodes")
    raw_edges = graph.get("edges")
    if not isinstance(raw_nodes, list) or len(raw_nodes) > MAX_NODES:
        raise ValueError(f"graph.nodes must be a list of at most {MAX_NODES} nodes")
    if not isinstance(raw_edges, list) or len(raw_edges) > MAX_EDGES:
        raise ValueError(f"graph.edges must be a list of at most {MAX_EDGES} edges")

    nodes: list[dict[str, str]] = []
    index_by_id: dict[str, int] = {}
    for index, node in enumerate(raw_nodes):
        if not isinstance(node, Mapping):
            raise TypeError("graph nodes must be objects")
        identifier, kind = node.get("id"), node.get("kind")
        if not isinstance(identifier, str) or not identifier or len(identifier) > 512:
            raise ValueError("each graph node needs a bounded non-empty string id")
        if kind not in {"device", "driver"}:
            raise ValueError("graph node kind must be device or driver")
        if identifier in index_by_id:
            raise ValueError(f"duplicate graph node id: {identifier}")
        index_by_id[identifier] = index
        nodes.append({"kind": kind, "ref": _node_ref(kind, identifier)})

    rows = [0] * len(nodes)
    seen_edges: set[tuple[str, str]] = set()
    exact_candidate_edge_count = 0
    for edge in raw_edges:
        if not isinstance(edge, Mapping):
            raise TypeError("graph edges must be objects")
        device_id, driver_id = edge.get("device_id"), edge.get("driver_id")
        if device_id not in index_by_id or driver_id not in index_by_id:
            raise ValueError("graph edge references an unknown node")
        device_index, driver_index = index_by_id[device_id], index_by_id[driver_id]
        if nodes[device_index]["kind"] != "device" or nodes[driver_index]["kind"] != "driver":
            raise ValueError("graph edges must connect a device to a driver")
        if edge.get("status") != "exact_identifier_candidate":
            continue
        matched_ids = edge.get("matched_ids")
        if not isinstance(matched_ids, list) or not matched_ids or any(
            not isinstance(value, str) or not value for value in matched_ids
        ):
            raise ValueError("exact candidate edges require matched identifier evidence")
        key = (device_id, driver_id)
        if key in seen_edges:
            raise ValueError("duplicate exact candidate edge")
        seen_edges.add(key)
        exact_candidate_edge_count += 1
        rows[device_index] |= 1 << driver_index
        rows[driver_index] |= 1 << device_index

    layers: list[dict[str, Any]] = []
    for level in range(1, depth + 1):
        squared: list[int] = []
        for reachable_intermediates in rows:
            reachable_targets = 0
            remaining = reachable_intermediates
            while remaining:
                least_bit = remaining & -remaining
                middle = least_bit.bit_length() - 1
                reachable_targets |= rows[middle]
                remaining ^= least_bit
            squared.append(reachable_targets)

        ordered_pair_count = sum(row.bit_count() for row in squared)
        diagonal_self_paths = sum(
            1 for index, row in enumerate(squared) if row & (1 << index)
        )
        relations: list[dict[str, Any]] = []
        for source_index, row in enumerate(squared):
            remaining = row
            while remaining and len(relations) < MAX_REPORTED_PAIRS:
                least_bit = remaining & -remaining
                target_index = least_bit.bit_length() - 1
                relations.append({
                    "source_ref": nodes[source_index]["ref"],
                    "target_ref": nodes[target_index]["ref"],
                    "source_kind": nodes[source_index]["kind"],
                    "target_kind": nodes[target_index]["kind"],
                    "self_path": source_index == target_index,
                })
                remaining ^= least_bit

        layers.append({
            "level": level,
            "path_length": 1 << level,
            "ordered_pair_count": ordered_pair_count,
            "diagonal_self_paths": diagonal_self_paths,
            "reported_pair_count": len(relations),
            "omitted_pair_count": ordered_pair_count - len(relations),
            "relations": relations,
        })
        rows = squared

    return {
        "schema": SELF_PRODUCT_SCHEMA,
        "mode": "read_only",
        "input_schema": GRAPH_SCHEMA,
        "depth": depth,
        "node_count": len(nodes),
        "exact_candidate_edge_count": exact_candidate_edge_count,
        "nodes": [
            {"index": index, **node} for index, node in enumerate(nodes)
        ],
        "layers": layers,
        "semantics": (
            "Boolean even-length paths through exact identifier candidate edges. "
            "Relations are discovery evidence only; they do not certify driver "
            "compatibility, rank candidates, or authorize installation."
        ),
        "safety": {
            "raw_node_identifiers_emitted": False,
            "driver_installation_attempted": False,
            "system_modified": False,
        },
    }
