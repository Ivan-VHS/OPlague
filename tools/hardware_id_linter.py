"""Format-only linting for Windows Plug and Play hardware identifiers.

The linter explains the shape of an identifier. It does not query hardware,
look up manufacturers, install drivers, or determine package safety.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

from .device_graph import normalize_hardware_id

_BUS_NAMES = {
    "PCI": "PCI",
    "USB": "USB",
    "ACPI": "ACPI",
    "ROOT": "ROOT-enumerated device",
    "HID": "Human Interface Device",
    "SWD": "Software device",
    "BTH": "Bluetooth",
    "DISPLAY": "Display",
    "SCSI": "SCSI",
    "IDE": "IDE",
    "VMBUS": "Hyper-V virtual bus",
}
_KEY_RE = re.compile(r"^[A-Z][A-Z0-9]{0,15}$")
_VALUE_RE = re.compile(r"^[A-Z0-9.-]{1,64}$")
_PATH_RE = re.compile(r"^[A-Z0-9_.&-]{1,128}$")
_HEX_RE = re.compile(r"^[0-9A-F]+$")

_FIELD_LABELS = {
    "VEN": "Vendor identifier",
    "VID": "Vendor identifier",
    "DEV": "Device identifier",
    "PID": "Product identifier",
    "SUBSYS": "Subsystem identifier",
    "REV": "Revision",
    "CC": "PCI class code",
    "MI": "USB interface number",
}
_FIELD_RULES = {
    "PCI": {
        "VEN": (4, 4, True),
        "DEV": (4, 4, True),
        "SUBSYS": (8, 8, False),
        "REV": (2, 2, False),
        "CC": (4, 6, False),
    },
    "USB": {
        "VID": (4, 4, True),
        "PID": (4, 4, True),
        "REV": (4, 4, False),
        "MI": (2, 2, False),
    },
}
_LIMITATIONS = [
    "Checks identifier syntax only; it does not prove that a device exists.",
    "Does not look up vendor names or validate driver compatibility.",
    "Does not assess package safety and performs no system changes.",
]


def lint_hardware_id(value: Any) -> dict[str, Any]:
    """Return a structured explanation of a PnP identifier's syntax."""
    result: dict[str, Any] = {
        "input": value if isinstance(value, str) else None,
        "normalized": None,
        "bus": None,
        "bus_name": None,
        "scope": None,
        "fields": [],
        "opaque_components": [],
        "additional_path_segments": [],
        "errors": [],
        "notes": [],
        "limitations": list(_LIMITATIONS),
        "valid": False,
    }

    if not isinstance(value, str):
        result["errors"].append("Hardware ID must be a string.")
        return result

    normalized = normalize_hardware_id(value)
    if not normalized:
        result["errors"].append(
            "Identifier is empty, too long, contains a NUL byte, or uses an unsupported bus prefix."
        )
        return result

    result["normalized"] = normalized
    segments = normalized.split("\\")
    if len(segments) < 2 or any(not segment for segment in segments):
        result["errors"].append("Identifier must contain a bus prefix and a non-empty device component.")
        return result

    bus = segments[0]
    result["bus"] = bus
    result["bus_name"] = _BUS_NAMES.get(bus, bus)

    for index, segment in enumerate(segments[1:], start=1):
        if segment in {".", ".."} or not _PATH_RE.fullmatch(segment):
            result["errors"].append(f"Path component {index} contains unsupported characters or traversal syntax.")
    if result["errors"]:
        return result

    identity = segments[1]
    parsed: dict[str, str] = {}
    opaque: list[str] = []

    for token in identity.split("&"):
        if not token:
            result["errors"].append("Identifier contains an empty attribute.")
            continue
        if "_" not in token:
            if not _PATH_RE.fullmatch(token):
                result["errors"].append(f"Malformed identifier component: {token!r}.")
            else:
                opaque.append(token)
            continue

        key, field_value = token.split("_", 1)
        if not _KEY_RE.fullmatch(key) or not _VALUE_RE.fullmatch(field_value):
            result["errors"].append(f"Malformed attribute: {token!r}.")
            continue
        if key in parsed:
            result["errors"].append(f"Duplicate attribute: {key}.")
            continue
        parsed[key] = field_value

    result["opaque_components"] = opaque
    rules = _FIELD_RULES.get(bus)
    if rules:
        for key, (minimum, maximum, required) in rules.items():
            field_value = parsed.get(key)
            if field_value is None:
                if required:
                    result["errors"].append(f"Required {key} attribute is missing.")
                continue
            if len(field_value) < minimum or len(field_value) > maximum or not _HEX_RE.fullmatch(field_value):
                expected = f"{minimum} hexadecimal digits" if minimum == maximum else f"{minimum} or {maximum} hexadecimal digits"
                result["errors"].append(f"{key} must contain {expected}.")

    for key, field_value in parsed.items():
        rules_for_bus = rules or {}
        if key not in rules_for_bus:
            result["notes"].append(
                f"Attribute {key} is preserved but has no bus-specific format rule in this linter."
            )
        rule = rules_for_bus.get(key)
        result["fields"].append({
            "code": key,
            "label": _FIELD_LABELS.get(key, key),
            "value": field_value,
            "format": (
                f"{rule[0]} hexadecimal digits"
                if rule and rule[0] == rule[1]
                else f"{rule[0]} or {rule[1]} hexadecimal digits"
                if rule
                else "syntax checked; value not interpreted"
            ),
        })

    if len(segments) > 2:
        result["additional_path_segments"] = segments[2:]
        result["scope"] = "instance-id-like path"
        result["notes"].append(
            "Additional path components are present; this may be a device-instance identifier rather than a hardware-ID string."
        )
    else:
        result["scope"] = "single device identifier component"

    if opaque and bus not in _FIELD_RULES:
        result["notes"].append(
            "This bus uses an opaque identifier component; the linter does not infer its meaning."
        )
    if bus not in {"PCI", "USB"}:
        result["notes"].append(
            "Only the general identifier shape was checked for this bus; no device database was consulted."
        )

    result["valid"] = not result["errors"]
    return result


