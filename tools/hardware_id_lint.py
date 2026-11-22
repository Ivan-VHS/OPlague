"""Explain the structure of Windows Plug and Play hardware identifiers.

This is a syntax linter only. It does not query a vendor database, confirm that
a device exists, validate a driver package, or make a safety determination.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

MAX_ID_LENGTH = 512
BUS_PREFIXES = {
    "PCI", "USB", "ACPI", "ROOT", "HID", "SWD", "BTH",
    "DISPLAY", "SCSI", "IDE", "VMBUS",
}
_FIELD_SPECS = {
    "PCI": {
        "VEN": (4, "PCI vendor identifier; no manufacturer name is inferred"),
        "DEV": (4, "PCI device identifier"),
        "SUBSYS": (8, "Subsystem vendor and device identifier pair"),
        "REV": (2, "PCI device revision"),
        "CC": (4, "PCI class code"),
        "PROG_IF": (2, "Programming interface code"),
    },
    "USB": {
        "VID": (4, "USB vendor identifier; no manufacturer name is inferred"),
        "PID": (4, "USB product identifier"),
        "REV": (4, "USB device release number"),
        "MI": (2, "USB interface number"),
    },
    "HID": {
        "VID": (4, "HID vendor identifier; no manufacturer name is inferred"),
        "PID": (4, "HID product identifier"),
        "REV": (4, "HID device release number"),
        "MI": (2, "HID interface number"),
    },
}
_REQUIRED_FIELDS = {"PCI": ("VEN", "DEV"), "USB": ("VID", "PID")}
_TOKEN = re.compile(r"^(?P<key>[A-Z][A-Z0-9_]*)_(?P<value>[A-Z0-9]+)$")
_OPAQUE_SEGMENT = re.compile(r"^[A-Z0-9_&.-]{1,128}$")


def _finding(code: str, severity: str, message: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message}


def lint_hardware_id(value: Any) -> dict[str, Any]:
    """Return a deterministic, bounded, explanation-only lint report."""
    findings: list[dict[str, str]] = []
    components: list[dict[str, Any]] = []

    if not isinstance(value, str):
        return {
            "schema": "oplage.hardware-id-lint.v1",
            "input": None,
            "normalized": None,
            "bus": None,
            "valid": False,
            "components": [],
            "findings": [_finding("OPL-E0100", "error", "Hardware ID must be text.")],
            "semantics": "Syntax inspection only; no existence, compatibility or safety verdict.",
        }

    raw = value.strip()
    if not raw:
        findings.append(_finding("OPL-E0100", "error", "Hardware ID is empty."))
    if len(raw) > MAX_ID_LENGTH:
        findings.append(_finding("OPL-E0100", "error", f"Hardware ID exceeds {MAX_ID_LENGTH} characters."))
    if any(ord(char) < 32 or ord(char) == 127 for char in raw):
        findings.append(_finding("OPL-E0100", "error", "Control characters are not allowed in a hardware ID."))

    normalized = raw.replace("/", "\\").upper()
    if normalized.startswith("\\\\") or any(part in {".", ".."} for part in normalized.split("\\")):
        findings.append(_finding("OPL-E0100", "error", "Empty, current-directory or parent-directory path components are not accepted."))
    segments = normalized.split("\\")
    bus = segments[0] if segments and segments[0] else None
    if not bus or len(segments) < 2 or not segments[1]:
        findings.append(_finding("OPL-E0100", "error", "Expected a bus prefix and at least one identifier component, for example PCI\\VEN_8086&DEV_1234."))
    elif bus not in BUS_PREFIXES:
        findings.append(_finding("OPL-E0101", "error", f"Unrecognized bus prefix {bus!r}; the linter does not guess its grammar."))
    elif len(segments) > 4:
        findings.append(_finding("OPL-W0105", "warning", "The identifier has more path components than the linter explains; remaining components are preserved without interpretation."))

    if bus and len(segments) >= 2:
        components.append({
            "name": "bus",
            "value": bus,
            "valid": bus in BUS_PREFIXES,
            "meaning": "Plug and Play bus or enumerator prefix",
        })

    if bus in _FIELD_SPECS and len(segments) >= 2 and segments[1]:
        fields: dict[str, str] = {}
        for token in segments[1].split("&"):
            match = _TOKEN.fullmatch(token)
            if not match:
                findings.append(_finding("OPL-E0102", "error", f"Malformed component {token!r}; expected NAME_HEX form."))
                components.append({"name": "unparsed", "value": token, "valid": False, "meaning": "Malformed field"})
                continue
            key, field_value = match.group("key"), match.group("value")
            spec = _FIELD_SPECS[bus].get(key)
            if key in fields:
                findings.append(_finding("OPL-E0103", "error", f"Field {key} occurs more than once."))
                valid = False
            elif spec is None:
                findings.append(_finding("OPL-W0104", "warning", f"Field {key} is not interpreted for the {bus} bus; it is retained as supplied."))
                valid = True
            else:
                expected_length, _ = spec
                valid = len(field_value) == expected_length and all(char in "0123456789ABCDEF" for char in field_value)
                if not valid:
                    findings.append(_finding("OPL-E0102", "error", f"{key} must contain exactly {expected_length} hexadecimal characters."))
            fields[key] = field_value
            components.append({
                "name": key.lower(),
                "value": field_value,
                "valid": valid,
                "meaning": spec[1] if spec else "Unrecognized field; no meaning is assumed",
            })

        required = _REQUIRED_FIELDS.get(bus, ())
        missing = [field for field in required if field not in fields]
        if missing:
            findings.append(_finding("OPL-E0102", "error", f"{bus} identifier is missing required field(s): {', '.join(missing)}."))

    elif bus in {"ACPI", "ROOT", "SWD", "BTH", "DISPLAY", "SCSI", "IDE", "VMBUS"} and len(segments) >= 2:
        token = segments[1]
        if not _OPAQUE_SEGMENT.fullmatch(token):
            findings.append(_finding("OPL-E0102", "error", "The bus identifier contains characters or a length not accepted by the generic syntax check."))
        else:
            components.append({
                "name": "identifier",
                "value": token,
                "valid": True,
                "meaning": "Opaque bus-specific identifier; no vendor or device database lookup is performed",
            })
            findings.append(_finding("OPL-I0106", "information", f"{bus} identifier syntax is preserved as an opaque token; no detailed vendor grammar is assumed."))

    if bus == "HID" and len(segments) >= 2 and not _FIELD_SPECS["HID"].get(segments[1].split("&", 1)[0].split("_", 1)[0]):
        token = segments[1]
        if _OPAQUE_SEGMENT.fullmatch(token):
            components.append({
                "name": "identifier",
                "value": token,
                "valid": True,
                "meaning": "Opaque HID identifier; no vendor or device database lookup is performed",
            })
            findings.append(_finding("OPL-I0106", "information", "HID identifier is not in VID/PID form; it is preserved without guessing its semantics."))

    errors = any(item["severity"] == "error" for item in findings)
    return {
        "schema": "oplage.hardware-id-lint.v1",
        "input": raw,
        "normalized": normalized if len(raw) <= MAX_ID_LENGTH else None,
        "bus": bus,
        "valid": not errors,
        "components": components,
        "findings": findings,
        "semantics": "Syntax inspection only; not proof that a device exists, that a driver is compatible, or that a package is safe.",
    }


def format_report(report: dict[str, Any]) -> str:
    lines = [str(report.get("normalized") or report.get("input") or "(empty hardware ID)")]
    lines.append(f"  bus: {report.get('bus') or 'unknown'}")
    for item in report.get("components", []):
        lines.append(f"  {item['name']:<12} {item['value']:<18} {'ok' if item['valid'] else 'invalid'}  {item['meaning']}")
    if report.get("findings"):
        lines.append("  findings:")
        for finding in report["findings"]:
            lines.append(f"    {finding['severity']}[{finding['code']}]: {finding['message']}")
    lines.append("  verdict: syntax valid" if report.get("valid") else "  verdict: syntax issues found")
    lines.append("  " + report["semantics"])
    return "\\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Explain a Windows Plug and Play hardware identifier without querying or modifying the host.")
    parser.add_argument("hardware_id", help="one PCI\\, USB\\, ACPI\\, HID\\ or other supported identifier")
    parser.add_argument("--json", action="store_true", help="emit the structured lint report as JSON")
    args = parser.parse_args(argv)
    report = lint_hardware_id(args.hardware_id)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report(report))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
