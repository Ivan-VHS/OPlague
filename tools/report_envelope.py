#!/usr/bin/env python3
"""Wrap tool-specific JSON output in the shared Ivan-VHS report envelope v1.

The wrapper is local and offline. It preserves the tool-specific result payload
and never writes to the input file or records the input path in the report.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import platform
import sys
from typing import Any

MAX_RESULT_BYTES = 16 * 1024 * 1024
MAX_HASH_FILE_BYTES = 1024 * 1024 * 1024
MAX_JSON_INTEGER_DIGITS = 1024
MAX_JSON_NESTING_DEPTH = 128
PROJECT_LIMITATIONS = {
    "pytyliki": (
        "hardware inspection is read-only",
        "performance claims require measurements on the target host",
    ),
    "reaper": (
        "the runtime is not an operating-system sandbox",
    ),
    "ventusample": (
        "processing is offline",
        "the tool does not determine rights to source material",
    ),
    "oplague": (
        "analysis is read-only",
        "no driver is installed or modified",
        "heuristic findings are not malware or compatibility verdicts",
    ),
}


class EnvelopeError(ValueError):
    """Raised when report metadata or its result is invalid."""


def _non_empty_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EnvelopeError(f"{label} must be a non-empty string")
    return value.strip()


def _validate_hex(value: str | None, label: str, minimum: int, maximum: int) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        raise EnvelopeError(f"{label} must contain {minimum}–{maximum} hexadecimal characters")
    if any(char not in "0123456789abcdefABCDEF" for char in value):
        raise EnvelopeError(f"{label} must be hexadecimal")
    return value.lower()


def sha256_file(path: str | Path) -> str:
    """Hash a bounded regular file without following symlinks or blocking on pipes."""
    candidate = Path(path)
    descriptor: int | None = None
    digest = hashlib.sha256()
    total_bytes = 0
    try:
        if candidate.is_symlink():
            raise EnvelopeError("hash input must not be a symbolic link")
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(candidate, flags)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise EnvelopeError("hash input must be a regular file")
        if metadata.st_size > MAX_HASH_FILE_BYTES:
            raise EnvelopeError(
                f"hash input exceeds the {MAX_HASH_FILE_BYTES}-byte limit"
            )
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = None
            while chunk := stream.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > MAX_HASH_FILE_BYTES:
                    raise EnvelopeError(
                        f"hash input exceeds the {MAX_HASH_FILE_BYTES}-byte limit"
                    )
                digest.update(chunk)
    except FileNotFoundError as error:
        raise EnvelopeError("hash input does not exist") from error
    except OSError as error:
        raise EnvelopeError(f"cannot safely read hash input: {error}") from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return digest.hexdigest()


def build_envelope(
    *,
    tool: str,
    version: str,
    commit: str | None,
    result: Any,
    limitations: list[str] | tuple[str, ...] | None = None,
    input_kind: str = "none",
    input_sha256: str | None = None,
    created: str | None = None,
    os_name: str | None = None,
    architecture: str | None = None,
) -> dict[str, Any]:
    """Build a validated, JSON-compatible report envelope."""
    try:
        json.dumps(result, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise EnvelopeError("result must contain only finite JSON-compatible values") from error

    tool_name = _non_empty_text(tool, "tool name").lower()
    if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for char in tool_name):
        raise EnvelopeError("tool name may contain only lowercase letters, digits, '-' and '_'")

    version_text = _non_empty_text(version, "tool version")
    commit_hash = _validate_hex(commit, "commit", 7, 64)
    input_hash = _validate_hex(input_sha256, "input SHA-256", 64, 64)
    kind = _non_empty_text(input_kind, "input kind").lower()

    if created is None:
        created = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    else:
        _non_empty_text(created, "created timestamp")
        if not created.endswith("Z"):
            raise EnvelopeError("created timestamp must be an ISO-8601 UTC timestamp ending in 'Z'")
        try:
            parsed_created = datetime.fromisoformat(created[:-1] + "+00:00")
        except ValueError as error:
            raise EnvelopeError(
                "created timestamp must be a valid ISO-8601 UTC timestamp ending in 'Z'"
            ) from error
        if parsed_created.tzinfo is None or parsed_created.utcoffset() != timedelta(0):
            raise EnvelopeError("created timestamp must use the UTC timezone")

    supplied_limitations = list(limitations or [])
    defaults = list(PROJECT_LIMITATIONS.get(tool_name, ()))
    combined: list[str] = []
    for item in defaults + supplied_limitations:
        entry = _non_empty_text(item, "limitation")
        if entry not in combined:
            combined.append(entry)

    return {
        "envelope": "ivan-vhs.report.v1",
        "tool": {
            "name": tool_name,
            "version": version_text,
            "commit": commit_hash,
        },
        "created": created,
        "platform": {
            "os": os_name or platform.system().lower() or "unknown",
            "arch": architecture or platform.machine().lower() or "unknown",
        },
        "input": {
            "kind": kind,
            "sha256": input_hash,
        },
        "result": result,
        "limitations": combined,
    }


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate keys so report consumers see one unambiguous value."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EnvelopeError(f"JSON result contains duplicate object key: {key!r}")
        result[key] = value
    return result


def _reject_non_finite_json_constant(value: str) -> None:
    """Reject NaN and Infinity extensions that are outside strict JSON."""
    raise EnvelopeError(f"JSON result contains non-finite numeric constant: {value}")


def _parse_finite_json_float(value: str) -> float:
    """Reject exponent overflow such as 1e999, which otherwise becomes infinity."""
    parsed = float(value)
    if not math.isfinite(parsed):
        raise EnvelopeError("JSON result contains a non-finite floating-point value")
    return parsed


def _parse_bounded_json_integer(value: str) -> int:
    """Avoid pathological integer tokens consuming excessive CPU and memory."""
    digits = value[1:] if value.startswith("-") else value
    if len(digits) > MAX_JSON_INTEGER_DIGITS:
        raise EnvelopeError(
            f"JSON integer exceeds the {MAX_JSON_INTEGER_DIGITS}-digit limit"
        )
    return int(value)


def _validate_json_nesting(raw: str) -> None:
    """Enforce a portable structural depth limit while ignoring string contents."""
    depth = 0
    in_string = False
    escaped = False
    for character in raw:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > MAX_JSON_NESTING_DEPTH:
                raise EnvelopeError(
                    f"JSON nesting exceeds the {MAX_JSON_NESTING_DEPTH}-level limit"
                )
        elif character in "]}":
            depth -= 1


def _read_result(stream: Any) -> Any:
    """Read UTF-8 text in bounded chunks, enforcing the limit on encoded bytes."""
    chunks: list[str] = []
    total_bytes = 0
    while True:
        remaining = MAX_RESULT_BYTES - total_bytes
        chunk = stream.read(min(64 * 1024, remaining + 1))
        if not chunk:
            break
        if not isinstance(chunk, str):
            raise EnvelopeError("JSON result stream must provide decoded text")
        total_bytes += len(chunk.encode("utf-8"))
        if total_bytes > MAX_RESULT_BYTES:
            raise EnvelopeError(f"JSON result exceeds the {MAX_RESULT_BYTES}-byte limit")
        chunks.append(chunk)
    raw = "".join(chunks)
    _validate_json_nesting(raw)
    try:
        return json.loads(
            raw,
            object_pairs_hook=_unique_json_object,
            parse_constant=_reject_non_finite_json_constant,
            parse_float=_parse_finite_json_float,
            parse_int=_parse_bounded_json_integer,
        )
    except json.JSONDecodeError as error:
        raise EnvelopeError(f"standard input is not valid JSON: {error}") from error
    except RecursionError as error:
        raise EnvelopeError("JSON nesting exceeds the supported parser depth") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Wrap a JSON result in the shared ivan-vhs.report.v1 envelope."
    )
    parser.add_argument("--tool", required=True, help="tool identifier: pytyliki, reaper, ventusample or oplague")
    parser.add_argument("--version", default=os.environ.get("IVAN_VHS_TOOL_VERSION", "unknown"))
    parser.add_argument("--commit", default=os.environ.get("GITHUB_SHA") or os.environ.get("IVAN_VHS_COMMIT"))
    parser.add_argument("--input-kind", default="none", help="kind of the source input; defaults to none")
    parser.add_argument("--input-file", help="optional file whose SHA-256 is recorded; the path is not included")
    parser.add_argument("--limitation", action="append", default=[], help="additional limitation; may be repeated")
    args = parser.parse_args(argv)

    try:
        result = _read_result(sys.stdin)
        input_kind = "file" if args.input_file else args.input_kind
        input_hash = sha256_file(args.input_file) if args.input_file else None
        report = build_envelope(
            tool=args.tool,
            version=args.version,
            commit=args.commit,
            result=result,
            limitations=args.limitation,
            input_kind=input_kind,
            input_sha256=input_hash,
        )
    except (EnvelopeError, OSError) as error:
        print(f"report-envelope: {error}", file=sys.stderr)
        return 2

    json.dump(report, sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