def format_report(result: dict[str, Any]) -> str:
    """Format a lint result for a human-readable terminal."""
    label = result.get("normalized") or str(result.get("input") or "<empty>")
    lines = [label]
    lines.append(f"  bus: {result.get('bus') or 'unresolved'} ({result.get('bus_name') or 'unknown'})")
    lines.append(f"  scope: {result.get('scope') or 'unresolved'}")
    for field in result.get("fields", []):
        lines.append(f"  {field['label'].lower()}: {field['value']} ({field['format']})")
    for component in result.get("opaque_components", []):
        lines.append(f"  component: {component} (not interpreted)")
    lines.append(f"  structure: {'valid' if result.get('valid') else 'invalid'}")
    for error in result.get("errors", []):
        lines.append(f"  error: {error}")
    for note in result.get("notes", []):
        lines.append(f"  note: {note}")
    for limitation in result.get("limitations", []):
        lines.append(f"  limitation: {limitation}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="hardware-id-linter",
        description="Explain the syntax of Windows Plug and Play hardware identifiers without querying or changing the system.",
    )
    parser.add_argument("--json", action="store_true", help="write machine-readable JSON")
    parser.add_argument("hardware_ids", nargs="+", metavar="HARDWARE_ID", help="one or more quoted PnP identifiers")
    args = parser.parse_args(argv)

    reports = [lint_hardware_id(value) for value in args.hardware_ids]
    if args.json:
        payload: Any = reports[0] if len(reports) == 1 else reports
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        for index, report in enumerate(reports):
            if index:
                print()
            print(format_report(report))

    return 0 if all(report["valid"] for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
