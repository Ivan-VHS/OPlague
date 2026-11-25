"""Export one read-only OPlague GPU telemetry snapshot for DuckOS/Reaper."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.game_optimizer import create_gpu_telemetry_snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export an OPlague GPU telemetry snapshot.")
    parser.add_argument("--output", required=True, type=Path, help="destination JSON file")
    args = parser.parse_args(argv)

    snapshot = create_gpu_telemetry_snapshot(output_path=args.output)
    print(json.dumps({
        "schema": snapshot["schema"],
        "available": snapshot["available"],
        "gpu_count": len(snapshot["gpus"]),
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "output": snapshot["snapshot_path"],
        "controls_performed": snapshot["controls_performed"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
