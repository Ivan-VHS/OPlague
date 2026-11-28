"""Read-only USB device-tree formatter for exported Plug and Play records.

The default JSON output uses local sequence labels and omits raw PnP Instance
IDs because those identifiers can contain device serial numbers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

MAX_DEVICES = 20_000
MAX_INSTANCE_ID = 2_048
MAX_DEPTH = 128


def _clean_text(value: Any, default: str, maximum: int) -> str:
    if not isinstance(value, str):
        return default
    cleaned = "".join(char for char in value.strip() if ord(char) >= 32 and ord(char) != 127)
    return cleaned[:maximum] or default


def _normalize_instance_id(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be text")
    normalized = value.strip().replace("/", "\\").upper()
    if not normalized or len(normalized) > MAX_INSTANCE_ID or "\x00" in normalized:
        raise ValueError(f"{field} is empty or exceeds {MAX_INSTANCE_ID} characters")
    if not normalized.startswith("USB\\"):
        raise ValueError(f"{field} must be a USB Plug and Play identifier")
    if any(part in {".", ".."} for part in normalized.split("\\")):
        raise ValueError(f"{field} contains a path-like component")
    return normalized


def build_usb_tree(
    devices: list[dict[str, Any]],
    *,
    include_instance_ids: bool = False,
) -> dict[str, Any]:
    """Build a stable hierarchy from an exported list of USB PnP records."""
    if not isinstance(devices, list) or len(devices) > MAX_DEVICES:
        raise ValueError(f"devices must be a list with at most {MAX_DEVICES} records")

    records: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(devices):
        if not isinstance(raw, dict):
            raise TypeError(f"devices[{index}] must be an object")
        instance_id = _normalize_instance_id(
            raw.get("instance_id", raw.get("InstanceId")),
            f"devices[{index}].instance_id",
        )
        if instance_id in records:
            raise ValueError(f"duplicate USB InstanceId at devices[{index}]")
        parent_raw = raw.get("parent_instance_id", raw.get("Parent"))
        parent_id = None
        if isinstance(parent_raw, str) and parent_raw.strip():
            parent_value = parent_raw.strip().replace("/", "\\").upper()
            if len(parent_value) <= MAX_INSTANCE_ID and parent_value.startswith("USB\\"):
                parent_id = parent_value
        records[instance_id] = {
            "instance_id": instance_id,
            "parent": parent_id,
            "name": _clean_text(raw.get("name", raw.get("FriendlyName")), "USB device", 256),
            "status": _clean_text(raw.get("status", raw.get("Status")), "Unknown", 64),
            "service": _clean_text(raw.get("service", raw.get("Service")), "", 128),
        }

    # Every node has at most one parent, so cycle detection is a bounded walk
    # over parent links rather than a recursive graph search.
    state: dict[str, int] = {}
    for start in records:
        current = start
        trail: list[str] = []
        while current in records and state.get(current, 0) == 0:
            state[current] = 1
            trail.append(current)
            parent = records[current]["parent"]
            if parent not in records:
                current = parent
                break
            current = parent
        if current in records and state.get(current) == 1:
            raise ValueError("USB parent references contain a cycle")
        for instance_id in trail:
            state[instance_id] = 2

    identifiers = {
        instance_id: f"usb-{index:05d}"
        for index, instance_id in enumerate(sorted(records), start=1)
    }
    children: dict[str, list[str]] = {instance_id: [] for instance_id in records}
    roots: list[str] = []
    orphan_count = 0
    for instance_id, record in records.items():
        parent = record["parent"]
        if parent in records:
            children[parent].append(instance_id)
        else:
            roots.append(instance_id)
            if parent is not None:
                orphan_count += 1

    def make_node(instance_id: str, depth: int) -> dict[str, Any]:
        if depth > MAX_DEPTH:
            raise ValueError(f"USB hierarchy exceeds the {MAX_DEPTH}-level safety limit")
        record = records[instance_id]
        node: dict[str, Any] = {
            "id": identifiers[instance_id],
            "name": record["name"],
            "status": record["status"],
            "children": [
                make_node(child, depth + 1)
                for child in sorted(children[instance_id], key=lambda item: (records[item]["name"].casefold(), item))
            ],
        }
        if record["service"]:
            node["service"] = record["service"]
        if include_instance_ids:
            node["instance_id"] = instance_id
        return node

    root_nodes = [
        make_node(instance_id, 0)
        for instance_id in sorted(roots, key=lambda item: (records[item]["name"].casefold(), item))
    ]
    return {
        "schema": "oplague.usb-tree.v1",
        "device_count": len(records),
        "root_count": len(root_nodes),
        "orphan_count": orphan_count,
        "includes_instance_ids": include_instance_ids,
        "roots": root_nodes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render a read-only USB device tree from exported PnP JSON.")
    parser.add_argument("input", type=Path, help="JSON file containing a list of USB device records")
    parser.add_argument("--show-instance-ids", action="store_true",
                        help="include raw PnP IDs; they may contain device serial numbers")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        devices = payload.get("devices") if isinstance(payload, dict) else payload
        report = build_usb_tree(devices, include_instance_ids=args.show_instance_ids)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as error:
        print(f"usb-tree-dump: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
