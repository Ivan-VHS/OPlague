"""Conservative, read-only extraction of device-ID evidence from Windows INF files.

This parser deliberately implements a documented subset of INF syntax. It does
not evaluate directives, expand arbitrary strings, follow Include/Needs, or
claim that a parsed model section is installable on the current Windows build.
"""
from __future__ import annotations

import csv
import io
import re
from collections.abc import Iterable
from typing import Any

MAX_INF_CHARS = 2 * 1024 * 1024
MAX_SECTIONS = 20_000
MAX_MODELS = 50_000
_DEVICE_ID_RE = re.compile(r"^[A-Za-z0-9_.&-]+\\[A-Za-z0-9_.&\\-]+$", re.IGNORECASE)


def _strip_comment(line: str) -> str:
    quoted = False
    result: list[str] = []
    index = 0
    while index < len(line):
        char = line[index]
        if char == '"':
            quoted = not quoted
        elif char in (";", "#") and not quoted:
            break
        result.append(char)
        index += 1
    return "".join(result).strip()


def _logical_lines(text: str) -> Iterable[str]:
    pending = ""
    for raw in text.lstrip("\ufeff").splitlines():
        line = _strip_comment(raw)
        if not line and not pending:
            continue
        if line.endswith("\\"):
            pending += line[:-1].rstrip() + " "
            continue
        yield (pending + line).strip()
        pending = ""
    if pending.strip():
        yield pending.strip()


def _csv_fields(value: str) -> list[str]:
    try:
        return [field.strip().strip('"') for field in next(csv.reader(io.StringIO(value), skipinitialspace=True))]
    except (csv.Error, StopIteration):
        return [part.strip().strip('"') for part in value.split(",")]


def _parse_sections(text: str) -> dict[str, list[str]]:
    if not isinstance(text, str):
        raise TypeError("INF content must be text")
    if len(text) > MAX_INF_CHARS:
        raise ValueError(f"INF content exceeds the {MAX_INF_CHARS}-character limit")
    sections: dict[str, list[str]] = {}
    active: str | None = None
    for line in _logical_lines(text):
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            active = line[1:-1].strip().casefold()
            if not active:
                active = None
            elif active not in sections:
                sections[active] = []
                if len(sections) > MAX_SECTIONS:
                    raise ValueError("INF contains too many sections")
            continue
        if active is not None and "=" in line:
            sections[active].append(line)
    return sections


def _parse_version(sections: dict[str, list[str]]) -> dict[str, str]:
    result: dict[str, str] = {}
    wanted = {"provider", "class", "classguid", "driverver", "catalogfile", "catalogfile.nt"}
    for line in sections.get("version", []):
        key, value = line.split("=", 1)
        normalized = key.strip().casefold()
        if normalized in wanted and normalized not in result:
            result[normalized] = value.strip().strip('"')
    return result


def _models_section_names(sections: dict[str, list[str]]) -> list[str]:
    names: list[str] = []
    for line in sections.get("manufacturer", []):
        _, value = line.split("=", 1)
        fields = _csv_fields(value)
        if not fields or not fields[0]:
            continue
        base = fields[0].casefold()
        names.append(base)
        names.extend(f"{base}.{decoration.casefold()}" for decoration in fields[1:] if decoration)
    if not names and "models" in sections:
        names.append("models")
    return list(dict.fromkeys(names))


def parse_inf_document(text: str) -> dict[str, Any]:
    """Extract Version metadata and model IDs without executing INF directives."""
    sections = _parse_sections(text)
    version = _parse_version(sections)
    models: list[dict[str, Any]] = []
    warnings: list[str] = []
    model_sections = _models_section_names(sections)
    if not model_sections:
        warnings.append("No [Manufacturer] model-section mapping was found; compatibility is unknown")
    for section_name in model_sections:
        for line in sections.get(section_name, []):
            description, value = line.split("=", 1)
            fields = _csv_fields(value)
            if not fields:
                continue
            install_section = fields[0]
            identifiers = [item for item in fields[1:] if _DEVICE_ID_RE.fullmatch(item)]
            if not identifiers:
                continue
            models.append({
                "description_token": description.strip(),
                "install_section": install_section,
                "model_section": section_name,
                "device_ids": identifiers,
            })
            if len(models) > MAX_MODELS:
                raise ValueError("INF contains too many model entries")
    if model_sections and not models:
        warnings.append("Model sections were found but no directly parseable device IDs were extracted")
    all_ids = list(dict.fromkeys(identifier for model in models for identifier in model["device_ids"]))
    return {
        "schema": "oplage.inf-evidence.v1",
        "version": version,
        "model_sections": model_sections,
        "models": models,
        "device_ids": all_ids,
        "warnings": warnings,
        "parser_scope": "Direct Manufacturer/Models declarations only; no Include/Needs, decorated OS evaluation, string expansion, or install validation",
    }
