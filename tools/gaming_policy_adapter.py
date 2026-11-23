"""Expose OPlague's real gaming evidence as DuckOS capability records.

The adapter only describes providers backed by existing local measurements.
It never changes a power plan, driver, registry key, service or device.
"""
from __future__ import annotations

import math
import platform
import re
from typing import Any

SCHEMA = "oplague.duckos-gaming-evidence.v1"
SAFE_SHA256 = re.compile(r"^[0-9a-fA-F]{64}$")
PROVIDER_IDS = (
    "process_catalog", "window_manager", "graphics_context", "display_info",
    "power_source", "session_coordinator", "scheduler", "cpu_telemetry", "cpu_topology",
    "interrupt_telemetry", "power_telemetry", "timer_provider", "frame_time",
    "memory_pressure", "swap_metrics", "compression", "page_cache",
    "storage_prefetch", "vram_metrics", "compositor", "gpu_queue", "vrr",
    "hdr", "gpu_telemetry", "graphics_recovery", "storage_io", "network_metrics",
    "input_devices", "usb_power", "background_sync", "event_log", "pcie_metrics",
    "power_plan", "thermal_control", "fan_control", "reliability_events",
    "compatibility_profiles", "hardware_profile", "consent_manager", "session_snapshot",
)


class GamingEvidenceError(ValueError):
    """Raised when supplied evidence is malformed or does not match its provider."""


def _provider(available: bool, name: str, reason: str | None = None,
              version: str | None = None) -> dict[str, Any]:
    return {
        "available": bool(available),
        "provider": name,
        "version": version,
        "reason": None if available else (reason or "evidence not supplied"),
    }


def _valid_record(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GamingEvidenceError(f"{field} must be an object")
    return value


def build_duckos_capability_evidence(
    *,
    devices: list[dict[str, Any]] | None = None,
    gpu_telemetry: dict[str, Any] | None = None,
    reliability_events: dict[str, Any] | None = None,
    frame_time: dict[str, Any] | None = None,
    active_power_plan: dict[str, Any] | None = None,
    snapshot: dict[str, Any] | None = None,
    compatibility_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete provider map; unknown host capabilities stay unavailable."""
    providers = {
        name: _provider(False, "OPlague", "OPlague has no verified provider for this capability")
        for name in PROVIDER_IDS
    }

    if devices is not None:
        if not isinstance(devices, list) or any(not isinstance(item, dict) for item in devices):
            raise GamingEvidenceError("devices must be a list of device objects")
        providers["hardware_profile"] = _provider(
            True, "OPlague PnP inventory", version="read-only"
        )

    if gpu_telemetry is not None:
        record = _valid_record(gpu_telemetry, "gpu_telemetry")
        if record.get("provider") != "nvidia-smi" or not isinstance(record.get("available"), bool):
            raise GamingEvidenceError("gpu_telemetry must contain a boolean availability from nvidia-smi")
        gpu_rows = record.get("gpus")
        if not isinstance(gpu_rows, list) or any(not isinstance(item, dict) for item in gpu_rows):
            raise GamingEvidenceError("gpu_telemetry.gpus must be a list of sensor records")
        available = record["available"] and bool(gpu_rows)
        providers["gpu_telemetry"] = _provider(
            available, "nvidia-smi",
            record.get("reason") or "NVIDIA sensor rows are unavailable",
            version="read-only",
        )
        if available:
            providers["vram_metrics"] = _provider(True, "nvidia-smi", version="read-only")

    if reliability_events is not None:
        record = _valid_record(reliability_events, "reliability_events")
        if not isinstance(record.get("available"), bool):
            raise GamingEvidenceError("reliability_events.available must be boolean")
        providers["reliability_events"] = _provider(
            record["available"], str(record.get("provider") or "Windows System event log"),
            record.get("reason"), version="read-only",
        )

    if frame_time is not None:
        record = _valid_record(frame_time, "frame_time")
        count = record.get("sample_count")
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise GamingEvidenceError("frame_time.sample_count must be a positive integer")
        value = record.get("p99_frametime_ms")
        if (
            isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(float(value)) or value <= 0
        ):
            raise GamingEvidenceError("frame_time.p99_frametime_ms must be a finite positive measurement")
        providers["frame_time"] = _provider(True, "PresentMon-compatible CSV", version="measured")
    
    if active_power_plan is not None:
        record = _valid_record(active_power_plan, "active_power_plan")
        guid = record.get("guid")
        if not isinstance(guid, str) or not re.fullmatch(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", guid
        ):
            raise GamingEvidenceError("active_power_plan.guid must be a power-scheme GUID")
        providers["power_plan"] = _provider(
            platform.system() == "Windows",
            "Windows powercfg",
            "temporary power-plan sessions are supported only on Windows",
            version="read-only snapshot",
        )

    if snapshot is not None:
        record = _valid_record(snapshot, "snapshot")
        if not isinstance(record.get("snapshot_id"), str) or not record["snapshot_id"]:
            raise GamingEvidenceError("snapshot.snapshot_id is required")
        fingerprint = record.get("hardware_fingerprint")
        if not isinstance(fingerprint, str) or not SAFE_SHA256.fullmatch(fingerprint):
            raise GamingEvidenceError("snapshot.hardware_fingerprint must be a SHA-256 hex digest")
        providers["session_snapshot"] = _provider(True, "OPlague atomic snapshot", version="v1")

    if compatibility_profile is not None:
        record = _valid_record(compatibility_profile, "compatibility_profile")
        if record.get("validation") != "operator_confirmed":
            raise GamingEvidenceError("compatibility profile must be operator-confirmed")
        if not isinstance(record.get("game_id"), str) or not isinstance(record.get("hardware_hash"), str):
            raise GamingEvidenceError("compatibility profile requires game_id and hardware_hash")
        if not SAFE_SHA256.fullmatch(record["hardware_hash"]):
            raise GamingEvidenceError("compatibility profile hardware_hash must be SHA-256")
        providers["compatibility_profiles"] = _provider(
            True, "OPlague validated local profile cache", version="operator-confirmed"
        )

    return {
        "schema": SCHEMA,
        "providers": providers,
        "provided_capabilities": sorted(
            name for name, evidence in providers.items() if evidence["available"]
        ),
        "system_mutations_performed": False,
        "driver_state_changed": False,
        "power_plan_changed": False,
        "execution_performed": False,
    }


def to_duckos_capabilities(evidence: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Return only the capability map accepted by DuckOS assess_capabilities()."""
    if not isinstance(evidence, dict) or evidence.get("schema") != SCHEMA:
        raise GamingEvidenceError(f"expected {SCHEMA} evidence")
    providers = evidence.get("providers")
    if not isinstance(providers, dict) or set(providers) != set(PROVIDER_IDS):
        raise GamingEvidenceError("provider inventory is incomplete or contains unknown fields")
    result = {}
    for name, value in providers.items():
        record = _valid_record(value, f"providers.{name}")
        if not isinstance(record.get("available"), bool):
            raise GamingEvidenceError(f"providers.{name}.available must be boolean")
        result[name] = {
            "available": record["available"],
            "provider": str(record.get("provider") or "OPlague")[:128],
            "version": record.get("version"),
            "reason": record.get("reason"),
        }
    return result
