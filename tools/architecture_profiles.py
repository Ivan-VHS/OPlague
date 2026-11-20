"""Read-only Windows driver target architecture classification.

The module compares explicit INF architecture decorations. It does not prove that a
driver is signed, installable, ABI-safe, or functional on a particular device.
"""
from __future__ import annotations

import argparse
import json
import platform
import re
from dataclasses import asdict, dataclass
from typing import Sequence


@dataclass(frozen=True, slots=True)
class TargetArchitecture:
    key: str
    inf_decoration: str
    pe_machine: str
    pointer_bits: int
    description: str


TARGETS: tuple[TargetArchitecture, ...] = (
    TargetArchitecture("x86", "NTx86", "0x014C (IMAGE_FILE_MACHINE_I386)", 32, "32-bit Intel-compatible Windows target"),
    TargetArchitecture("amd64", "NTamd64", "0x8664 (IMAGE_FILE_MACHINE_AMD64)", 64, "64-bit x86 Windows target"),
    TargetArchitecture("arm", "NTarm", "0x01C4 (IMAGE_FILE_MACHINE_ARMNT)", 32, "32-bit ARM Windows target"),
    TargetArchitecture("arm64", "NTarm64", "0xAA64 (IMAGE_FILE_MACHINE_ARM64)", 64, "64-bit ARM Windows target"),
    TargetArchitecture("ia64", "NTia64", "0x0200 (IMAGE_FILE_MACHINE_IA64)", 64, "Legacy Itanium Windows target"),
)

_ALIASES = {
    "x86": "x86", "i386": "x86", "i486": "x86", "i586": "x86", "i686": "x86", "win32": "x86",
    "amd64": "amd64", "x64": "amd64", "x86_64": "amd64", "x86-64": "amd64",
    "arm": "arm", "armv7": "arm", "armv7l": "arm", "arm32": "arm",
    "arm64": "arm64", "aarch64": "arm64", "armv8": "arm64",
    "ia64": "ia64", "itanium": "ia64",
}
_INF_TOKEN = re.compile(r"(?i)\bNT(x86|amd64|arm64|arm|ia64)(?=[.\],\s]|$)")


def normalize_architecture(value: str) -> str | None:
    """Map a known host/target spelling to the canonical Windows architecture key."""
    if not isinstance(value, str):
        raise TypeError("architecture must be a string")
    if len(value) > 64:
        raise ValueError("architecture name is too long")
    return _ALIASES.get(value.strip().casefold())


def detect_inf_target_architectures(inf_text: str) -> list[str]:
    """Return unique architecture decorations explicitly present in INF text."""
    if not isinstance(inf_text, str):
        raise TypeError("INF content must be text")
    if len(inf_text) > 8 * 1024 * 1024:
        raise ValueError("INF text exceeds the 8 MiB parsing limit")
    found: set[str] = set()
    for match in _INF_TOKEN.finditer(inf_text):
        canonical = normalize_architecture(match.group(1))
        if canonical:
            found.add(canonical)
    return sorted(found)


def evaluate_driver_targets(host_architecture: str, declared_targets: Sequence[str]) -> dict[str, object]:
    """Compare one host architecture to explicit INF targets without guessing."""
    host = normalize_architecture(host_architecture)
    if not isinstance(declared_targets, (list, tuple)):
        raise TypeError("declared_targets must be a list or tuple of architecture names")
    if len(declared_targets) > 64:
        raise ValueError("declared_targets exceeds the 64-entry limit")

    normalized: set[str] = set()
    unrecognized: list[str] = []
    for value in declared_targets:
        if not isinstance(value, str) or not value.strip() or len(value) > 64:
            raise ValueError("each declared target must be a non-empty string of at most 64 characters")
        candidate = normalize_architecture(value)
        if candidate is None:
            unrecognized.append(value)
        else:
            normalized.add(candidate)

    if host is None or not normalized:
        verdict = "unknown"
        evidence = "A known host architecture and at least one recognized INF target are required."
    elif host in normalized:
        verdict = "explicit_match"
        evidence = "The INF text explicitly declares the host architecture."
    else:
        verdict = "explicit_nonmatch"
        evidence = "The INF text declares other recognized architectures but not the host architecture."

    return {
        "schema": "oplage.driver-target-analysis.v1",
        "host_architecture": host_architecture,
        "normalized_host": host,
        "declared_architectures": sorted(normalized),
        "unrecognized_declarations": sorted(set(unrecognized), key=str.casefold),
        "verdict": verdict,
        "evidence": evidence,
        "limitations": [
            "An explicit architecture match is not proof of driver signing, OS-version support, device-ID match, or successful installation.",
            "An explicit non-match may coexist with undecorated or generic INF install sections; inspect the full INF before rejecting a package.",
            "No package code is loaded, extracted, installed, or executed."
        ],
    }


def current_host_architecture() -> str | None:
    """Best-effort normalized host label from Python's platform.machine()."""
    return normalize_architecture(platform.machine())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only INF driver target architecture analysis.")
    parser.add_argument("--list", action="store_true", help="list known Windows INF target profiles")
    parser.add_argument("--host", default=platform.machine(), help="host architecture (for example amd64 or arm64)")
    parser.add_argument("--targets", default="", help="comma-separated declared INF targets")
    parser.add_argument("--inf", help="optional INF path to scan for decorated target architectures")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list:
        payload = {"schema": "oplage.windows-target-architectures.v1", "targets": [asdict(item) for item in TARGETS]}
    else:
        declared = [item.strip() for item in args.targets.split(",") if item.strip()]
        if args.inf:
            from pathlib import Path
            declared.extend(detect_inf_target_architectures(Path(args.inf).read_text(encoding="utf-8-sig", errors="replace")))
        payload = evaluate_driver_targets(args.host, declared)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
