"""OPlague hardware and game-performance diagnostics.

Read-only inventory, driver evidence and repeatable benchmark analysis.
No firmware, registry, driver, device, power or game-setting mutations occur.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.device_graph import build_compatibility_graph

SCHEMA = "oplague.hardware-game-stack.v1"
SUBSYSTEMS = (
    "host_inventory", "firmware_uefi", "cpu_topology", "memory_topology",
    "gpu_inventory", "pnp_bus_inventory", "driver_store_inventory",
    "device_health", "windows_update_discovery", "driver_compatibility",
    "signature_evidence", "thermal_watchdog", "power_policy", "game_runtime",
    "game_performance_planner",
)
MAX_DEVICES = 20_000
MAX_DRIVERS = 20_000
MAX_SAMPLES = 500_000
MAX_CATALOG = 5_000
GAME_NAMES = {
    "apex", "apex_legends", "cs2", "cyberpunk2077", "eldenring",
    "escape_from_tarkov", "fortniteclient-win64-shipping", "gta5",
    "helldivers2", "hogwartslegacy", "r5apex", "reddeadredemption2",
    "starfield", "valorant-win64-shipping", "witcher3", "wow",
}
PROBLEM_CODES = {
    1: "device_not_configured_correctly", 3: "driver_corrupted_or_memory_unavailable",
    10: "device_cannot_start", 12: "insufficient_system_resources",
    14: "restart_required", 18: "reinstall_device_driver",
    19: "registry_configuration_corrupt", 22: "device_disabled",
    28: "driver_not_installed", 31: "windows_cannot_load_driver",
    32: "driver_service_disabled", 37: "driver_initialization_failed",
    39: "driver_missing_or_corrupted", 41: "driver_not_loaded",
    43: "device_reported_failure", 48: "driver_blocked_by_compatibility_policy",
}

def _map(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}

def _rows(value: Any, limit: int) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value[:limit] if isinstance(item, Mapping)]

def _text(value: Any, limit: int = 512) -> str:
    return str(value).strip()[:limit] if value is not None else ""

def _num(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None

def _int(value: Any) -> int | None:
    number = _num(value)
    return int(number) if number is not None else None

def _section(status: str, summary: str, data: Mapping[str, Any] | None = None,
             findings: Sequence[str] = ()) -> dict[str, Any]:
    return {"status": status, "summary": summary, "data": dict(data or {}),
            "findings": list(findings)}

def analyze_benchmark(benchmark: Mapping[str, Any] | None) -> dict[str, Any]:
    """Calculate average FPS, 1% low and frame-time percentiles from bounded samples."""
    if not benchmark:
        return {"status": "not_provided", "metrics": {}, "findings": []}
    frames = benchmark.get("frame_times_ms")
    fps = benchmark.get("fps_samples")
    if isinstance(frames, list):
        if not 1 <= len(frames) <= MAX_SAMPLES:
            raise ValueError(f"frame_times_ms must contain 1..{MAX_SAMPLES} values")
        values = [_num(item) for item in frames]
        if any(item is None or item <= 0 or item > 10_000 for item in values):
            raise ValueError("frame times must be finite and between 0 and 10,000 ms")
        ordered = sorted(float(item) for item in values if item is not None)
        count = max(1, math.ceil(len(ordered) * 0.01))
        tail = ordered[-count:]
        average_frame = statistics.fmean(ordered)
        average_fps = 1000 / average_frame
        low = 1000 / statistics.fmean(tail)
        low_01 = (1000 / statistics.fmean(ordered[-max(1, math.ceil(len(ordered) * .001)):])
                  if len(ordered) >= 1000 else None)
        median_frame = statistics.median(ordered)
        p99_frame = ordered[min(len(ordered) - 1, math.ceil(len(ordered) * .99) - 1)]
    elif isinstance(fps, list):
        if not 1 <= len(fps) <= MAX_SAMPLES:
            raise ValueError(f"fps_samples must contain 1..{MAX_SAMPLES} values")
        values = [_num(item) for item in fps]
        if any(item is None or item <= 0 or item > 10_000 for item in values):
            raise ValueError("FPS samples must be finite and between 0 and 10,000")
        ordered = sorted(float(item) for item in values if item is not None)
        average_fps = statistics.fmean(ordered)
        count = max(1, math.ceil(len(ordered) * .01))
        low = statistics.fmean(ordered[:count])
        low_01 = statistics.fmean(ordered[:max(1, math.ceil(len(ordered) * .001))]) if len(ordered) >= 1000 else None
        average_frame = 1000 / average_fps
        median_frame = 1000 / statistics.median(ordered)
        p99_frame = None
    else:
        raise ValueError("benchmark must contain frame_times_ms or fps_samples")
    findings = []
    if low / average_fps < .55:
        findings.append("1% low is below 55% of average FPS; inspect repeatable frame-time spikes, shader compilation, temperatures and background load.")
    if p99_frame is not None and p99_frame > median_frame * 2:
        findings.append("99th-percentile frame time exceeds twice the median; prioritize frame pacing over peak-FPS tuning.")
    return {
        "status": "available",
        "metrics": {
            "game": _text(benchmark.get("game"), 160),
            "resolution": _text(benchmark.get("resolution"), 40),
            "preset": _text(benchmark.get("preset"), 80),
            "sample_count": len(ordered),
            "average_fps": round(average_fps, 2),
            "one_percent_low_fps": round(low, 2),
            "point_one_percent_low_fps": round(low_01, 2) if low_01 is not None else None,
            "average_frame_time_ms": round(average_frame, 3),
            "median_frame_time_ms": round(median_frame, 3),
            "p99_frame_time_ms": round(p99_frame, 3) if p99_frame is not None else None,
        },
        "findings": findings,
    }

def build_report(snapshot: Mapping[str, Any], *, benchmark: Mapping[str, Any] | None = None,
                 driver_catalog: Sequence[Mapping[str, Any]] = (),
                 games: Sequence[str] = ()) -> dict[str, Any]:
    """Create the complete 15-subsystem report from a saved or live snapshot."""
    if not isinstance(snapshot, Mapping):
        raise TypeError("snapshot must be a JSON object")
    devices = _rows(snapshot.get("devices"), MAX_DEVICES)
    drivers = _rows(snapshot.get("drivers"), MAX_DRIVERS)
    if len(driver_catalog) > MAX_CATALOG:
        raise ValueError(f"driver catalog is limited to {MAX_CATALOG} entries")
    host = _map(snapshot.get("host"))
    firmware = _map(snapshot.get("firmware"))
    cpu = _map(snapshot.get("cpu"))
    memory = _map(snapshot.get("memory"))
    gpus = _rows(snapshot.get("gpus"), 64)
    modules = _rows(memory.get("modules"), 256)
    total = _int(memory.get("total_bytes")) or sum(_int(x.get("capacity_bytes")) or 0 for x in modules) or None
    free = _int(memory.get("free_bytes"))
    problems = []
    bus_counts: dict[str, int] = {}
    for dev in devices:
        hardware_ids = dev.get("hardware_ids", [])
        compatible_ids = dev.get("compatible_ids", [])
        if isinstance(hardware_ids, str):
            hardware_ids = [hardware_ids]
        if isinstance(compatible_ids, str):
            compatible_ids = [compatible_ids]
        if not isinstance(hardware_ids, (list, tuple)):
            hardware_ids = []
        if not isinstance(compatible_ids, (list, tuple)):
            compatible_ids = []
        identifiers = [*hardware_ids[:256], *compatible_ids[:256]]
        ident = " ".join(str(value) for value in identifiers).upper()
        bus = next(
            (prefix for prefix in ("PCI", "USB", "ACPI", "HID", "BTH", "SCSI", "DISPLAY", "ROOT", "VMBUS")
             if prefix + "\\" in ident),
            "other",
        )
        bus_counts[bus] = bus_counts.get(bus, 0) + 1
        code = _int(dev.get("problem_code"))
        if code not in (None, 0):
            problems.append({"name": _text(dev.get("name")), "class": _text(dev.get("class")),
                             "problem_code": code, "problem": PROBLEM_CODES.get(code, "unmapped_device_problem_code"),
                             "status": _text(dev.get("status"))})
    updates = _rows(snapshot.get("driver_updates"), 1000)
    catalog = [dict(x) for x in driver_catalog]
    for i, item in enumerate(updates):
        ids = item.get("hardware_ids", [])
        if isinstance(ids, str):
            ids = [ids]
        if ids:
            catalog.append({"driver_id": _text(item.get("update_id")) or f"wu-{i}",
                            "package_name": _text(item.get("title")) or f"Windows Update {i}",
                            "hardware_ids": ids, "architectures": ["unspecified"]})
    graph_data: dict[str, Any] = {"catalog_driver_count": len(catalog), "device_count": len(devices),
                                 "exact_match_edges": 0, "architecture_mismatch_edges": 0,
                                 "manual_review_required": True, "matches": []}
    catalog = catalog[:MAX_CATALOG]
    if catalog:
        graph_devices = [{"device_id": f"d{i}", "name": _text(d.get("name")) or f"Device {i}",
                          "hardware_ids": d.get("hardware_ids", []),
                          "compatible_ids": d.get("compatible_ids", [])}
                         for i, d in enumerate(devices)]
        graph_drivers = [{"driver_id": _text(d.get("driver_id")) or f"driver-{i}",
                          "package_name": _text(d.get("package_name") or d.get("title")) or f"Driver {i}",
                          "hardware_ids": d.get("hardware_ids", []),
                          "architectures": d.get("architectures", ["unspecified"])}
                         for i, d in enumerate(catalog)]
        graph = build_compatibility_graph(graph_devices, graph_drivers,
                                          host_architecture=_text(host.get("architecture")) or None)
        for edge in graph["edges"]:
            key = "exact_match_edges" if edge.get("status") == "exact_identifier_candidate" else "architecture_mismatch_edges"
            graph_data[key] += 1
            if len(graph_data["matches"]) < 500:
                di = int(edge["device_id"][1:])
                driver = next((x for x in graph_drivers if x["driver_id"] == edge["driver_id"]), {})
                graph_data["matches"].append({"device": graph_devices[di]["name"],
                                               "package": driver.get("package_name", ""),
                                               "status": edge.get("status"),
                                               "matched_ids": edge.get("matched_ids", [])})
    zone_rows = []
    thermal_findings = []
    for zone in _rows(snapshot.get("thermal_zones"), 128):
        value = _num(zone.get("current_temperature"))
        celsius = value / 10 - 273.15 if value is not None and value > 1000 else value
        if celsius is not None and not -20 <= celsius <= 150:
            celsius = None
        state = "unknown" if celsius is None else "hot" if celsius >= 95 else "elevated" if celsius >= 85 else "normal"
        zone_rows.append({"name": _text(zone.get("name")) or "ACPI thermal zone",
                          "temperature_c": round(celsius, 1) if celsius is not None else None, "state": state})
        if state == "hot":
            thermal_findings.append("ACPI thermal zone is at least 95 °C; stop stress testing and check cooling.")
        elif state == "elevated":
            thermal_findings.append("ACPI thermal zone is at least 85 °C; repeat the measurement under a controlled load.")
    signed = sum(1 for d in drivers if d.get("is_signed") is True)
    unsigned = sum(1 for d in drivers if d.get("is_signed") is False)
    process_rows = _rows(snapshot.get("processes"), 5000)
    wanted = GAME_NAMES | {str(x).casefold().removesuffix(".exe") for x in games}
    running = [{"process": _text(p.get("name")), "pid": _int(p.get("pid")),
                "cpu_seconds": _num(p.get("cpu_seconds")), "working_set_bytes": _int(p.get("working_set_bytes"))}
               for p in process_rows if _text(p.get("name")).casefold().removesuffix(".exe") in wanted]
    update_status = _text(snapshot.get("driver_update_discovery_status")) or "not_requested"
    firmware_status = "available" if any(firmware.get(k) for k in ("vendor", "version", "release_date")) else "limited"
    total_gib = total / (1024 ** 3) if total else None
    memory_findings = []
    if total_gib is not None and total_gib < 16:
        memory_findings.append("Installed memory is below 16 GiB; check game requirements and background usage before upgrading.")
    if total and free is not None and 1 - min(free, total) / total >= .9:
        memory_findings.append("Physical memory use is at least 90% in this snapshot; repeat after closing unrelated workloads.")
    recs = []
    if problems:
        recs.append({"priority": "high", "area": "device_health", "action": "Investigate reported PnP problem codes using exact device IDs and the current vendor package.", "changes_system": False})
    if any(z["state"] in ("hot", "elevated") for z in zone_rows):
        recs.append({"priority": "high", "area": "cooling", "action": "Check airflow and cooling before increasing power limits.", "changes_system": False})
    if total_gib is not None and total_gib < 16:
        recs.append({"priority": "medium", "area": "memory", "action": "Check memory pressure and platform upgrade limits.", "changes_system": False})
    if updates:
        recs.append({"priority": "medium", "area": "drivers", "action": "Review Windows Update candidates against exact device IDs and vendor release notes; do not install from a title match.", "changes_system": False})
    bench = analyze_benchmark(benchmark)
    if bench["status"] == "not_provided":
        recs.append({"priority": "medium", "area": "measurement", "action": "Capture three runs at the same scene, resolution, preset and power source; compare average FPS and 1% lows.", "changes_system": False})
    else:
        recs.extend({"priority": "medium", "area": "frame_pacing", "action": x, "changes_system": False} for x in bench["findings"])

    subsystems = {
        "host_inventory": _section("available" if host else "limited", "OS build, platform manufacturer and architecture.",
                                   {"manufacturer": _text(host.get("manufacturer")), "model": _text(host.get("model")),
                                    "os_name": _text(host.get("os_name") or host.get("caption")),
                                    "os_version": _text(host.get("version")), "os_build": _text(host.get("build_number")),
                                    "architecture": _text(host.get("architecture"))}),
        "firmware_uefi": _section(firmware_status, "SMBIOS/UEFI and platform security evidence, read only.",
                                  {"vendor": _text(firmware.get("vendor")), "version": _text(firmware.get("version")),
                                   "release_date": _text(firmware.get("release_date")), "smbios_version": _text(firmware.get("smbios_version")),
                                   "secure_boot": ("enabled" if firmware.get("secure_boot") is True else "disabled" if firmware.get("secure_boot") is False else _text(firmware.get("secure_boot") or "unknown")),
                                   "tpm": "present" if firmware.get("tpm_present") is True else "not_reported" if firmware.get("tpm_present") is None else "not_detected"},
                                  ["Firmware changes are never applied; use only signed OEM updates and the recovery procedure."]),
        "cpu_topology": _section("available" if cpu else "limited", "Processor model, core/thread topology and current load.",
                                 {"name": _text(cpu.get("name")), "cores": _int(cpu.get("cores")),
                                  "logical_processors": _int(cpu.get("logical_processors")),
                                  "max_clock_mhz": _int(cpu.get("max_clock_mhz")), "load_percent": _num(cpu.get("load_percent")),
                                  "virtualization_firmware_enabled": cpu.get("virtualization_firmware_enabled")}),
        "memory_topology": _section("available" if total else "limited", "Memory capacity and DIMM metadata without module serials.",
                                   {"total_bytes": total, "total_gib": round(total_gib, 2) if total_gib else None,
                                    "free_bytes": free, "module_count": len(modules),
                                    "modules": [{"capacity_bytes": _int(m.get("capacity_bytes")),
                                                 "speed_mhz": _int(m.get("speed_mhz")),
                                                 "configured_speed_mhz": _int(m.get("configured_speed_mhz")),
                                                 "manufacturer": _text(m.get("manufacturer"), 80)} for m in modules]},
                                   memory_findings),
        "gpu_inventory": _section("available" if gpus else "limited", "Display adapter names and reported driver versions.",
                                  {"adapter_count": len(gpus), "adapters": [
                                      {"name": _text(g.get("name")), "driver_version": _text(g.get("driver_version")),
                                       "driver_date": _text(g.get("driver_date")), "video_processor": _text(g.get("video_processor")),
                                       "status": _text(g.get("status")),
                                       "current_resolution": f'{_int(g.get("horizontal_resolution"))}x{_int(g.get("vertical_resolution"))}' if _int(g.get("horizontal_resolution")) and _int(g.get("vertical_resolution")) else None,
                                       "refresh_rate_hz": _int(g.get("refresh_rate_hz"))} for g in gpus]}),
        "pnp_bus_inventory": _section("available" if devices else "limited", "Present Plug and Play devices grouped by observed bus; identifiers remain private by default.",
                                       {"device_count": len(devices), "bus_counts": dict(sorted(bus_counts.items())),
                                        "problem_device_count": len(problems)}),
        "driver_store_inventory": _section("available" if drivers else "limited", "Bound driver metadata from Win32_PnPSignedDriver; not a complete Driver Store export.",
                                            {"bound_driver_count": len(drivers),
                                             "provider_counts": {name: sum(1 for d in drivers if _text(d.get("provider")) == name) for name in sorted({_text(d.get("provider")) or "unknown" for d in drivers})},
                                             "drivers": [{"device_name": _text(d.get("device_name")), "provider": _text(d.get("provider")),
                                                          "version": _text(d.get("version")), "date": _text(d.get("date")),
                                                          "inf_name": _text(d.get("inf_name")),
                                                          "is_signed": d.get("is_signed") if isinstance(d.get("is_signed"), bool) else None}
                                                         for d in drivers[:500]]},
                                            ["PnPUtil can enumerate staged packages; localized command output is not parsed here."]),
        "device_health": _section("warning" if problems else "available" if devices else "limited", "Windows PnP problem codes surfaced for diagnosis, not auto-repair.",
                                  {"problem_device_count": len(problems), "problem_devices": problems[:200]}),
        "windows_update_discovery": _section("available" if updates else "limited" if update_status == "error" else "not_requested" if update_status == "not_requested" else "available",
                                             "Optional Windows Update Agent driver search; no download or installation.",
                                             {"discovery_status": update_status, "candidate_count": len(updates),
                                              "candidates": [{"title": _text(u.get("title")), "provider": _text(u.get("provider")),
                                                              "manufacturer": _text(u.get("manufacturer")), "model": _text(u.get("model")),
                                                              "version": _text(u.get("version")), "release_date": _text(u.get("release_date")),
                                                              "hardware_id_count": len(u.get("hardware_ids", [])) if isinstance(u.get("hardware_ids", []), (list, tuple)) else 0,
                                                              "update_id": _text(u.get("update_id"), 80)} for u in updates[:1000]]}),
        "driver_compatibility": _section("warning" if graph_data["exact_match_edges"] or graph_data["architecture_mismatch_edges"] else "available" if catalog else "not_requested",
                                         "Exact hardware-ID matches are candidates only, not Windows driver rank or install approval.",
                                         graph_data, ["Validate OS target, Windows driver rank, CAT signature, publisher and rollback before any future deployment."]),
        "signature_evidence": _section("available" if drivers else "limited", "OS-reported IsSigned metadata; certificate chain and catalog trust are not verified.",
                                        {"reported_signed": signed, "reported_unsigned": unsigned,
                                         "signature_state_unknown": len(drivers) - signed - unsigned,
                                         "trust_verdict": "not_performed"},
                                        ["Never disable driver-signature enforcement to load an unknown package."]),
        "thermal_watchdog": _section("warning" if any(x["state"] in ("hot", "elevated") for x in zone_rows) else "available" if zone_rows else "limited",
                                     "ACPI thermal zones only; absent readings do not mean CPU or GPU is cool.",
                                     {"zone_count": len(zone_rows), "zones": zone_rows},
                                     thermal_findings or (["No ACPI thermal zone was exposed; use vendor sensor tools for CPU/GPU temperatures."] if not zone_rows else [])),
        "power_policy": _section("available" if _map(snapshot.get("power")) else "limited", "Active power scheme and battery state; no power settings are changed.",
                                  {"active_scheme": _text(_map(snapshot.get("power")).get("active_scheme"), 300),
                                   "battery_present": _map(snapshot.get("battery")).get("present"),
                                   "battery_status": _text(_map(snapshot.get("battery")).get("status")),
                                   "estimated_charge_percent": _num(_map(snapshot.get("battery")).get("charge_percent"))}),
        "game_runtime": _section("available" if process_rows else "limited", "Configured game processes and working-set/CPU-time metadata; no process is altered.",
                                 {"running_game_count": len(running), "games": running[:100]}),
        "game_performance_planner": _section("available" if bench["status"] == "available" else "limited",
                                             "Benchmark-driven frame pacing advice; no clocks, affinity or game settings are changed.",
                                             {"benchmark": bench, "recommendations": recs,
                                              "automatic_changes_applied": 0, "rollback_required": False},
                                             ["Repeat the same scene, resolution, preset, driver and power source before judging a change."]),
    }
    return {
        "schema": SCHEMA, "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_snapshot_time": _text(snapshot.get("collected_at"), 80) or None,
        "mode": "read_only_analysis", "subsystem_count": len(subsystems), "subsystems": subsystems,
        "safety": {
            "firmware_written": False, "drivers_downloaded": False, "drivers_installed": False,
            "drivers_loaded": False, "registry_modified": False, "power_policy_modified": False,
            "device_state_modified": False, "processes_modified": False,
            "game_settings_modified": False, "kernel_code_modified": False,
        },
    }

def redact_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Remove exact PnP IDs from an export and retain a privacy marker."""
    copy = json.loads(json.dumps(report))
    matches = copy.get("subsystems", {}).get("driver_compatibility", {}).get("data", {}).get("matches", [])
    for match in matches:
        match.pop("matched_ids", None)
    copy["privacy"] = {"hardware_ids_included": False, "device_instance_ids_included": False,
                       "note": "PnP instance and matched hardware IDs are omitted from this report."}
    return copy

