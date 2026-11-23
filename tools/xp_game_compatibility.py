"""Read-only compatibility audit for Windows XP SP3-era game requirements.

This tool translates the old graphics, display, sound, input and network
expectations into explicit host-side findings. It never changes drivers,
registry keys, services, power plans or display modes.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

PROFILE_SCHEMA = "duckos.game-launch-profile.v1"
REPORT_SCHEMA = "oplague.xp-sp3-game-compatibility.v1"
MAX_INPUT_BYTES = 1024 * 1024

def _finding(code: str, severity: str, message: str, next_step: str) -> dict[str, str]:
    return {"code": code, "severity": severity, "message": message, "next_step": next_step}

def audit_game_profile(profile: dict[str, Any], hardware: dict[str, Any] | None = None) -> dict[str, Any]:
    if not isinstance(profile, dict) or profile.get("schema") != PROFILE_SCHEMA:
        raise ValueError(f"expected a {PROFILE_SCHEMA} profile")
    compatibility = profile.get("compatibility")
    if not isinstance(compatibility, dict):
        raise ValueError("profile.compatibility must be an object")
    display = compatibility.get("display", {})
    if not isinstance(display, dict):
        raise ValueError("profile.compatibility.display must be an object")
    findings: list[dict[str, str]] = []

    graphics = compatibility.get("graphics", [])
    audio = compatibility.get("audio", [])
    input_apis = compatibility.get("input", [])
    network = compatibility.get("network", [])
    for field, values in (("graphics", graphics), ("audio", audio), ("input", input_apis), ("network", network)):
        if not isinstance(values, list) or any(not isinstance(item, str) for item in values):
            raise ValueError(f"profile.compatibility.{field} must be a list of strings")

    if "glide" in graphics:
        findings.append(_finding(
            "XP-GFX-GLIDE", "warning",
            "The profile requests 3dfx Glide; modern GPUs generally need a separately installed Glide wrapper.",
            "Check a trusted wrapper's supported Glide version and keep its DLL beside the game only when the wrapper vendor documents that setup.",
        ))
    if "directdraw" in graphics or any(item in graphics for item in ("direct3d7", "direct3d8", "direct3d9")):
        findings.append(_finding(
            "XP-GFX-DX", "info",
            "The game uses a legacy DirectDraw/Direct3D path; this audit does not prove that a translation backend supports every call.",
            "Verify the selected Wine/Proton graphics backend and inspect the game's own log after a controlled test.",
        ))
    if "opengl" in graphics:
        findings.append(_finding(
            "XP-GFX-OPENGL", "info",
            "OpenGL support depends on the host driver's ICD and the compatibility runtime's GL bridge.",
            "Confirm the renderer and GL version reported by the host driver; do not infer support from the GPU name alone.",
        ))

    color_depth = display.get("color_depth", 32)
    if color_depth in {8, 16}:
        findings.append(_finding(
            "XP-DISPLAY-COLOR-DEPTH", "warning",
            f"The profile requests {color_depth}-bit color, a legacy mode that may not be exposed by a modern compositor.",
            "Try a per-game compatibility option or a runtime-managed virtual display; do not change the global desktop mode automatically.",
        ))
    width, height = display.get("width", 1024), display.get("height", 768)
    if isinstance(width, bool) or isinstance(height, bool) or not isinstance(width, int) or not isinstance(height, int) or width < 1 or height < 1:
        raise ValueError("display width and height must be positive integers")
    ratio = width / height
    if not math.isclose(ratio, 4 / 3, rel_tol=0.015):
        findings.append(_finding(
            "XP-DISPLAY-ASPECT", "info",
            "The requested display mode is not 4:3; classic interfaces may stretch, crop or misplace their HUD.",
            "Use a game-specific widescreen patch or integer/scaled viewport when available; preserve the original game files.",
        ))
    refresh = display.get("refresh_rate_hz", 60)
    if isinstance(refresh, bool) or not isinstance(refresh, int) or not 30 <= refresh <= 360:
        raise ValueError("display.refresh_rate_hz must be an integer from 30 to 360")
    if refresh > 60:
        findings.append(_finding(
            "XP-DISPLAY-REFRESH", "warning",
            f"The requested {refresh} Hz mode may expose old frame-rate-dependent timing or physics.",
            "Use an in-game frame limiter or runtime cap and compare behavior at 60 Hz before changing host display settings.",
        ))

    if "eax" in audio:
        findings.append(_finding(
            "XP-AUDIO-EAX", "warning",
            "EAX is requested, but modern host audio stacks rarely expose the original hardware EAX path directly.",
            "Check whether the chosen runtime offers an OpenAL/EAX emulation layer; otherwise use the game's software audio mode.",
        ))
    if "directsound" in audio or "winmm" in audio:
        findings.append(_finding(
            "XP-AUDIO-LEGACY", "info",
            "DirectSound/WinMM calls require the selected compatibility runtime's audio bridge.",
            "Check audio output, sample rate and channel layout in a short test session; this report does not play sound.",
        ))

    if "directinput" in input_apis or "xinput" in input_apis:
        findings.append(_finding(
            "XP-INPUT-LEGACY", "info",
            "The profile requests a legacy input API; controller behavior depends on the host HID mapping.",
            "Verify buttons, axes, dead zones and cursor capture in the game's own input test.",
        ))
    if "directplay" in network or "ipx_spx" in network:
        findings.append(_finding(
            "XP-NETWORK-LEGACY", "warning",
            "DirectPlay or IPX/SPX is requested; modern hosts do not provide a drop-in legacy LAN stack by default.",
            "Use a documented compatibility gateway or a private network tunnel; do not expose legacy game ports to the public internet.",
        ))

    hardware_summary = {"supplied": hardware is not None, "display_adapters": []}
    if hardware is not None:
        if not isinstance(hardware, dict) or not isinstance(hardware.get("devices", []), list):
            raise ValueError("hardware snapshot must contain a devices list")
        for device in hardware.get("devices", []):
            if not isinstance(device, dict):
                continue
            description = " ".join(str(device.get(key) or "") for key in ("name", "friendly_name", "device_class")).casefold()
            if any(term in description for term in ("display", "vga", "3d controller", "gpu", "graphics")):
                hardware_summary["display_adapters"].append({
                    "name": str(device.get("name") or device.get("friendly_name") or "Unknown adapter"),
                    "driver_version": str(device.get("driver_version") or ""),
                    "status": str(device.get("status") or "unknown"),
                })
        if not hardware_summary["display_adapters"]:
            findings.append(_finding(
                "XP-HW-GPU-UNKNOWN", "warning",
                "The supplied snapshot did not identify a display adapter; no GPU or driver compatibility claim can be made.",
                "Capture a fresh read-only OPlague/DuckOS device snapshot before selecting a graphics backend.",
            ))

    return {
        "schema": REPORT_SCHEMA,
        "game": {"id": str(profile.get("id", "")), "name": str(profile.get("name", ""))},
        "target": "windows-xp-sp3",
        "status": "attention_required" if any(item["severity"] == "warning" for item in findings) else "reviewed",
        "summary": {"findings": len(findings), "warnings": sum(item["severity"] == "warning" for item in findings)},
        "hardware": hardware_summary,
        "findings": findings,
        "read_only": True,
        "drivers_changed": False,
        "display_settings_changed": False,
        "registry_changed": False,
        "network_modified": False,
    }

def audit_file(path: str | Path, hardware_path: str | Path | None = None) -> dict[str, Any]:
    source = Path(path).expanduser()
    if source.is_symlink() or not source.is_file():
        raise ValueError("profile must be a regular, non-symlink file")
    if source.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("profile exceeds the 1 MiB input limit")
    profile = json.loads(source.read_text(encoding="utf-8"))
    hardware = None
    if hardware_path is not None:
        snapshot_path = Path(hardware_path).expanduser()
        if snapshot_path.is_symlink() or not snapshot_path.is_file() or snapshot_path.stat().st_size > MAX_INPUT_BYTES:
            raise ValueError("hardware snapshot must be a regular file no larger than 1 MiB")
        hardware = json.loads(snapshot_path.read_text(encoding="utf-8"))
    return audit_game_profile(profile, hardware)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit XP-era game API and hardware requirements without changing the host.")
    parser.add_argument("profile", type=Path)
    parser.add_argument("--hardware", type=Path, help="optional read-only OPlague/DuckOS device snapshot")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = audit_file(args.profile, args.hardware)
        encoded = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            if args.output.resolve() == args.profile.resolve() or (args.hardware and args.output.resolve() == args.hardware.resolve()):
                raise ValueError("report output must not overwrite an input file")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(encoded, encoding="utf-8", newline="\n")
        else:
            print(encoded, end="")
        return 0
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        print(f"xp-game-compatibility: {error}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
