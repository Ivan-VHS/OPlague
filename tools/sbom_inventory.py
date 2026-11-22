"""Deterministic file-inventory SBOM export for local OPlague evidence.

This is an SPDX 2.3 file inventory, not a dependency resolver or license verdict.
Unknown license information is emitted as NOASSERTION, never guessed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

SCHEMA = "oplague.spdx-inventory.v1"
MAX_FILES = 10_000
MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
IGNORED_DIRECTORIES = {".git", ".venv", "__pycache__", "build", "dist", "node_modules"}


class SBOMError(ValueError):
    """Raised when an inventory cannot be produced within its safety limits."""


def _created_time(created: str | None) -> str:
    if created is None:
        epoch = os.environ.get("SOURCE_DATE_EPOCH", "0")
        try:
            created = datetime.fromtimestamp(int(epoch), timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        except (ValueError, OverflowError, OSError) as error:
            raise SBOMError("SOURCE_DATE_EPOCH must be a valid non-negative Unix timestamp") from error
    if not isinstance(created, str):
        raise SBOMError("created must be ISO-8601 text")
    try:
        value = datetime.fromisoformat(created.replace("Z", "+00:00"))
    except ValueError as error:
        raise SBOMError("created must be an ISO-8601 timestamp") from error
    if value.tzinfo is None:
        raise SBOMError("created timestamp must include a timezone")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _files(root: Path, max_files: int):
    if root.is_symlink() or not root.is_dir():
        raise SBOMError("source root must be a regular directory, not a symlink")
    collected: list[Path] = []
    for folder, dirs, names in os.walk(root, topdown=True, followlinks=False):
        current = Path(folder)
        dirs[:] = sorted(
            name for name in dirs
            if name not in IGNORED_DIRECTORIES and not (current / name).is_symlink()
        )
        for name in sorted(names):
            path = current / name
            if path.is_symlink() or not path.is_file():
                continue
            collected.append(path)
            if len(collected) > max_files:
                raise SBOMError(f"directory contains more than {max_files} files")
    return sorted(collected, key=lambda item: item.relative_to(root).as_posix())


def _file_record(path: Path, root: Path) -> tuple[dict[str, Any], int]:
    try:
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise SBOMError(f"{path.name} exceeds the 512 MiB per-file limit")
        digest = hashlib.sha256()
        read_size = 0
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                read_size += len(chunk)
                if read_size > MAX_FILE_BYTES:
                    raise SBOMError(f"{path.name} changed while being read")
                digest.update(chunk)
    except OSError as error:
        raise SBOMError(f"cannot read {path}: {error}") from error
    relative = path.relative_to(root).as_posix()
    file_id = "SPDXRef-File-" + hashlib.sha256(relative.encode("utf-8")).hexdigest()[:20]
    record = {
        "fileName": "./" + relative,
        "SPDXID": file_id,
        "checksums": [{"algorithm": "SHA256", "checksumValue": digest.hexdigest()}],
        "licenseConcluded": "NOASSERTION",
        "licenseInfoInFiles": ["NOASSERTION"],
        "copyrightText": "NOASSERTION",
    }
    return record, read_size


def build_sbom(root: str | Path, *, created: str | None = None,
               max_files: int = MAX_FILES) -> dict[str, Any]:
    if isinstance(max_files, bool) or not isinstance(max_files, int) or not 1 <= max_files <= MAX_FILES:
        raise SBOMError(f"max_files must be between 1 and {MAX_FILES}")
    source = Path(root).expanduser().resolve(strict=True)
    created_at = _created_time(created)
    paths = _files(source, max_files)
    files = []
    total = 0
    for path in paths:
        record, size = _file_record(path, source)
        total += size
        if total > MAX_TOTAL_BYTES:
            raise SBOMError("source tree exceeds the 2 GiB aggregate limit")
        files.append(record)
    inventory_hash = hashlib.sha256(
        "".join(item["checksums"][0]["checksumValue"] for item in files).encode("ascii")
    ).hexdigest()
    namespace = f"https://spdx.org/spdxdocs/oplague-inventory-{inventory_hash}"
    return {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": source.name or "OPlague file inventory",
        "documentNamespace": namespace,
        "creationInfo": {
            "creators": ["Tool: OPlague-SBOM/0.1.0"],
            "created": created_at,
            "comment": "Local file inventory only; no dependency graph or license conclusions are inferred.",
        },
        "packages": [],
        "files": files,
        "relationships": [
            {"spdxElementId": "SPDXRef-DOCUMENT", "relationshipType": "DESCRIBES",
             "relatedSpdxElement": item["SPDXID"]}
            for item in files
        ],
        "annotations": [],
    }


def write_sbom(report: dict[str, Any], destination: str | Path) -> None:
    path = Path(destination).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n",
                                         dir=path.parent, prefix=f".{path.name}.",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise SBOMError(f"refusing to overwrite existing report: {path}")
        os.link(temporary, path)
        temporary.unlink()
    except OSError as error:
        raise SBOMError(f"cannot write SBOM: {error}") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic SPDX file inventory.")
    parser.add_argument("directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--created", help="Explicit ISO-8601 timestamp; defaults to SOURCE_DATE_EPOCH or Unix epoch.")
    args = parser.parse_args(argv)
    try:
        report = build_sbom(args.directory, created=args.created)
        write_sbom(report, args.output)
        print(f"SPDX inventory written: {args.output} ({len(report['files'])} files)")
        return 0
    except (OSError, SBOMError) as error:
        parser.exit(2, f"SBOM export failed: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