def load_json_object(path: str | Path) -> dict[str, Any]:
    source = Path(path).expanduser()
    if source.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("JSON input exceeds 64 MiB")
    value = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{source} must contain a JSON object")
    return value

def load_driver_catalog(path: str | Path | None) -> list[dict[str, Any]]:
    if path is None:
        return []
    value = load_json_object(path)
    if value.get("schema") not in ("oplague.driver-catalog.v1", "oplague.driver-candidate-list.v1"):
        raise ValueError("Driver catalog schema must be oplague.driver-catalog.v1")
    items = value.get("drivers", [])
    if not isinstance(items, list) or len(items) > MAX_CATALOG:
        raise ValueError(f"Driver catalog is limited to {MAX_CATALOG} entries")
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not isinstance(item.get("hardware_ids", []), list):
            raise ValueError(f"Invalid driver catalog entry at index {index}")
    return items

_POWERSHELL_PROBE = r"""
$ErrorActionPreference = 'Stop'
function SafeCim($class, $namespace = 'root/cimv2') {
  try { @(Get-CimInstance -ClassName $class -Namespace $namespace -ErrorAction Stop) } catch { @() }
}
function SafePnpProperty($instance, $key) {
  try { $value = (Get-PnpDeviceProperty -InstanceId $instance -KeyName $key -ErrorAction Stop).Data; @($value) } catch { @() }
}
$os = SafeCim 'Win32_OperatingSystem' | Select-Object -First 1
$cs = SafeCim 'Win32_ComputerSystem' | Select-Object -First 1
$bios = SafeCim 'Win32_BIOS' | Select-Object -First 1
$cpu = SafeCim 'Win32_Processor' | Select-Object -First 1
$memOS = SafeCim 'Win32_OperatingSystem' | Select-Object -First 1
$memory = @(SafeCim 'Win32_PhysicalMemory' | Select-Object -First 256 | ForEach-Object {
  @{ capacity_bytes = [uint64]$_.Capacity; speed_mhz = $_.Speed; configured_speed_mhz = $_.ConfiguredClockSpeed; manufacturer = $_.Manufacturer }
})
$gpus = @(SafeCim 'Win32_VideoController' | Select-Object -First 64 | ForEach-Object {
  @{ name = $_.Name; driver_version = $_.DriverVersion; driver_date = $_.DriverDate; video_processor = $_.VideoProcessor; status = $_.Status; horizontal_resolution = $_.CurrentHorizontalResolution; vertical_resolution = $_.CurrentVerticalResolution; refresh_rate_hz = $_.CurrentRefreshRate }
})
$drivers = @(SafeCim 'Win32_PnPSignedDriver' | Select-Object -First 20000 | ForEach-Object {
  @{ device_name = $_.DeviceName; device_id = $_.DeviceID; provider = $_.DriverProviderName; version = $_.DriverVersion; date = $_.DriverDate; inf_name = $_.InfName; is_signed = $_.IsSigned }
})
$devices = @()
try {
  foreach ($d in @(Get-PnpDevice -PresentOnly -ErrorAction Stop | Select-Object -First 20000)) {
    $devices += @{ name = $d.FriendlyName; class = $d.Class; status = $d.Status; pnp_id = $d.InstanceId;
      hardware_ids = (SafePnpProperty $d.InstanceId 'DEVPKEY_Device_HardwareIds');
      compatible_ids = (SafePnpProperty $d.InstanceId 'DEVPKEY_Device_CompatibleIds');
      problem_code = (SafePnpProperty $d.InstanceId 'DEVPKEY_Device_ProblemCode' | Select-Object -First 1) }
  }
} catch {
  $devices = @(SafeCim 'Win32_PnPEntity' | Select-Object -First 20000 | ForEach-Object {
    @{ name = $_.Name; class = $_.PNPClass; status = $_.Status; pnp_id = $_.PNPDeviceID; hardware_ids = @(); compatible_ids = @(); problem_code = $_.ConfigManagerErrorCode }
  })
}
$thermal = @(SafeCim 'MSAcpi_ThermalZoneTemperature' 'root/wmi' | Select-Object -First 128 | ForEach-Object { @{ name = $_.InstanceName; current_temperature = $_.CurrentTemperature } })
$processes = @(Get-Process | Select-Object -First 5000 | ForEach-Object { @{ name = $_.ProcessName; pid = $_.Id; cpu_seconds = $_.CPU; working_set_bytes = $_.WorkingSet64 } })
$power = (& powercfg.exe /getactivescheme 2>$null | Out-String).Trim()
$secureBoot = 'unknown'
try { $secureBoot = [bool](Confirm-SecureBootUEFI -ErrorAction Stop) } catch {}
$tpmPresent = $null
try { $tpmPresent = [bool](Get-Tpm -ErrorAction Stop).TpmPresent } catch {}
$battery = @{ present = $false; status = ''; charge_percent = $null }
$b = SafeCim 'Win32_Battery' | Select-Object -First 1
if ($null -ne $b) { $battery.present = $true; $battery.status = [string]$b.BatteryStatus; $battery.charge_percent = $b.EstimatedChargeRemaining }
$updates = @()
$updateStatus = 'not_requested'
$updateError = ''
if ($env:OPLAGUE_DISCOVER_DRIVER_UPDATES -eq '1') {
  try {
    $session = New-Object -ComObject 'Microsoft.Update.Session'
    $search = $session.CreateUpdateSearcher().Search("IsInstalled=0 and Type='Driver' and IsHidden=0")
    for ($i = 0; $i -lt [Math]::Min([int]$search.Updates.Count, 1000); $i++) {
      $u = $search.Updates.Item($i)
      $ids = @()
      try { $ids = @($u.DriverHardwareID) } catch {}
      $updates += @{ title = [string]$u.Title; update_id = [string]$u.Identity.UpdateID; provider = [string]$u.DriverProvider;
        manufacturer = [string]$u.DriverManufacturer; model = [string]$u.DriverModel; version = [string]$u.DriverVersion;
        release_date = [string]$u.DriverVerDate; hardware_ids = $ids }
    }
    $updateStatus = 'complete'
  } catch { $updateStatus = 'error'; $updateError = $_.Exception.Message }
}
@{
 schema = 'oplague.hardware-snapshot.v1'; collected_at = [DateTime]::UtcNow.ToString('o')
 host = @{ manufacturer = $cs.Manufacturer; model = $cs.Model; os_name = $os.Caption; version = $os.Version; build_number = $os.BuildNumber; architecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString() }
 firmware = @{ vendor = $bios.Manufacturer; version = $bios.SMBIOSBIOSVersion; release_date = $bios.ReleaseDate; smbios_version = "$($bios.SMBIOSMajorVersion).$($bios.SMBIOSMinorVersion)"; secure_boot = $secureBoot; tpm_present = $tpmPresent }
 cpu = @{ name = $cpu.Name; cores = $cpu.NumberOfCores; logical_processors = $cpu.NumberOfLogicalProcessors; max_clock_mhz = $cpu.MaxClockSpeed; load_percent = $cpu.LoadPercentage; virtualization_firmware_enabled = $cpu.VirtualizationFirmwareEnabled }
 memory = @{ total_bytes = [uint64]$cs.TotalPhysicalMemory; free_bytes = [uint64]$memOS.FreePhysicalMemory * 1024; modules = $memory }
 gpus = $gpus; devices = $devices; drivers = $drivers; thermal_zones = $thermal
 power = @{ active_scheme = $power }; battery = $battery; processes = $processes
 driver_updates = $updates; driver_update_discovery_status = $updateStatus; driver_update_discovery_error = $updateError
} | ConvertTo-Json -Depth 8 -Compress
"""

