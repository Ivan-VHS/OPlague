from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.federation import build_device_snapshot  # noqa: E402

OUTPUT = ROOT / "build" / "reaper-fixtures"
KEY = b"reaper-language-fixture-key-2026-11"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    baseline_devices = [
        {
            "InstanceId": r"PCI\VEN_1234&DEV_5678\SYNTH-GPU-A",
            "FriendlyName": "Synthetic GPU A",
            "Class": "Display",
            "Status": "OK",
            "Problem": 0,
        },
        {
            "InstanceId": r"USB\VID_1234&PID_5678\SYNTH-USB-B",
            "FriendlyName": "Synthetic USB Device B",
            "Class": "USB",
            "Status": "OK",
            "Problem": 0,
        },
    ]
    candidate_devices = [
        {
            "InstanceId": r"PCI\VEN_1234&DEV_5678\SYNTH-GPU-A",
            "FriendlyName": "Synthetic GPU A",
            "Class": "Display",
            "Status": "OK",
            "Problem": 0,
        },
        {
            "InstanceId": r"USB\VID_1234&PID_5678\SYNTH-USB-B",
            "FriendlyName": "Synthetic USB Device B",
            "Class": "USB",
            "Status": "Error",
            "Problem": 28,
        },
        {
            "InstanceId": r"PCI\VEN_4321&DEV_8765\SYNTH-NET-C",
            "FriendlyName": "Synthetic Network Device C",
            "Class": "Net",
            "Status": "OK",
            "Problem": 0,
        },
    ]
    snapshots = {
        "baseline": build_device_snapshot(
            baseline_devices,
            captured_utc="2026-11-22T00:00:00Z",
            provider="synthetic-ci-fixture",
            identity_key=KEY,
        ),
        "candidate": build_device_snapshot(
            candidate_devices,
            captured_utc="2026-11-22T00:01:00Z",
            provider="synthetic-ci-fixture",
            identity_key=KEY,
        ),
    }
    for name, snapshot in snapshots.items():
        destination = OUTPUT / f"oplage-{name}.json"
        destination.write_text(
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    print("Created two deterministic synthetic OPlague snapshots; no host inventory was queried.")


if __name__ == "__main__":
    main()
