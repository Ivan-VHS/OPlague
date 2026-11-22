#!/usr/bin/env python3
# Copyright (c) 2026 Ivan-VHS
# SPDX-License-Identifier: Apache-2.0
"""Inspect PE driver candidates without loading, extracting or executing them."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import struct
import sys
from pathlib import Path
from typing import Any, BinaryIO

MAX_FILE_BYTES = 512 * 1024 * 1024
MACHINE_NAMES = {
    0x014C: "x86", 0x8664: "x86_64", 0x01C0: "arm", 0x01C4: "armv7",
    0xAA64: "arm64", 0x0200: "ia64", 0xA641: "arm64ec",
}
SUBSYSTEM_NAMES = {
    1: "native", 2: "windows_gui", 3: "windows_console", 7: "posix_console",
    9: "windows_ce_gui", 10: "efi_application", 11: "efi_boot_service_driver",
    12: "efi_runtime_driver", 13: "efi_rom", 14: "xbox", 16: "windows_boot_application",
}

class PEFormatError(ValueError):
    pass

def _read_at(stream: BinaryIO, offset: int, size: int) -> bytes:
    if offset < 0 or size < 0 or offset > MAX_FILE_BYTES or size > 4096:
        raise PEFormatError("invalid PE header offset or field size")
    stream.seek(offset)
    data = stream.read(size)
    if len(data) != size:
        raise PEFormatError("truncated PE header")
    return data

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()

def inspect_pe(path: str | os.PathLike[str]) -> dict[str, Any]:
    file_path = Path(path)
    size = file_path.stat().st_size
    if size <= 0 or size > MAX_FILE_BYTES:
        raise PEFormatError(f"file size must be between 1 byte and {MAX_FILE_BYTES} bytes")
    with file_path.open("rb") as stream:
        if _read_at(stream, 0, 2) != b"MZ":
            raise PEFormatError("missing DOS MZ signature")
        pe_offset = struct.unpack("<I", _read_at(stream, 0x3C, 4))[0]
        if _read_at(stream, pe_offset, 4) != b"PE\0\0":
            raise PEFormatError("missing PE signature")
        coff = _read_at(stream, pe_offset + 4, 20)
        machine, sections, _timestamp, _symbols, _symbol_count, optional_size, characteristics = struct.unpack("<HHIIIHH", coff)
        if sections > 96:
            raise PEFormatError("section count exceeds the PE specification limit")
        if optional_size < 70 or optional_size > 4096:
            raise PEFormatError("invalid optional-header size")
        optional = _read_at(stream, pe_offset + 24, optional_size)
        magic = struct.unpack_from("<H", optional, 0)[0]
        if magic not in (0x10B, 0x20B):
            raise PEFormatError("unsupported PE optional-header format")
        subsystem = struct.unpack_from("<H", optional, 68)[0]

    is_sys_extension = file_path.suffix.lower() == ".sys"
    native_subsystem = subsystem == 1
    return {
        "path": str(file_path), "size_bytes": size, "sha256": _sha256(file_path),
        "machine": MACHINE_NAMES.get(machine, f"unknown_0x{machine:04x}"),
        "machine_code": f"0x{machine:04x}",
        "subsystem": SUBSYSTEM_NAMES.get(subsystem, f"unknown_{subsystem}"),
        "subsystem_code": subsystem, "section_count": sections,
        "pe32_plus": magic == 0x20B, "is_dll": bool(characteristics & 0x2000),
        "driver_candidate": is_sys_extension or native_subsystem,
        "classification_note": "candidate only; this report does not prove driver role, signature trust or compatibility",
        "signature_status": "not_checked",
    }

def scan_directory(root: str | os.PathLike[str]) -> list[dict[str, Any]]:
    base = Path(root).resolve(strict=True)
    if not base.is_dir():
        raise NotADirectoryError(str(base))
    results: list[dict[str, Any]] = []
    for current, directories, filenames in os.walk(base, followlinks=False):
        directories[:] = sorted(name for name in directories if not (Path(current) / name).is_symlink())
        for name in sorted(filenames):
            candidate = Path(current) / name
            if candidate.is_symlink() or candidate.suffix.lower() not in {".sys", ".dll", ".exe"}:
                continue
            try:
                report = inspect_pe(candidate)
                report["path"] = str(candidate.relative_to(base))
                results.append(report)
            except (OSError, PEFormatError) as exc:
                results.append({"path": str(candidate.relative_to(base)), "error": str(exc), "signature_status": "not_checked"})
    return results

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only PE and driver-candidate inventory")
    parser.add_argument("path", help="PE file or directory to inspect")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)
    target = Path(args.path)
    try:
        reports = [inspect_pe(target)] if target.is_file() else scan_directory(target)
    except (OSError, PEFormatError) as exc:
        print(f"oplague-pe-probe: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            if "error" in report:
                print(f"ERROR {report['path']}: {report['error']}")
            else:
                kind = "candidate" if report["driver_candidate"] else "image"
                print(f"{report['machine']:8} {report['subsystem']:24} {kind:9} {report['path']}")
    return 0 if reports else 1

if __name__ == "__main__":
    raise SystemExit(main())