def collect_windows_snapshot(*, discover_driver_updates: bool = False, timeout_seconds: int = 90) -> dict[str, Any]:
    """Run fixed read-only Windows CIM/PnP/firmware queries."""
    if os.name != "nt":
        raise RuntimeError("Live collection is Windows-only; use --snapshot for offline analysis.")
    if not 10 <= timeout_seconds <= 300:
        raise ValueError("timeout_seconds must be between 10 and 300")
    env = os.environ.copy()
    env["OPLAGUE_DISCOVER_DRIVER_UPDATES"] = "1" if discover_driver_updates else "0"
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", _POWERSHELL_PROBE],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout_seconds, check=False, env=env,
    )
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout or "Hardware probe failed").strip()[:2000])
    value = json.loads(result.stdout.lstrip("\ufeff"))
    if not isinstance(value, dict):
        raise RuntimeError("PowerShell probe returned an unexpected JSON shape")
    return value

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OPlague 15-subsystem hardware/game diagnostics (read only)")
    parser.add_argument("--snapshot", help="previously captured hardware snapshot JSON")
    parser.add_argument("--driver-catalog", help="local exact-ID driver catalog JSON")
    parser.add_argument("--benchmark", help="FPS or frametime benchmark JSON")
    parser.add_argument("--game", action="append", default=[], help="extra process name to detect")
    parser.add_argument("--discover-windows-update-drivers", action="store_true",
                        help="search Windows Update for driver candidates; metadata only, no download/install")
    parser.add_argument("--include-hardware-ids", action="store_true", help="retain exact IDs in exported report")
    parser.add_argument("--output", help="write report JSON to this path")
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args(argv)
    try:
        snapshot = load_json_object(args.snapshot) if args.snapshot else collect_windows_snapshot(
            discover_driver_updates=args.discover_windows_update_drivers, timeout_seconds=args.timeout)
        benchmark = load_json_object(args.benchmark) if args.benchmark else None
        report = build_report(snapshot, benchmark=benchmark,
                              driver_catalog=load_driver_catalog(args.driver_catalog), games=args.game)
        if not args.include_hardware_ids:
            report = redact_report(report)
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            destination = Path(args.output).expanduser()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(rendered, encoding="utf-8")
            print(f"OPlague report written to {destination}")
        else:
            sys.stdout.write(rendered)
        return 0
    except (OSError, RuntimeError, ValueError, TypeError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        print(f"OPlague hardware stack: {error}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
