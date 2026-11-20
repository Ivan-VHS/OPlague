#!/usr/bin/env python3
"""Read-only validation for UDRV v1 directory and ZIP packages.

The inspector never extracts files, executes payloads, installs drivers, or
contacts external services. It verifies a manifest against the bytes present.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import BinaryIO

FORMAT_NAME = "udrv"
FORMAT_VERSION = 1
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 10_000
MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
READ_CHUNK_BYTES = 1024 * 1024
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class PackageError(ValueError):
    """Raised when a package violates the UDRV container contract."""


@dataclass(frozen=True)
class InspectionReport:
    source: str
    container: str
    package_id: str
    version: str
    files_verified: int
    total_bytes: int
    manifest_sha256: str


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PackageError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _safe_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 1024:
        raise PackageError("payload path must be a non-empty relative path")
    if "\\" in value or value.startswith("/"):
        raise PackageError(f"unsafe payload path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise PackageError(f"unsafe payload path: {value!r}")
    if path.parts[0] != "payload" or len(path.parts) < 2:
        raise PackageError("payload files must be stored below payload/")
    if ":" in path.parts[0] or str(path) != value:
        raise PackageError(f"non-canonical payload path: {value!r}")
    return value


def _parse_manifest(raw: bytes) -> tuple[dict[str, object], dict[str, tuple[int, str]]]:
    if len(raw) > MAX_MANIFEST_BYTES:
        raise PackageError("manifest exceeds the 4 MiB limit")
    try:
        manifest = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PackageError(f"manifest is not valid UTF-8 JSON: {error}") from error
    if not isinstance(manifest, dict):
        raise PackageError("manifest root must be a JSON object")
    if manifest.get("format") != FORMAT_NAME:
        raise PackageError("manifest format must be 'udrv'")
    if type(manifest.get("format_version")) is not int or manifest["format_version"] != FORMAT_VERSION:
        raise PackageError(f"unsupported UDRV format version; expected {FORMAT_VERSION}")

    package_id = manifest.get("id")
    version = manifest.get("version")
    if not isinstance(package_id, str) or not _ID_RE.fullmatch(package_id):
        raise PackageError("manifest id must use 1-128 letters, digits, dots, underscores, or hyphens")
    if not isinstance(version, str) or not version or len(version) > 128 or any(c.isspace() for c in version):
        raise PackageError("manifest version must be a non-empty string without whitespace")

    payload = manifest.get("payload")
    if not isinstance(payload, list) or not payload:
        raise PackageError("manifest payload must be a non-empty array")

    expected: dict[str, tuple[int, str]] = {}
    total = 0
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise PackageError(f"payload entry {index} must be an object")
        relative_path = _safe_relative_path(item.get("path"))
        size = item.get("size")
        digest = item.get("sha256")
        if type(size) is not int or size < 0 or size > MAX_FILE_BYTES:
            raise PackageError(f"payload entry {relative_path!r} has an invalid or excessive size")
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            raise PackageError(f"payload entry {relative_path!r} has an invalid SHA-256 digest")
        folded = relative_path.casefold()
        if any(existing.casefold() == folded for existing in expected):
            raise PackageError(f"duplicate payload path (case-insensitive): {relative_path}")
        expected[relative_path] = (size, digest.lower())
        total += size
        if total > MAX_TOTAL_BYTES:
            raise PackageError("declared payload exceeds the 2 GiB package limit")
    return manifest, expected


def _digest_stream(stream: BinaryIO, expected_size: int, name: str) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    while True:
        chunk = stream.read(READ_CHUNK_BYTES)
        if not chunk:
            break
        size += len(chunk)
        if size > MAX_FILE_BYTES or size > expected_size:
            raise PackageError(f"payload size exceeds the manifest for {name!r}")
        digest.update(chunk)
    if size != expected_size:
        raise PackageError(f"payload size mismatch for {name!r}: expected {expected_size}, got {size}")
    return size, digest.hexdigest()


def _validate_directory(root: Path) -> tuple[bytes, dict[str, Path]]:
    manifest_path = root / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise PackageError("directory package must contain a regular manifest.json")
    # Read at most the configured limit plus one byte. Checking only after
    # read_bytes() would allow an oversized manifest to consume unbounded RAM.
    with manifest_path.open("rb") as stream:
        raw = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(raw) > MAX_MANIFEST_BYTES:
        raise PackageError("manifest exceeds the 4 MiB limit")
    files: dict[str, Path] = {}
    for current, directories, filenames in os.walk(root, followlinks=False):
        base = Path(current)
        for directory in directories:
            child = base / directory
            if child.is_symlink():
                raise PackageError(f"symbolic links are not allowed: {child.relative_to(root)}")
        for filename in filenames:
            child = base / filename
            if child.is_symlink():
                raise PackageError(f"symbolic links are not allowed: {child.relative_to(root)}")
            if child == manifest_path:
                continue
            mode = child.stat(follow_symlinks=False).st_mode
            if not stat.S_ISREG(mode):
                raise PackageError(f"non-regular package entry is not allowed: {child.relative_to(root)}")
            relative = child.relative_to(root).as_posix()
            _safe_relative_path(relative)
            files[relative] = child
            if len(files) > MAX_ARCHIVE_ENTRIES:
                raise PackageError("package contains too many entries")
    return raw, files


def _zip_entry_path(name: str, is_directory: bool) -> str:
    value = name[:-1] if is_directory and name.endswith("/") else name
    if not value or "\\" in value or value.startswith("/"):
        raise PackageError(f"unsafe archive entry path: {name!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise PackageError(f"unsafe archive entry path: {name!r}")
    if ":" in path.parts[0]:
        raise PackageError(f"unsafe archive entry path: {name!r}")
    return value


def _validate_zip(archive_path: Path) -> tuple[bytes, dict[str, zipfile.ZipInfo], zipfile.ZipFile]:
    archive = zipfile.ZipFile(archive_path, "r")
    infos = archive.infolist()
    if len(infos) > MAX_ARCHIVE_ENTRIES:
        archive.close()
        raise PackageError("archive contains too many entries")

    manifest_info: zipfile.ZipInfo | None = None
    files: dict[str, zipfile.ZipInfo] = {}
    seen: set[str] = set()
    total_declared = 0
    for info in infos:
        is_directory = info.is_dir()
        relative = _zip_entry_path(info.filename, is_directory)
        folded = relative.casefold()
        if folded in seen:
            archive.close()
            raise PackageError(f"duplicate archive entry (case-insensitive): {relative}")
        seen.add(folded)
        mode = (info.external_attr >> 16) & 0xFFFF
        file_type = stat.S_IFMT(mode)
        if file_type == stat.S_IFLNK or (file_type not in (0, stat.S_IFREG, stat.S_IFDIR)):
            archive.close()
            raise PackageError(f"non-regular archive entry is not allowed: {relative}")
        if info.flag_bits & 0x1:
            archive.close()
            raise PackageError(f"encrypted archive entry is not supported: {relative}")
        if is_directory:
            continue
        if relative == "manifest.json":
            manifest_info = info
            if info.file_size > MAX_MANIFEST_BYTES:
                archive.close()
                raise PackageError("manifest exceeds the 4 MiB limit")
            continue
        _safe_relative_path(relative)
        if info.file_size > MAX_FILE_BYTES:
            archive.close()
            raise PackageError(f"archive entry exceeds the per-file limit: {relative}")
        total_declared += info.file_size
        if total_declared > MAX_TOTAL_BYTES:
            archive.close()
            raise PackageError("archive payload exceeds the 2 GiB limit")
        files[relative] = info

    if manifest_info is None:
        archive.close()
        raise PackageError("archive package must contain a root manifest.json")
    try:
        raw = archive.read(manifest_info)
    except (OSError, RuntimeError, zipfile.BadZipFile) as error:
        archive.close()
        raise PackageError(f"cannot read manifest.json: {error}") from error
    return raw, files, archive


def inspect_package(source: str | os.PathLike[str]) -> InspectionReport:
    """Validate a UDRV v1 directory or ZIP package without extracting it."""
    path = Path(source)
    if not path.exists():
        raise PackageError(f"package does not exist: {path}")
    if path.is_symlink():
        raise PackageError("the package root cannot be a symbolic link")

    archive: zipfile.ZipFile | None = None
    if path.is_dir():
        raw_manifest, actual_files = _validate_directory(path)
        container = "directory"
        open_file = lambda name: actual_files[name].open("rb")
        source_name = path.name or "."
    elif path.is_file() and zipfile.is_zipfile(path):
        raw_manifest, zip_files, archive = _validate_zip(path)
        actual_files = {}
        container = "zip"
        open_file = lambda name: archive.open(zip_files[name], "r")  # type: ignore[union-attr]
        source_name = path.name
    else:
        raise PackageError("package must be a directory or a ZIP archive")

    try:
        manifest, expected_files = _parse_manifest(raw_manifest)
        expected_names = set(expected_files)
        actual_names = set(actual_files) if container == "directory" else set(zip_files)
        missing = sorted(expected_names - actual_names)
        undeclared = sorted(actual_names - expected_names)
        if missing:
            raise PackageError(f"manifest references missing payload files: {', '.join(missing[:5])}")
        if undeclared:
            raise PackageError(f"package contains undeclared files: {', '.join(undeclared[:5])}")

        total_bytes = 0
        for name, (expected_size, expected_digest) in expected_files.items():
            try:
                with open_file(name) as stream:
                    size, actual_digest = _digest_stream(stream, expected_size, name)
            except (OSError, RuntimeError, zipfile.BadZipFile) as error:
                raise PackageError(f"cannot read payload {name!r}: {error}") from error
            if actual_digest != expected_digest:
                raise PackageError(f"SHA-256 mismatch for payload {name!r}")
            total_bytes += size

        return InspectionReport(
            source=source_name,
            container=container,
            package_id=str(manifest["id"]),
            version=str(manifest["version"]),
            files_verified=len(expected_files),
            total_bytes=total_bytes,
            manifest_sha256=hashlib.sha256(raw_manifest).hexdigest(),
        )
    finally:
        if archive is not None:
            archive.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read-only UDRV v1 manifest, payload-size and SHA-256 inspector."
    )
    parser.add_argument("package", help="UDRV package directory or ZIP archive")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = inspect_package(args.package)
    except (PackageError, OSError, zipfile.BadZipFile) as error:
        print(f"UDRV INVALID: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    else:
        print(
            f"UDRV VALID | {report.package_id}@{report.version} | "
            f"{report.files_verified} file(s) | {report.total_bytes} bytes | "
            f"{report.container} | manifest sha256={report.manifest_sha256}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
