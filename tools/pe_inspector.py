"""Read-only PE/COFF header inspection for local driver and application files.

The parser reads headers and section metadata only. It never loads or executes
the inspected image and does not treat a certificate directory as a trust verdict.
"""
from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path
from typing import Any

SCHEMA = "oplague.pe-inspection.v1"
MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024
MAX_PE_HEADER_OFFSET = 1024 * 1024
MAX_SECTIONS = 96
MAX_OPTIONAL_HEADER = 4096
_MACHINE = {
    0x014C: "x86", 0x8664: "x64", 0x01C0: "ARM",
    0x01C4: "ARMv7", 0xAA64: "ARM64", 0xA641: "ARM64EC",
}


class PEFormatError(ValueError):
    """Raised when an input is not a supported, bounded PE image."""


def _unpack(fmt: str, data: bytes, offset: int, label: str):
    size = struct.calcsize(fmt)
    if offset < 0 or offset + size > len(data):
        raise PEFormatError(f"{label} extends beyond the available PE header")
    return struct.unpack_from(fmt, data, offset)


def inspect_pe_bytes(data: bytes, *, file_size: int | None = None) -> dict[str, Any]:
    if not isinstance(data, bytes):
        raise TypeError("PE input must be bytes")
    actual_size = len(data) if file_size is None else file_size
    if isinstance(actual_size, bool) or not isinstance(actual_size, int) or actual_size < len(data):
        raise PEFormatError("file_size must be an integer at least as large as the supplied header")
    if actual_size > MAX_FILE_BYTES:
        raise PEFormatError("PE file exceeds the 2 GiB inspection limit")
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise PEFormatError("missing DOS MZ header")
    pe_offset = _unpack("<I", data, 0x3C, "e_lfanew")[0]
    if pe_offset < 0x40 or pe_offset > MAX_PE_HEADER_OFFSET:
        raise PEFormatError("PE header offset is outside the supported range")
    if pe_offset + 24 > len(data) or data[pe_offset:pe_offset + 4] != b"PE\0\0":
        raise PEFormatError("missing PE signature or truncated COFF header")

    machine, section_count, timestamp, _, _, optional_size, characteristics = _unpack(
        "<HHIIIHH", data, pe_offset + 4, "COFF header"
    )
    if section_count > MAX_SECTIONS:
        raise PEFormatError(f"section count exceeds the {MAX_SECTIONS}-section limit")
    if optional_size > MAX_OPTIONAL_HEADER:
        raise PEFormatError("optional header exceeds the supported 4096-byte limit")
    optional_offset = pe_offset + 24
    section_table = optional_offset + optional_size
    if section_table > len(data):
        raise PEFormatError("optional header extends beyond the available header bytes")
    optional = data[optional_offset:section_table]
    magic = _unpack("<H", optional, 0, "optional-header magic")[0]
    if magic == 0x10B:
        pe_kind, image_base_fmt, image_base_offset, directory_count_offset, directories_offset = (
            "PE32", "<I", 28, 92, 96
        )
    elif magic == 0x20B:
        pe_kind, image_base_fmt, image_base_offset, directory_count_offset, directories_offset = (
            "PE32+", "<Q", 24, 108, 112
        )
    else:
        raise PEFormatError(f"unsupported optional-header magic 0x{magic:04X}")
    if len(optional) < directories_offset:
        raise PEFormatError("optional header is too short for its standard fields")

    entry_point = _unpack("<I", optional, 16, "AddressOfEntryPoint")[0]
    image_base = _unpack(image_base_fmt, optional, image_base_offset, "ImageBase")[0]
    section_alignment = _unpack("<I", optional, 32, "SectionAlignment")[0]
    file_alignment = _unpack("<I", optional, 36, "FileAlignment")[0]
    subsystem = _unpack("<H", optional, 68, "Subsystem")[0]
    directory_count = min(_unpack("<I", optional, directory_count_offset, "NumberOfRvaAndSizes")[0], 16)
    if directories_offset + directory_count * 8 > len(optional):
        raise PEFormatError("data-directory table is truncated")
    directories = []
    for index in range(directory_count):
        address, size = _unpack("<II", optional, directories_offset + index * 8, "data directory")
        directories.append({"index": index, "address": address, "size": size})

    sections = []
    section_end = section_table + section_count * 40
    if section_end > len(data):
        raise PEFormatError("section table extends beyond the available header bytes")
    for index in range(section_count):
        offset = section_table + index * 40
        raw_name = data[offset:offset + 8].split(b"\0", 1)[0]
        name = raw_name.decode("ascii", errors="replace")
        virtual_size, virtual_address, raw_size, raw_pointer = _unpack(
            "<IIII", data, offset + 8, "section dimensions"
        )
        section_characteristics = _unpack("<I", data, offset + 36, "section characteristics")[0]
        if raw_size and (raw_pointer > actual_size or raw_size > actual_size - raw_pointer):
            raise PEFormatError(f"section {name!r} raw data extends beyond the file")
        sections.append({
            "name": name, "virtual_size": virtual_size, "virtual_address": virtual_address,
            "raw_size": raw_size, "raw_pointer": raw_pointer,
            "characteristics": section_characteristics,
        })

    certificate = next((item for item in directories if item["index"] == 4), None)
    certificate_valid_bounds = None
    if certificate and certificate["address"] and certificate["size"]:
        start, size = certificate["address"], certificate["size"]
        certificate_valid_bounds = start <= actual_size and size <= actual_size - start

    return {
        "schema": SCHEMA,
        "file_size": actual_size,
        "format": pe_kind,
        "machine": _MACHINE.get(machine, f"unknown-0x{machine:04X}"),
        "machine_code": machine,
        "section_count": section_count,
        "timestamp_unix": timestamp,
        "characteristics": characteristics,
        "entry_point_rva": entry_point,
        "image_base": image_base,
        "section_alignment": section_alignment,
        "file_alignment": file_alignment,
        "subsystem_code": subsystem,
        "data_directories": directories,
        "certificate_table": {
            "present": bool(certificate and certificate["address"] and certificate["size"]),
            "file_range_valid": certificate_valid_bounds,
            "verified": False,
        },
        "sections": sections,
        "execution_performed": False,
        "signature_verdict": "not-checked",
    }


def inspect_pe(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser()
    if source.is_symlink() or not source.is_file():
        raise PEFormatError("input must be a regular, non-symlink file")
    size = source.stat().st_size
    if size > MAX_FILE_BYTES:
        raise PEFormatError("PE file exceeds the 2 GiB inspection limit")
    with source.open("rb") as stream:
        prefix = stream.read(0x40)
        if len(prefix) < 0x40 or prefix[:2] != b"MZ":
            raise PEFormatError("missing DOS MZ header")
        pe_offset = struct.unpack_from("<I", prefix, 0x3C)[0]
        if pe_offset < 0x40 or pe_offset > MAX_PE_HEADER_OFFSET:
            raise PEFormatError("PE header offset is outside the supported range")
        stream.seek(0)
        header = stream.read(min(size, pe_offset + 24 + MAX_OPTIONAL_HEADER + MAX_SECTIONS * 40))
    return inspect_pe_bytes(header, file_size=size)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect PE/COFF headers without executing the file.")
    parser.add_argument("file", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = inspect_pe(args.file)
        output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8", newline="\n")
        else:
            print(output, end="")
        return 0
    except (OSError, PEFormatError) as error:
        parser.exit(2, f"PE inspection failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
