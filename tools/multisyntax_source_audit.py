"""Read-only audit of Reaper multi-syntax validation reports.

OPlague verifies that a Reaper syntax-only report belongs to the exact source
file and checks declared capability requirements against the selected frontend.
It never executes or rewrites source code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPORT_SCHEMAS = {
    "reaper.syntax-validation.v1",
    "reaper.polyglot-validation.v1",
}
SUPPORTED_SYNTAXES = {"reaper", "python", "pipeline", "lisp", "forth", "brainfuck", "befunge93"}
CAPABILITY_ALLOWLISTS = {
    "reaper": {"pure", "console_output", "filesystem_io", "resource_management", "modules"},
    "python": {"pure", "console_output"},
    "pipeline": {"pure", "console_output"},
    "lisp": {"pure", "console_output"},
    "forth": {"pure", "console_output", "byte_input", "byte_output", "stack_memory"},
    "brainfuck": {"pure", "byte_input", "byte_output", "tape_memory"},
    "befunge93": {"pure", "byte_input", "byte_output", "two_dimensional_grid", "stack_memory"},
}
MAX_SOURCE_BYTES = 1024 * 1024
MAX_REPORT_BYTES = 1024 * 1024
MAX_CAPABILITIES = 64
CAPABILITY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


class SyntaxAuditError(ValueError):
    """Invalid source file or Reaper validation evidence."""


def _load_json(path: Path, maximum: int, label: str) -> Any:
    if path.is_symlink() or not path.is_file():
        raise SyntaxAuditError(f"{label} must be a regular, non-symlink file")
    if path.stat().st_size > maximum:
        raise SyntaxAuditError(f"{label} exceeds the {maximum}-byte input limit")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise SyntaxAuditError(f"cannot read {label}: {error}") from error
    except json.JSONDecodeError as error:
        raise SyntaxAuditError(f"{label} is not valid JSON: {error}") from error


def audit_validation_report(
    source_path: str | Path,
    report: dict[str, Any],
    requested_capabilities: list[str] | None = None,
) -> dict[str, Any]:
    source = Path(source_path).expanduser()
    if source.is_symlink() or not source.is_file():
        raise SyntaxAuditError("source must be a regular, non-symlink file")
    if source.stat().st_size > MAX_SOURCE_BYTES:
        raise SyntaxAuditError("source exceeds the 1 MiB input limit")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()

    if not isinstance(report, dict) or report.get("schema") not in REPORT_SCHEMAS:
        raise SyntaxAuditError("unsupported Reaper syntax validation report schema")
    if report.get("execution_performed") is not False:
        raise SyntaxAuditError("source evidence must come from a non-executing syntax check")
    if report.get("valid") is not True:
        raise SyntaxAuditError("Reaper did not report valid syntax")
    if report.get("source_sha256") != digest:
        raise SyntaxAuditError("source SHA-256 does not match the Reaper validation report")

    schema = report["schema"]
    blocks: list[dict[str, Any]]
    if schema == "reaper.syntax-validation.v1":
        syntax = report.get("syntax")
        if syntax not in SUPPORTED_SYNTAXES:
            raise SyntaxAuditError("validation report names an unknown syntax frontend")
        blocks = [{
            "syntax": syntax,
            "valid": report.get("valid"),
            "analysis": report.get("analysis", {}),
        }]
    else:
        raw_blocks = report.get("blocks")
        if (
            not isinstance(raw_blocks, list)
            or not raw_blocks
            or len(raw_blocks) > 128
            or report.get("block_count") != len(raw_blocks)
        ):
            raise SyntaxAuditError("polyglot validation report has an invalid block inventory")
        blocks = []
        for index, block in enumerate(raw_blocks):
            if not isinstance(block, dict) or block.get("valid") is not True:
                raise SyntaxAuditError(f"polyglot block {index + 1} is not validated")
            if block.get("execution_performed") is not False:
                raise SyntaxAuditError(f"polyglot block {index + 1} is not marked non-executing")
            if block.get("syntax") not in SUPPORTED_SYNTAXES:
                raise SyntaxAuditError(f"polyglot block {index + 1} names an unknown syntax")
            blocks.append(block)

    requested = requested_capabilities or []
    if not isinstance(requested, list) or len(requested) > MAX_CAPABILITIES:
        raise SyntaxAuditError(f"requested_capabilities must contain at most {MAX_CAPABILITIES} values")
    if any(not isinstance(item, str) or not CAPABILITY_PATTERN.fullmatch(item) for item in requested):
        raise SyntaxAuditError("requested capabilities must use canonical lowercase identifiers")
    requested = list(dict.fromkeys(requested))

    syntaxes = list(dict.fromkeys(block["syntax"] for block in blocks))
    shared = set.intersection(*(CAPABILITY_ALLOWLISTS[syntax] for syntax in syntaxes))
    unsupported = sorted(set(requested) - shared)
    findings: list[dict[str, str]] = []
    if unsupported:
        findings.append({
            "code": "OPL-SYNTAX-CAPABILITY",
            "severity": "blocker",
            "message": "The selected syntax frontend does not provide: " + ", ".join(unsupported),
            "next_step": "Remove the undeclared dependency or select an explicitly reviewed host-side bridge.",
        })

    for index, block in enumerate(blocks):
        analysis = block.get("analysis", {})
        if not isinstance(analysis, dict):
            continue
        warnings = analysis.get("pointer_balance_warnings", [])
        if not isinstance(warnings, list):
            continue
        for warning in warnings:
            if isinstance(warning, dict):
                findings.append({
                    "code": str(warning.get("code") or "OPL-SYNTAX-WARNING"),
                    "severity": "warning",
                    "message": f"Block {index + 1}: {str(warning.get('message') or 'syntax analyzer warning')}",
                    "next_step": "Review the loop pointer invariant before relying on the program's tape layout.",
                })

    status = "blocked" if unsupported else "attention_required" if findings else "reviewed"
    return {
        "schema": "oplague.multisyntax-source-audit.v1",
        "status": status,
        "source": str(source.resolve()),
        "source_sha256": digest,
        "validation_schema": schema,
        "validated_syntaxes": syntaxes,
        "block_count": len(blocks),
        "requested_capabilities": requested,
        "supported_capabilities": sorted(shared),
        "unsupported_capabilities": unsupported,
        "findings": findings,
        "source_execution_performed": False,
        "host_settings_changed": False,
    }


def audit_files(
    source_path: str | Path,
    report_path: str | Path,
    requested_capabilities: list[str] | None = None,
) -> dict[str, Any]:
    report = _load_json(Path(report_path).expanduser(), MAX_REPORT_BYTES, "validation report")
    return audit_validation_report(source_path, report, requested_capabilities)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify Reaper syntax-only evidence and audit declared frontend capabilities.")
    parser.add_argument("source", type=Path)
    parser.add_argument("report", type=Path, help="JSON result from reaper syntax --check --json")
    parser.add_argument("--require-capability", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = audit_files(args.source, args.report, args.require_capability)
        encoded = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            output = args.output.expanduser()
            if output.resolve() in {args.source.resolve(), args.report.resolve()}:
                raise SyntaxAuditError("audit output must not overwrite an input file")
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(encoded, encoding="utf-8", newline="\n")
        else:
            print(encoded, end="")
        return 1 if result["status"] == "blocked" else 0
    except (SyntaxAuditError, OSError, ValueError, TypeError) as error:
        print(f"oplague-multisyntax-audit: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
