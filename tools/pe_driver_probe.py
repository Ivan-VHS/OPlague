#!/usr/bin/env python3
# Copyright (c) 2026 Ivan-VHS
# SPDX-License-Identifier: Apache-2.0
"""OPlague PE Workbench: bounded, read-only executable and driver-package auditing."""
from __future__ import annotations
import argparse, hashlib, json, math, os, struct, sys
from collections import defaultdict
from pathlib import Path
from typing import Any, BinaryIO

MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_FILES = 50_000
ENTROPY_SAMPLE_BYTES = 1024 * 1024
MACHINE_NAMES = {
    0x014C: "x86", 0x8664: "x86_64", 0x01C0: "arm", 0x01C4: "armv7",
    0xAA64: "arm64", 0x0200: "ia64", 0xA641: "arm64ec",
}
SUBSYSTEM_NAMES = {
    1: "native", 2: "windows_gui", 3: "windows_console", 7: "posix_console",
    9: "windows_ce_gui", 10: "efi_application", 11: "efi_boot_service_driver",
    12: "efi_runtime_driver", 13: "efi_rom", 14: "xbox", 16: "windows_boot_application",
}
IMAGE_FILE_MACHINE_UNKNOWN = 0
IMAGE_FILE_DLL = 0x2000
IMAGE_FILE_EXECUTABLE_IMAGE = 0x0002

class PEFormatError(ValueError):
    """A malformed or unsupported Portable Executable header."""

def _read_at(stream: BinaryIO, offset: int, size: int, file_size: int) -> bytes:
    if offset < 0 or size < 0 or size > 4096 or offset + size > file_size:
        raise PEFormatError("PE header field falls outside the file")
    stream.seek(offset)
    data = stream.read(size)
    if len(data) != size:
        raise PEFormatError("truncated PE header")
    return data

def _entropy(stream: BinaryIO, offset: int, size: int) -> float | None:
    sample_size = min(size, ENTROPY_SAMPLE_BYTES)
    if sample_size <= 0:
        return None
    stream.seek(offset)
    data = stream.read(sample_size)
    if len(data) != sample_size:
        return None
    frequencies = [0] * 256
    for value in data:
        frequencies[value] += 1
    entropy = 0.0
    for count in frequencies:
        if count:
            probability = count / sample_size
            entropy -= probability * math.log2(probability)
    return round(entropy, 3)

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()

