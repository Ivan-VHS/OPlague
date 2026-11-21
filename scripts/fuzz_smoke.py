#!/usr/bin/env python3
"""Deterministic fuzz-smoke corpus for OPlague INF and UDRV parsing."""
from __future__ import annotations

import random
import tempfile
import zipfile
from pathlib import Path

from oplage_app import parse_inf_text
from tools.udrv_inspector import PackageError, _parse_manifest, inspect_package

def main() -> int:
    rng = random.Random(0x0A11CE26)
    alphabet = b"{}[],:\"'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/\\..\x00\xff"
    handled = 0
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="oplague-fuzz-") as directory:
        root = Path(directory)
        for index in range(384):
            size = rng.randrange(0, 2049)
            raw = bytes(rng.choice(alphabet) for _ in range(size))
            # Exercise the production manifest parser directly with bounded bytes.
            try:
                _parse_manifest(raw)
                handled += 1
            except PackageError:
                rejected += 1

            # INF parser is a read-only text parser: arbitrary decoded text must not crash it.
            parse_inf_text(raw.decode("utf-8", errors="replace"))

            # Every 16th iteration also enters the real package-inspection entry point.
            if index % 16 == 0:
                archive_path = root / f"case-{index}.zip"
                archive_path.write_bytes(raw)
                try:
                    inspect_package(archive_path)
                    handled += 1
                except (PackageError, OSError, zipfile.BadZipFile):
                    rejected += 1

        # A structurally valid ZIP with a traversal member exercises archive path rejection.
        traversal = root / "traversal.zip"
        with zipfile.ZipFile(traversal, "w") as archive:
            archive.writestr("../escape.inf", "[Version]\nClass=Net\n")
        try:
            inspect_package(traversal)
        except (PackageError, ValueError):
            rejected += 1
        else:
            raise AssertionError("traversal archive was unexpectedly accepted")

    print(f"OPlague parser fuzz-smoke: PASS (384 bounded manifest/INF inputs; {handled} accepted; {rejected} rejected safely)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
