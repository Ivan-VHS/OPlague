"""Quantum Contour Syntax (QCS): a small systems-contract parser.

QCS validates contour metadata and records transfer operators. Swift-like
bodies stay opaque: this is not a compiler, code generator, driver or verifier.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA = "oplage.qcs-contour.v1"
MAX_SOURCE_BYTES = 1_048_576

# One grammar, 66 named domain profiles; not 66 compiler implementations.
_ROWS = (
    ("SwiftCore-ASM", "regfile"), ("KernelSwift", "irq"),
    ("BareSwift", "mmio"), ("SliceSwift", "page"),
    ("VoltSwift", "pmu"), ("TrapSwift", "trap"),
    ("RingSwift", "atomic"), ("SlabSwift", "slab"),
    ("BootSwift", "boot"), ("BusSwift", "bus"),
    ("CtxSwift", "contextSwitch"), ("PtrSwift", "pointer"),
    ("ArenaSwift", "arena"), ("BorrowSwift", "borrow"),
    ("CacheSwift", "cache"), ("DmaSwift", "dma"),
    ("PageSwift", "mmu"), ("HeapSwift", "heap"),
    ("PackSwift", "bitfield"), ("RefCountSwift", "refcount"),
    ("ZeroCopySwift", "zeroCopy"), ("GuardSwift", "stackGuard"),
    ("SimdSwift", "simd"), ("LockSwift", "spinlock"),
    ("FenceSwift", "fence"), ("FiberSwift", "fiber"),
    ("PipeSwift", "pipeline"), ("CoreSwift", "affinity"),
    ("TimerSwift", "timer"), ("EventSwift", "event"),
    ("ActorAsmSwift", "actorBox"), ("BatchSwift", "batchIo"),
    ("WatchSwift", "watchdog"), ("CryptoAsmSwift", "crypto"),
    ("EnclaveSwift", "enclave"), ("PermSwift", "privilege"),
    ("HashSwift", "hash"), ("RandSwift", "trng"),
    ("AuditSwift", "trace"), ("SandboxSwift", "sandbox"),
    ("SignSwift", "verify"), ("MemTagSwift", "memTag"),
    ("FaultSwift", "tmr"), ("KeySwift", "secretZeroize"),
    ("GateSwift", "logic"), ("ClockSwift", "clock"),
    ("FpgaSwift", "fpga"), ("DspSwift", "dsp"),
    ("AdcSwift", "adc"), ("PwmSwift", "pwm"),
    ("SpiSwift", "spi"), ("I2cSwift", "i2c"),
    ("UartSwift", "uart"), ("CanSwift", "canFd"),
    ("FsmSwift", "fsm"), ("VmSwift", "vm"),
    ("ByteSwift", "bytecode"), ("JitSwift", "jit"),
    ("IrSwift", "ir"), ("MacroAsmSwift", "macro"),
    ("HyperSwift", "hypervisor"), ("LinkSwift", "linker"),
    ("ElfSwift", "elf64"), ("DbgSwift", "debug"),
    ("ABI Swift", "abi"), ("QcsSwift", "qcsMeta"),
)
DIALECTS = tuple(
    {"index": i, "name": name, "id": re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-"), "domain": domain}
    for i, (name, domain) in enumerate(_ROWS, 1)
)
DOMAIN_TO_DIALECT = {item["domain"]: item for item in DIALECTS}

_HEADER = re.compile(r"^\s*\|~\s*(.*?)\s*~\|\s*$")
_DOMAIN = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*)(?:\((.*)\))?$")
_BUDGET = re.compile(r"^\d+(?:\.\d+)?(?:ns|us|µs|ms|s|cycles)?$", re.I)
_TRANSFER = re.compile(r"->>|<-~")


class QCSSyntaxError(ValueError):
    """A source error with a stable line and column."""

    def __init__(self, message: str, line: int, column: int = 1) -> None:
        self.line, self.column = line, column
        super().__init__(f"line {line}, column {column}: {message}")


def _split_attributes(header: str, line: int) -> list[str]:
    parts, start, depth = [], 0, 0
    quote = None
    escaped = False
    for i, char in enumerate(header):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise QCSSyntaxError("unexpected closing parenthesis", line, i + 1)
        elif char == "," and depth == 0:
            parts.append(header[start:i].strip())
            start = i + 1
    if quote:
        raise QCSSyntaxError("unterminated string in contour header", line, len(header) + 1)
    if depth:
        raise QCSSyntaxError("unclosed parenthesis in contour header", line, len(header) + 1)
    parts.append(header[start:].strip())
    if any(not part for part in parts):
        raise QCSSyntaxError("empty contour attribute", line)
    return parts


def _parse_header(header: str, line: int) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for part in _split_attributes(header, line):
        if ":" not in part:
            raise QCSSyntaxError(f"expected key:value, got {part!r}", line)
        key, value = (item.strip() for item in part.split(":", 1))
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", key):
            raise QCSSyntaxError(f"invalid attribute name {key!r}", line)
        key = key.casefold()
        if key in attrs:
            raise QCSSyntaxError(f"duplicate attribute {key!r}", line)
        if not value:
            raise QCSSyntaxError(f"attribute {key!r} has no value", line)
        attrs[key] = value

    domain = attrs.get("domain", "")
    match = _DOMAIN.fullmatch(domain)
    if not match:
        raise QCSSyntaxError("contour requires a valid domain:<name>", line)
    name = match.group(1)
    if name not in DOMAIN_TO_DIALECT:
        raise QCSSyntaxError(f"unknown domain {name!r}; use one of the 66 QCS domains", line)
    if attrs.get("invariant") not in {"?", "!", "~"}:
        raise QCSSyntaxError("invariant must be one of ?, !, ~", line)
    if "budget" in attrs and not _BUDGET.fullmatch(attrs["budget"]):
        raise QCSSyntaxError("budget must be a duration such as 120ns, 2us, 1ms or 800cycles", line)
    if "arch" in attrs and not re.fullmatch(r"[A-Za-z0-9_.+-]+", attrs["arch"]):
        raise QCSSyntaxError("arch must be a simple architecture identifier", line)
    return attrs


def parse_source(source: str) -> dict[str, Any]:
    """Parse contour wrappers into a JSON-serializable contract AST."""
    if not isinstance(source, str):
        raise TypeError("QCS source must be text")
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError(f"QCS source exceeds the {MAX_SOURCE_BYTES}-byte limit")

    contours, active, body = [], None, []
    transfer_count = 0
    for line_no, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()
        if active is None:
            if line == "|~ end ~|":
                raise QCSSyntaxError("closing marker without an open contour", line_no)
            match = _HEADER.fullmatch(raw)
            if match:
                if match.group(1).strip().casefold() == "end":
                    raise QCSSyntaxError("malformed closing marker", line_no)
                active = {
                    "index": len(contours) + 1,
                    "line": line_no,
                    "attributes": _parse_header(match.group(1), line_no),
                }
                body = []
            elif line and not line.startswith("//"):
                raise QCSSyntaxError("content must be inside a |~ ... ~| contour", line_no)
            continue

        if line == "|~ end ~|":
            text = "\n".join(body).rstrip()
            if not text:
                raise QCSSyntaxError("contour body must not be empty", active["line"])
            transfers = []
            for offset, body_line in enumerate(body):
                for token in _TRANSFER.finditer(body_line):
                    op = token.group(0)
                    transfers.append({
                        "operator": op,
                        "line": active["line"] + offset + 1,
                        "column": token.start() + 1,
                        "kind": "handoff" if op == "->>" else "borrow-release",
                    })
            attrs = active["attributes"]
            domain = attrs["domain"].split("(", 1)[0]
            contours.append({
                **active,
                "end_line": line_no,
                "domain": domain,
                "dialect": DOMAIN_TO_DIALECT[domain]["name"],
                "invariant": attrs["invariant"],
                "body": text,
                "transfers": transfers,
            })
            transfer_count += len(transfers)
            active, body = None, []
            continue

        if _HEADER.fullmatch(raw):
            raise QCSSyntaxError("nested contours are not supported; close the current contour first", line_no)
        body.append(raw)

    if active is not None:
        raise QCSSyntaxError("contour is missing |~ end ~|", active["line"])
    if not contours:
        raise QCSSyntaxError("no QCS contours found", 1)

    domains = list(dict.fromkeys(item["domain"] for item in contours))
    return {
        "schema": SCHEMA,
        "valid": True,
        "contours": contours,
        "summary": {
            "contour_count": len(contours),
            "transfer_count": transfer_count,
            "domains": domains,
            "dialect_count": len({item["dialect"] for item in contours}),
        },
        "limitations": [
            "Swift-like bodies are preserved as text; they are not compiled or executed.",
            "Validation checks declared metadata and transfer-token locations, not hardware behaviour or formal proofs.",
            "A domain profile is a capability label, not a detected device or permission to access it.",
        ],
    }


def render_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        f"QCS validation: PASS ({summary['contour_count']} contour(s))",
        f"Domains: {', '.join(summary['domains'])}",
        f"Explicit transfers: {summary['transfer_count']}",
    ]
    for contour in result["contours"]:
        attrs = contour["attributes"]
        detail = f"{contour['dialect']} · {contour['domain']} · invariant {contour['invariant']}"
        if "arch" in attrs:
            detail += f" · {attrs['arch']}"
        if "budget" in attrs:
            detail += f" · {attrs['budget']}"
        lines.append(f"  {contour['index']:02d}. lines {contour['line']}–{contour['end_line']}: {detail}")
    lines.append("Note: metadata validation only; no compilation, execution or hardware access.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Quantum Contour Syntax (QCS) contracts.")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate", help="validate contour syntax in a .qcs file")
    validate.add_argument("source", help="path to a .qcs file, or - for stdin")
    validate.add_argument("--json", action="store_true", help="print the parsed contract as JSON")
    sub.add_parser("dialects", help="list the 66 domain profiles")
    args = parser.parse_args(argv)

    if args.command == "dialects":
        print("QCS domain profiles (66)")
        for item in DIALECTS:
            print(f"{item['index']:02d}. {item['name']:<16} {item['domain']}")
        return 0
    try:
        source = sys.stdin.read() if args.source == "-" else Path(args.source).read_text(encoding="utf-8")
        result = parse_source(source)
        print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else render_report(result))
        return 0
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        print(f"qcs: FAIL: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