def inspect_pe(path: str | os.PathLike[str]) -> dict[str, Any]:
    file_path = Path(path)
    file_size = file_path.stat().st_size
    if file_size <= 0 or file_size > MAX_FILE_BYTES:
        raise PEFormatError(f"file size must be between 1 byte and {MAX_FILE_BYTES} bytes")
    warnings: list[str] = []
    sections_info: list[dict[str, Any]] = []

    with file_path.open("rb") as stream:
        if _read_at(stream, 0, 2, file_size) != b"MZ":
            raise PEFormatError("missing DOS MZ signature")
        pe_offset = struct.unpack("<I", _read_at(stream, 0x3C, 4, file_size))[0]
        if pe_offset < 64:
            raise PEFormatError("PE header offset overlaps the DOS header")
        if _read_at(stream, pe_offset, 4, file_size) != b"PE\0\0":
            raise PEFormatError("missing PE signature")
        coff = _read_at(stream, pe_offset + 4, 20, file_size)
        machine, section_count, timestamp, _symbols, _symbol_count, optional_size, characteristics = struct.unpack(
            "<HHIIIHH", coff
        )
        if machine == IMAGE_FILE_MACHINE_UNKNOWN:
            warnings.append("unknown_machine_type")
        if section_count > 96:
            raise PEFormatError("section count exceeds the PE specification limit")
        if optional_size < 70 or optional_size > 4096:
            raise PEFormatError("invalid optional-header size")
        optional_offset = pe_offset + 24
        optional = _read_at(stream, optional_offset, optional_size, file_size)
        magic = struct.unpack_from("<H", optional, 0)[0]
        if magic == 0x10B:
            directory_count_offset, directory_table_offset = 92, 96
            pe_format = "PE32"
        elif magic == 0x20B:
            directory_count_offset, directory_table_offset = 108, 112
            pe_format = "PE32+"
        else:
            raise PEFormatError("unsupported PE optional-header format")
        subsystem = struct.unpack_from("<H", optional, 68)[0]
        certificate_offset = certificate_size = 0
        if optional_size >= directory_count_offset + 4:
            directory_count = struct.unpack_from("<I", optional, directory_count_offset)[0]
            if directory_count > 4 and optional_size >= directory_table_offset + (5 * 8):
                certificate_offset, certificate_size = struct.unpack_from(
                    "<II", optional, directory_table_offset + (4 * 8)
                )
        certificate_present = certificate_offset > 0 and certificate_size > 0
        certificate_bounds_valid = (
            certificate_present and certificate_offset + certificate_size <= file_size
        ) if certificate_present else None
        if certificate_present and not certificate_bounds_valid:
            warnings.append("certificate_table_out_of_file_bounds")
        elif not certificate_present:
            warnings.append("no_authenticode_certificate_table")

        section_table_offset = optional_offset + optional_size
        if section_table_offset + section_count * 40 > file_size:
            raise PEFormatError("section table extends beyond the file")
        for index in range(section_count):
            raw = _read_at(stream, section_table_offset + index * 40, 40, file_size)
            name = raw[:8].split(b"\0", 1)[0].decode("ascii", errors="replace")
            virtual_size, virtual_address, raw_size, raw_offset = struct.unpack_from("<IIII", raw, 8)
            section_flags = struct.unpack_from("<I", raw, 36)[0]
            raw_valid = raw_size == 0 or (raw_offset > 0 and raw_offset + raw_size <= file_size)
            section_entropy = None
            if raw_size and raw_valid:
                section_entropy = _entropy(stream, raw_offset, raw_size)
            elif raw_size and not raw_valid:
                warnings.append(f"section_{index + 1}_raw_range_out_of_bounds")
            if section_entropy is not None and section_entropy >= 7.2:
                warnings.append(f"section_{index + 1}_high_entropy_review")
            sections_info.append({
                "index": index + 1, "name": name, "virtual_size": virtual_size,
                "virtual_address": f"0x{virtual_address:08x}", "raw_size": raw_size,
                "raw_offset": raw_offset, "raw_range_valid": raw_valid,
                "entropy_sample_bits_per_byte": section_entropy,
                "executable": bool(section_flags & 0x20000000),
                "writable": bool(section_flags & 0x80000000),
            })

    suffix = file_path.suffix.lower()
    reasons = []
    if suffix == ".sys":
        reasons.append("sys_extension")
    if subsystem == 1:
        reasons.append("native_subsystem")
    driver_candidate = bool(reasons)
    return {
        "path": str(file_path), "size_bytes": file_size, "sha256": _sha256(file_path),
        "machine": MACHINE_NAMES.get(machine, f"unknown_0x{machine:04x}"),
        "machine_code": f"0x{machine:04x}",
        "subsystem": SUBSYSTEM_NAMES.get(subsystem, f"unknown_{subsystem}"),
        "subsystem_code": subsystem, "pe_format": pe_format, "section_count": section_count,
        "sections": sections_info, "timestamp": timestamp,
        "is_dll": bool(characteristics & IMAGE_FILE_DLL),
        "is_executable_image": bool(characteristics & IMAGE_FILE_EXECUTABLE_IMAGE),
        "driver_candidate": driver_candidate, "candidate_reasons": reasons,
        "authenticode": {
            "certificate_table_present": certificate_present,
            "certificate_table_bounds_valid": certificate_bounds_valid,
            "certificate_table_offset": certificate_offset,
            "certificate_table_size": certificate_size,
            "trust": "not_verified",
        },
        "warnings": warnings,
        "classification_note": "candidate classification is heuristic; signature trust and device compatibility are not established",
    }

def scan_directory(root: str | os.PathLike[str], max_files: int = 5000) -> list[dict[str, Any]]:
    if not 1 <= max_files <= MAX_FILES:
        raise ValueError(f"max_files must be between 1 and {MAX_FILES}")
    base = Path(root).resolve(strict=True)
    if not base.is_dir():
        raise NotADirectoryError(str(base))
    results: list[dict[str, Any]] = []
    scanned = 0
    truncated = False
    for current, directories, filenames in os.walk(base, followlinks=False):
        directories[:] = sorted(name for name in directories if not (Path(current) / name).is_symlink())
        for name in sorted(filenames):
            candidate = Path(current) / name
            if candidate.is_symlink() or candidate.suffix.lower() not in {".sys", ".dll", ".exe"}:
                continue
            if scanned >= max_files:
                truncated = True
                break
            scanned += 1
            try:
                report = inspect_pe(candidate)
                report["path"] = str(candidate.relative_to(base))
                results.append(report)
            except (OSError, PEFormatError) as exc:
                results.append({"path": str(candidate.relative_to(base)), "error": str(exc), "warnings": []})
        if truncated:
            break
    if truncated:
        results.append({"scan_warning": "max_file_limit_reached", "max_files": max_files})
    return results

