"""Portable, deterministic export for OPlague's read-only evidence reports."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from collections.abc import Mapping
from typing import Any

_SENSITIVE_FIELDS = {
    "pnp_id", "pnpdeviceid", "hardware_id", "hardware_ids",
    "compatible_id", "compatible_ids", "instance_id", "instanceid",
    "serial", "serial_number", "serialnumber",
}


def anonymize_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Copy a report while replacing device identifiers with stable local hashes."""
    if not isinstance(report, Mapping):
        raise TypeError("report must be a mapping")

    replacements: dict[str, str] = {}

    def private_value(value: Any) -> str:
        original = str(value)
        if original not in replacements:
            digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:16]
            replacements[original] = f"redacted-{digest}"
        return replacements[original]

    def visit(value: Any, key: str = "") -> Any:
        normalized = key.casefold()
        if normalized in {"path", "device_path", "source_path"}:
            return "<redacted>"
        if normalized in _SENSITIVE_FIELDS:
            if isinstance(value, list):
                return [private_value(item) for item in value]
            if value is None:
                return None
            return private_value(value)
        if isinstance(value, Mapping):
            return {str(child_key): visit(child, str(child_key)) for child_key, child in value.items()}
        if isinstance(value, list):
            return [visit(item, key) for item in value]
        if isinstance(value, tuple):
            return [visit(item, key) for item in value]
        return value

    return visit(report)


def _as_packages(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    packages = report.get("packages")
    if isinstance(packages, list):
        return [dict(item) for item in packages if isinstance(item, Mapping)]
    return [dict(report)]


def render_report_json(report: Mapping[str, Any]) -> str:
    if not isinstance(report, Mapping):
        raise TypeError("report must be a mapping")
    return json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"


def render_report_csv(report: Mapping[str, Any]) -> str:
    """Render one row per package; nested evidence remains JSON in its cell."""
    if not isinstance(report, Mapping):
        raise TypeError("report must be a mapping")
    rows = _as_packages(report)
    flattened: list[dict[str, str]] = []
    fieldnames: set[str] = set()
    for package in rows:
        row = {
            str(key): (
                json.dumps(value, ensure_ascii=False, sort_keys=True)
                if isinstance(value, (dict, list, tuple))
                else "" if value is None else str(value)
            )
            for key, value in package.items()
        }
        flattened.append(row)
        fieldnames.update(row)
    if not fieldnames:
        return ""
    ordered_fields = sorted(fieldnames, key=str.casefold)
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=ordered_fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(flattened)
    return stream.getvalue()


def _markdown_cell(value: Any) -> str:
    if isinstance(value, (dict, list, tuple)):
        rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    elif value is None:
        rendered = "—"
    else:
        rendered = str(value)
    return rendered.replace("|", r"\|").replace("\r", " ").replace("\n", " ")


def render_report_markdown(report: Mapping[str, Any]) -> str:
    if not isinstance(report, Mapping):
        raise TypeError("report must be a mapping")
    lines = [
        "# OPlague inspection report",
        "",
        f"- Schema: {_markdown_cell(report.get('schema', 'single-package report'))}",
        "- Mode: read_only",
        "- Meaning: evidence for review, not a driver-installation recommendation",
        "",
    ]
    packages = _as_packages(report)
    for index, package in enumerate(packages, start=1):
        name = package.get("file_name") or f"Package {index}"
        lines.extend([f"## {index}. {_markdown_cell(name)}", "", "| Field | Value |", "|---|---|"])
        for key in sorted(package, key=str.casefold):
            lines.append(f"| {_markdown_cell(key)} | {_markdown_cell(package[key])} |")
        lines.append("")
    totals = report.get("totals")
    if isinstance(totals, Mapping):
        lines.extend(["## Bundle totals", "", "| Metric | Value |", "|---|---|"])
        for key in sorted(totals, key=str.casefold):
            lines.append(f"| {_markdown_cell(key)} | {_markdown_cell(totals[key])} |")
        lines.append("")
    lines.extend([
        "## Limitations",
        "",
        "This report records inspected metadata and hashes. It does not establish publisher trust, "
        "operating-system compatibility, driver safety, or suitability for installation.",
        "",
    ])
    return "\n".join(lines)


def render_report(report: Mapping[str, Any], format_name: str, *, anonymize: bool = False) -> str:
    """Render JSON, CSV or Markdown, optionally anonymizing device-specific identifiers."""
    selected = anonymize_report(report) if anonymize else report
    normalized = format_name.casefold().lstrip(".")
    if normalized == "json":
        return render_report_json(selected)
    if normalized == "csv":
        return render_report_csv(selected)
    if normalized in {"md", "markdown"}:
        return render_report_markdown(selected)
    raise ValueError("format must be json, csv or markdown")