def build_inventory_report(records: list[dict[str, Any]], target: str) -> dict[str, Any]:
    valid = [record for record in records if "sha256" in record]
    hashes: dict[str, list[str]] = defaultdict(list)
    architectures: dict[str, int] = {}
    for record in valid:
        hashes[record["sha256"]].append(record["path"])
        arch = record["machine"]
        architectures[arch] = architectures.get(arch, 0) + 1
    duplicates = [{"sha256": digest, "paths": sorted(paths)}
                  for digest, paths in sorted(hashes.items()) if len(paths) > 1]
    return {
        "schema": "oplague.pe-inventory.v1", "target": target,
        "summary": {
            "records": len(records), "valid_pe_files": len(valid),
            "driver_candidates": sum(bool(item["driver_candidate"]) for item in valid),
            "parse_errors": sum("error" in item for item in records),
            "warning_count": sum(len(item.get("warnings", [])) for item in records),
            "duplicate_groups": len(duplicates),
            "scan_truncated": any(item.get("scan_warning") for item in records),
        },
        "architectures": dict(sorted(architectures.items())),
        "duplicates": duplicates, "records": records,
        "trust_boundary": {
            "signature_verification": "not_performed",
            "driver_installation": "not_performed",
            "payload_execution": "not_performed",
            "compatibility_verdict": "not_performed",
        },
    }

def render_table(report: dict[str, Any]) -> str:
    lines = ["ARCH     SUBSYSTEM                TYPE       PATH", "-" * 78]
    for item in report["records"]:
        if "scan_warning" in item:
            lines.append(f"WARNING: {item['scan_warning']} ({item['max_files']})")
        elif "error" in item:
            lines.append(f"ERROR    {item['path']}: {item['error']}")
        else:
            kind = "candidate" if item["driver_candidate"] else "image"
            lines.append(f"{item['machine']:8} {item['subsystem']:24} {kind:10} {item['path']}")
            for warning in item["warnings"]:
                lines.append(f"  ! {warning}")
    summary = report["summary"]
    lines.extend(["", f"{summary['valid_pe_files']} valid PE · {summary['driver_candidates']} candidates · "
                  f"{summary['parse_errors']} errors · {summary['duplicate_groups']} duplicate groups"])
    return "\n".join(lines)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only PE and driver-package inventory")
    parser.add_argument("path", help="PE file or directory to inspect")
    parser.add_argument("--format", choices=("table", "json", "markdown"), default="table")
    parser.add_argument("--json", action="store_true", help="compatibility alias for --format json")
    parser.add_argument("--max-files", type=int, default=5000, help=f"directory scan ceiling (1–{MAX_FILES})")
    parser.add_argument("--output", help="write the selected report to a file")
    parser.add_argument("--strict", action="store_true", help="return exit code 1 when any file failed inspection")
    args = parser.parse_args(argv)
    target = Path(args.path)
    try:
        records = [inspect_pe(target)] if target.is_file() else scan_directory(target, args.max_files)
    except (OSError, PEFormatError, ValueError) as exc:
        print(f"oplague-pe-probe: {exc}", file=sys.stderr)
        return 2
    report = build_inventory_report(records, str(target))
    output_format = "json" if args.json else args.format
    if output_format == "json":
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    elif output_format == "markdown":
        summary = report["summary"]
        lines = ["# OPlague PE Inventory", "", f"Target: {target}", "",
                 f"Valid files: {summary['valid_pe_files']} · candidates: {summary['driver_candidates']} · "
                 f"parse errors: {summary['parse_errors']}", "",
                 "| File | Architecture | Subsystem | Candidate | Warnings |",
                 "|---|---|---|---:|---:|"]
        for item in records:
            if "sha256" in item:
                lines.append(f"| {item['path']} | {item['machine']} | {item['subsystem']} | "
                             f"{'yes' if item['driver_candidate'] else 'no'} | {len(item['warnings'])} |")
        rendered = "\n".join(lines) + "\n"
    else:
        rendered = render_table(report) + "\n"
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    errors = report["summary"]["parse_errors"]
    return 1 if args.strict and errors else 0

if __name__ == "__main__":
    raise SystemExit(main())
