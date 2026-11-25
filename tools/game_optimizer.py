"""Safe, reversible game-session and hardware-profile helpers for OPlague.

The module deliberately avoids driver installation, registry edits, overclocking,
interrupt-affinity changes, service termination and network-stack modification.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
import platform
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

SCHEMA_VERSION = "oplague.gaming.v1"
GUID_PATTERN = re.compile(r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$")
DEVICE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,31}(\\[A-Z0-9&_.{}:+#\\-]+)+$")
FRAME_TIME_COLUMNS = (
    "msbetweenpresents",
    "frametime",
    "frametimems",
    "msbetweendisplaychange",
    "msbetweenrendercompletes",
)

PowerRunner = Callable[..., Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_hardware_id(value: Any) -> str:
    """Normalize a full PnP ID without weakening it into a vendor-only match."""
    normalized = str(value or "").strip().replace("/", "\\").upper()
    normalized = re.sub(r"\\+", r"\\", normalized)
    if not normalized or ".." in normalized or "*" in normalized:
        return ""
    if not DEVICE_ID_PATTERN.fullmatch(normalized):
        return ""
    return normalized


def hardware_identity(value: Any) -> dict[str, str]:
    """Extract PCI/USB fields while retaining the exact normalized device ID."""
    device_id = normalize_hardware_id(value)
    if not device_id:
        return {}
    fields = {"device_id": device_id, "bus": device_id.split("\\", 1)[0]}
    for key, pattern in (
        ("vendor_id", r"(?:^|[&\\])VEN_([0-9A-F]{4})(?:&|\\|$)"),
        ("device_code", r"(?:^|[&\\])DEV_([0-9A-F]{4})(?:&|\\|$)"),
        ("subsystem_id", r"(?:^|[&\\])SUBSYS_([0-9A-F]{8})(?:&|\\|$)"),
        ("revision", r"(?:^|[&\\])REV_([0-9A-F]{2})(?:&|\\|$)"),
        ("usb_vendor_id", r"(?:^|[&\\])VID_([0-9A-F]{4})(?:&|\\|$)"),
        ("usb_product_id", r"(?:^|[&\\])PID_([0-9A-F]{4})(?:&|\\|$)"),
    ):
        match = re.search(pattern, device_id)
        if match:
            fields[key] = match.group(1)
    return fields


def hardware_fingerprint(devices: Iterable[dict[str, Any]]) -> str:
    """Return a stable hash of exact device IDs and current driver versions."""
    records = []
    for device in devices:
        identity = hardware_identity(device.get("pnp_id") or device.get("device_id"))
        if identity:
            records.append((
                identity["device_id"],
                str(device.get("driver_version") or ""),
                str(device.get("inf_name") or ""),
            ))
    canonical = json.dumps(sorted(records), separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _data_directory() -> Path:
    if os.name == "nt" and os.environ.get("APPDATA"):
        return Path(os.environ["APPDATA"]) / "OPlague" / "gaming"
    if platform.system() == "Darwin":
        return Path.home() / "Library" / "Application Support" / "OPlague" / "gaming"
    root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "oplague" / "gaming"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n",
            prefix=f".{path.name}.", suffix=".tmp",
            dir=path.parent, delete=False,
        ) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path.name}")
    return payload


def _run(command: list[str], runner: PowerRunner | None = None) -> Any:
    execute = runner or subprocess.run
    return execute(
        command, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=20, check=False,
    )


def collect_windows_devices(timeout_seconds: int = 30) -> list[dict[str, Any]]:
    """Read PnP and signed-driver metadata using one fixed, non-interactive query."""
    if os.name != "nt":
        raise RuntimeError("Live Plug and Play inventory is available only on Windows")

    script = (
        "$ErrorActionPreference = 'Stop'; "
        "$drivers = @{}; "
        "Get-CimInstance -ClassName Win32_PnPSignedDriver | ForEach-Object { "
        "$drivers[[string]$_.DeviceID] = $_ }; "
        "$items = @(Get-CimInstance -ClassName Win32_PnPEntity | ForEach-Object { "
        "$d = $drivers[[string]$_.PNPDeviceID]; "
        "[PSCustomObject]@{ "
        "Name = $_.Name; Status = $_.Status; Manufacturer = $_.Manufacturer; "
        "PNPDeviceID = $_.PNPDeviceID; ConfigManagerErrorCode = $_.ConfigManagerErrorCode; "
        "DriverProvider = if ($d) { $d.DriverProviderName } else { $null }; "
        "DriverVersion = if ($d) { $d.DriverVersion } else { $null }; "
        "DriverDate = if ($d) { $d.DriverDate } else { $null }; "
        "InfName = if ($d) { $d.InfName } else { $null }; "
        "IsSigned = if ($d) { [bool]$d.IsSigned } else { $null }; "
        "Signer = if ($d) { $d.Signer } else { $null } "
        "} }); "
        "ConvertTo-Json -InputObject $items -Depth 4 -Compress"
    )
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=timeout_seconds, check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Windows PnP inventory failed")
    output = result.stdout.strip().lstrip("\ufeff")
    if not output:
        return []
    payload = json.loads(output)
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected Windows PnP response")
    devices = []
    for row in payload:
        if not isinstance(row, dict):
            continue
        raw_id = str(row.get("PNPDeviceID") or "")
        identity = hardware_identity(raw_id)
        devices.append({
            "name": str(row.get("Name") or "Unknown device"),
            "status": str(row.get("Status") or "Unknown"),
            "manufacturer": str(row.get("Manufacturer") or ""),
            "pnp_id": identity.get("device_id", ""),
            "hardware_identity": identity,
            "config_manager_error": row.get("ConfigManagerErrorCode"),
            "driver_provider": str(row.get("DriverProvider") or ""),
            "driver_version": str(row.get("DriverVersion") or ""),
            "driver_date": str(row.get("DriverDate") or ""),
            "inf_name": str(row.get("InfName") or ""),
            "is_signed": row.get("IsSigned"),
            "signer": str(row.get("Signer") or ""),
            "trust_note": "Windows CIM metadata only; not an independent signature verdict",
        })
    return devices


def _number_or_none(value: str, *, integer: bool = False) -> int | float | None:
    cleaned = str(value or "").strip()
    if not cleaned or cleaned.casefold() in {"n/a", "na", "not supported", "[not supported]"}:
        return None
    try:
        number = float(cleaned)
    except ValueError:
        return None
    if not math.isfinite(number):
        return None
    return int(number) if integer else number


def collect_nvidia_telemetry(
    runner: PowerRunner | None = None,
) -> dict[str, Any]:
    """Read NVIDIA GPU sensors through nvidia-smi without changing device state."""
    command = shutil.which("nvidia-smi")
    if not command:
        return {
            "provider": "nvidia-smi",
            "captured_at": utc_now(),
            "available": False,
            "reason": "nvidia-smi was not found on PATH",
            "gpus": [],
        }

    fields = (
        "name,driver_version,temperature.gpu,utilization.gpu,memory.used,memory.total,"
        "power.draw,clocks.gr,clocks.mem"
    )
    result = _run(
        [command, f"--query-gpu={fields}", "--format=csv,noheader,nounits"],
        runner,
    )
    if result.returncode:
        return {
            "provider": "nvidia-smi",
            "captured_at": utc_now(),
            "available": False,
            "reason": (result.stderr or "nvidia-smi query failed").strip(),
            "gpus": [],
        }

    gpus = []
    for row in csv.reader(io.StringIO(result.stdout or "")):
        if not row:
            continue
        if len(row) != 9:
            return {
                "provider": "nvidia-smi",
                "captured_at": utc_now(),
                "available": False,
                "reason": f"Unexpected nvidia-smi row width: {len(row)}",
                "gpus": [],
            }
        gpus.append({
            "name": row[0].strip(),
            "driver_version": row[1].strip(),
            "temperature_c": _number_or_none(row[2], integer=True),
            "utilization_pct": _number_or_none(row[3], integer=True),
            "memory_used_mib": _number_or_none(row[4], integer=True),
            "memory_total_mib": _number_or_none(row[5], integer=True),
            "power_w": _number_or_none(row[6]),
            "graphics_clock_mhz": _number_or_none(row[7], integer=True),
            "memory_clock_mhz": _number_or_none(row[8], integer=True),
        })

    return {
        "provider": "nvidia-smi",
        "captured_at": utc_now(),
        "available": bool(gpus),
        "reason": None if gpus else "nvidia-smi returned no GPU rows",
        "gpus": gpus,
    }


def create_gpu_telemetry_snapshot(
    *,
    telemetry: dict[str, Any] | None = None,
    output_path: Path | None = None,
    directory: Path | None = None,
) -> dict[str, Any]:
    """Export one bounded, read-only GPU sensor snapshot for DuckOS/Reaper.

    The exporter preserves unsupported sensors as null. It never reads or writes
    GPU registers and never applies clocks, voltage, fan or power changes.
    """
    if output_path is not None and directory is not None:
        raise ValueError("Pass output_path or directory, not both")

    source = telemetry if telemetry is not None else collect_nvidia_telemetry()
    if not isinstance(source, dict) or source.get("provider") != "nvidia-smi":
        raise ValueError("GPU telemetry must come from the read-only nvidia-smi provider")

    captured_at = source.get("captured_at")
    if not isinstance(captured_at, str) or not captured_at.strip():
        captured_at = utc_now()

    raw_gpus = source.get("gpus")
    if not isinstance(raw_gpus, list) or len(raw_gpus) > 16:
        raise ValueError("GPU telemetry must contain at most 16 device records")

    normalized_gpus: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_gpus):
        if not isinstance(raw, dict):
            raise ValueError(f"GPU telemetry row {index} must be an object")
        name = str(raw.get("name") or "").strip()
        driver_version = str(raw.get("driver_version") or "").strip()
        if not name or len(name) > 256 or not driver_version or len(driver_version) > 128:
            raise ValueError(f"GPU telemetry row {index} has invalid device identity")

        values: dict[str, int | float | None] = {
            "temperature_c": _number_or_none(raw.get("temperature_c"), integer=True),
            "utilization_pct": _number_or_none(raw.get("utilization_pct"), integer=True),
            "memory_used_mib": _number_or_none(raw.get("memory_used_mib"), integer=True),
            "memory_total_mib": _number_or_none(raw.get("memory_total_mib"), integer=True),
            "power_w": _number_or_none(raw.get("power_w")),
            "graphics_clock_mhz": _number_or_none(raw.get("graphics_clock_mhz"), integer=True),
            "memory_clock_mhz": _number_or_none(raw.get("memory_clock_mhz"), integer=True),
        }
        bounds = {
            "temperature_c": (-20, 150),
            "utilization_pct": (0, 100),
            "memory_used_mib": (0, 2**31 - 1),
            "memory_total_mib": (1, 2**31 - 1),
            "power_w": (0, 10000),
            "graphics_clock_mhz": (0, 20000),
            "memory_clock_mhz": (0, 20000),
        }
        for field, value in values.items():
            lower, upper = bounds[field]
            if value is not None and not lower <= value <= upper:
                raise ValueError(f"GPU telemetry row {index} has out-of-range {field}")
        used = values["memory_used_mib"]
        total = values["memory_total_mib"]
        if used is not None and total is not None and used > total:
            raise ValueError(f"GPU telemetry row {index} reports memory use above total")

        normalized_gpus.append({
            "name": name,
            "driver_version": driver_version,
            **values,
        })

    available = bool(source.get("available")) and bool(normalized_gpus)
    if not available and normalized_gpus:
        raise ValueError("Unavailable telemetry cannot contain GPU samples")
    reason = source.get("reason")
    if not available and not isinstance(reason, str):
        reason = "GPU telemetry provider returned no usable readings"

    payload: dict[str, Any] = {
        "schema": "oplage.gpu-telemetry.v1",
        "snapshot_id": str(uuid.uuid4()),
        "captured_at": captured_at,
        "source": {"provider": "nvidia-smi", "mode": "read_only"},
        "available": available,
        "reason": reason if not available else None,
        "controls_performed": False,
        "gpus": normalized_gpus,
    }
    canonical = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    payload["snapshot_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    if output_path is not None:
        path = Path(output_path)
    else:
        folder = directory or (_data_directory() / "gpu-telemetry")
        path = folder / f"{payload['snapshot_id']}.json"
    _atomic_write_json(path, payload)
    payload["snapshot_path"] = str(path)
    return payload



def collect_windows_reliability_events(
    hours: int = 24,
    *,
    runner: PowerRunner | None = None,
) -> dict[str, Any]:
    """Read recent WHEA and Windows display-driver reset events, when available."""
    if not isinstance(hours, int) or isinstance(hours, bool) or not 1 <= hours <= 168:
        raise ValueError("Event lookback must be between 1 and 168 hours")
    if os.name != "nt":
        return {
            "provider": "Windows System event log",
            "captured_at": utc_now(),
            "available": False,
            "reason": "Windows event logs are only available on Windows",
            "events": [],
        }

    script = (
        "$ErrorActionPreference = 'SilentlyContinue'; "
        f"$since = (Get-Date).AddHours(-{hours}); "
        "$items = @(Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$since} "
        "-MaxEvents 2000 -ErrorAction SilentlyContinue | "
        "Where-Object { $_.ProviderName -eq 'Microsoft-Windows-WHEA-Logger' -or "
        "($_.ProviderName -eq 'Display' -and $_.Id -eq 4101) } | "
        "Select-Object -First 100 @{Name='TimeCreated';Expression={$_.TimeCreated.ToUniversalTime().ToString('o')}}, "
        "ProviderName, Id, LevelDisplayName, Message); "
        "ConvertTo-Json -InputObject $items -Depth 3 -Compress"
    )
    result = _run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        runner,
    )
    if result.returncode:
        return {
            "provider": "Windows System event log",
            "captured_at": utc_now(),
            "available": False,
            "reason": (result.stderr or "Could not read Windows System event log").strip(),
            "events": [],
        }

    output = (result.stdout or "").strip().lstrip("\ufeff")
    if not output or output.casefold() == "null":
        events = []
    else:
        payload = json.loads(output)
        events = [payload] if isinstance(payload, dict) else payload
        if not isinstance(events, list):
            raise RuntimeError("Unexpected Windows event-log response")
    return {
        "provider": "Windows System event log",
        "captured_at": utc_now(),
        "available": True,
        "lookback_hours": hours,
        "event_count": len(events),
        "events": [
            {
                "time_created": str(event.get("TimeCreated") or ""),
                "provider": str(event.get("ProviderName") or ""),
                "event_id": event.get("Id"),
                "level": str(event.get("LevelDisplayName") or ""),
                "message": str(event.get("Message") or "")[:2000],
            }
            for event in events if isinstance(event, dict)
        ],
        "event_types": ["Microsoft-Windows-WHEA-Logger", "Display/4101"],
    }


def active_power_scheme(runner: PowerRunner | None = None) -> dict[str, str]:
    """Read the active power scheme; no settings are changed."""
    if os.name != "nt":
        raise RuntimeError("Power-plan control is available only on Windows")
    result = _run(["powercfg.exe", "/getactivescheme"], runner)
    if result.returncode:
        raise RuntimeError((result.stderr or "").strip() or "Unable to read active power scheme")
    match = re.search(
        r"([0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12})",
        result.stdout or "",
    )
    if not match:
        raise RuntimeError("Windows returned an unrecognized active power-scheme response")
    return {"guid": match.group(1).lower(), "description": (result.stdout or "").strip()}


def set_active_power_scheme(guid: str, runner: PowerRunner | None = None) -> None:
    """Activate only a validated, existing power-scheme GUID."""
    if os.name != "nt":
        raise RuntimeError("Power-plan control is available only on Windows")
    if not GUID_PATTERN.fullmatch(str(guid or "")):
        raise ValueError("Invalid power-scheme GUID")
    result = _run(["powercfg.exe", "/setactive", guid], runner)
    if result.returncode:
        raise RuntimeError((result.stderr or "").strip() or "Windows could not activate the power scheme")


def _snapshot_payload(
    devices: list[dict[str, Any]],
    power_scheme: dict[str, str] | None,
    telemetry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    safe_devices = []
    for device in devices:
        if not isinstance(device, dict):
            continue
        identity = hardware_identity(device.get("pnp_id") or device.get("device_id"))
        safe_devices.append({
            "name": str(device.get("name") or "Unknown device"),
            "manufacturer": str(device.get("manufacturer") or ""),
            "pnp_id": identity.get("device_id", ""),
            "hardware_identity": identity,
            "driver_provider": str(device.get("driver_provider") or ""),
            "driver_version": str(device.get("driver_version") or ""),
            "driver_date": str(device.get("driver_date") or ""),
            "inf_name": str(device.get("inf_name") or ""),
            "is_signed": device.get("is_signed"),
            "signer": str(device.get("signer") or ""),
        })
    return {
        "schema": SCHEMA_VERSION,
        "snapshot_id": str(uuid.uuid4()),
        "created_at": utc_now(),
        "host": {"system": platform.system(), "release": platform.release(), "architecture": platform.machine()},
        "hardware_fingerprint": hardware_fingerprint(safe_devices),
        "active_power_scheme": power_scheme,
        "telemetry": telemetry,
        "devices": safe_devices,
        "scope": "Configuration and driver metadata only; no SYS/INF payload copy or system write",
    }


def create_snapshot(
    *,
    devices: list[dict[str, Any]] | None = None,
    power_scheme: dict[str, str] | None = None,
    telemetry: dict[str, Any] | None = None,
    directory: Path | None = None,
) -> dict[str, Any]:
    """Capture an atomic local baseline before a game session or tuning action."""
    if devices is None:
        devices = collect_windows_devices() if os.name == "nt" else []
    if power_scheme is None and os.name == "nt":
        power_scheme = active_power_scheme()
    payload = _snapshot_payload(devices, power_scheme, telemetry)
    folder = directory or (_data_directory() / "snapshots")
    path = folder / f"{payload['snapshot_id']}.json"
    _atomic_write_json(path, payload)
    payload["snapshot_path"] = str(path)
    return payload


def _session_path(directory: Path | None = None) -> Path:
    return (directory or _data_directory()) / "active-session.json"


def start_game_session(
    game_name: str,
    *,
    power_mode: str = "performance",
    directory: Path | None = None,
    runner: PowerRunner | None = None,
    device_reader: Callable[[], list[dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Snapshot first, then optionally switch to a built-in Windows power plan."""
    cleaned_name = str(game_name or "").strip()
    if not cleaned_name or len(cleaned_name) > 128:
        raise ValueError("Game name must contain between 1 and 128 characters")
    if power_mode not in {"performance", "balanced", "none"}:
        raise ValueError("Power mode must be performance, balanced or none")
    if os.name != "nt":
        raise RuntimeError("Temporary power profiles are currently supported only on Windows")

    session_file = _session_path(directory)
    if session_file.is_file():
        existing = _read_json(session_file)
        if existing.get("schema") == SCHEMA_VERSION and existing.get("status") in {"active", "starting"}:
            raise RuntimeError("An OPlague game session is already active. Restore it before starting another one.")

    devices = (device_reader or collect_windows_devices)()
    previous = active_power_scheme(runner)
    telemetry = {
        "gpu": collect_nvidia_telemetry(runner),
        "reliability_events": collect_windows_reliability_events(runner=runner),
    }
    snapshot = create_snapshot(
        devices=devices, power_scheme=previous, telemetry=telemetry,
        directory=(directory or _data_directory()) / "snapshots",
    )
    target = {
        "performance": "SCHEME_MIN",
        "balanced": "SCHEME_BALANCED",
        "none": previous["guid"],
    }[power_mode]
    session = {
        "schema": SCHEMA_VERSION,
        "session_id": str(uuid.uuid4()),
        "game_name": cleaned_name,
        "started_at": utc_now(),
        "snapshot_id": snapshot["snapshot_id"],
        "snapshot_path": snapshot["snapshot_path"],
        "previous_power_scheme": previous,
        "applied_power_scheme_guid": previous["guid"],
        "power_mode": power_mode,
        "status": "starting",
        "restore_policy": "Restore only if the active plan is still the one this session applied",
    }
    _atomic_write_json(session_file, session)

    changed_power_plan = False
    try:
        if target != previous["guid"] and power_mode != "none":
            result = _run(["powercfg.exe", "/setactive", target], runner)
            if result.returncode:
                raise RuntimeError((result.stderr or "").strip() or "Could not activate the requested built-in power plan")
            changed_power_plan = True
            applied = active_power_scheme(runner)
            session["applied_power_scheme_guid"] = applied["guid"]
        session["status"] = "active"
        _atomic_write_json(session_file, session)
        return session
    except Exception as error:
        rollback_note = "No power-plan change needed."
        if changed_power_plan:
            try:
                current = active_power_scheme(runner)
                if current["guid"].casefold() == session["applied_power_scheme_guid"].casefold():
                    set_active_power_scheme(previous["guid"], runner)
                    rollback_note = "The previous power plan was restored after session startup failed."
                else:
                    rollback_note = "The active plan changed externally; it was left untouched."
            except Exception as rollback_error:
                rollback_note = f"Automatic startup rollback failed: {rollback_error}"
        session["status"] = "start_failed"
        session["finished_at"] = utc_now()
        session["restore_note"] = rollback_note
        try:
            _atomic_write_json(session_file, session)
        except OSError:
            pass
        raise RuntimeError(f"{error}. {rollback_note}") from error


def restore_game_session(
    *,
    directory: Path | None = None,
    runner: PowerRunner | None = None,
) -> dict[str, Any]:
    """Restore the pre-session plan without overwriting a later user choice."""
    path = _session_path(directory)
    if not path.is_file():
        raise FileNotFoundError("No OPlague game session is available to restore")
    session = _read_json(path)
    if session.get("schema") != SCHEMA_VERSION or session.get("status") not in {"active", "starting"}:
        raise ValueError("The saved game session is not active or has an unsupported schema")
    previous = session.get("previous_power_scheme") or {}
    previous_guid = str(previous.get("guid") or "")
    applied_guid = str(session.get("applied_power_scheme_guid") or "")
    current = active_power_scheme(runner)
    if session.get("status") == "starting":
        # The process may have stopped between switching the plan and recording
        # the resulting GUID. Never guess whether a different plan is ours.
        session["finished_at"] = utc_now()
        if current["guid"].casefold() == previous_guid.casefold():
            session["status"] = "restored"
            session["restore_note"] = "Startup did not complete; the original plan was still active."
            _atomic_write_json(path, session)
            return {"restored": True, "session": session}
        session["status"] = "restore_skipped_external_change"
        session["restore_note"] = "Startup ended before the applied plan GUID was recorded. The active plan was left untouched for safety."
        _atomic_write_json(path, session)
        return {"restored": False, "reason": "incomplete_startup", "session": session}
    if current["guid"].casefold() != applied_guid.casefold():
        session["status"] = "restore_skipped_external_change"
        session["finished_at"] = utc_now()
        session["restore_note"] = "The active power plan changed outside this session; it was left untouched."
        _atomic_write_json(path, session)
        return {"restored": False, "reason": "external_power_plan_change", "session": session}
    if previous_guid and current["guid"].casefold() != previous_guid.casefold():
        set_active_power_scheme(previous_guid, runner)
    session["status"] = "restored"
    session["finished_at"] = utc_now()
    session["restore_note"] = "The power plan captured before the session was restored."
    _atomic_write_json(path, session)
    return {"restored": True, "session": session}


def _normalized_column(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name or "").casefold())


def summarize_frametime_csv(filename: str | Path, *, max_rows: int = 2_000_000) -> dict[str, Any]:
    """Summarize frame-time CSV exported by PresentMon or a compatible tool."""
    path = Path(filename).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Benchmark file not found: {path}")
    samples: list[float] = []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError("Benchmark CSV has no header row")
        columns = {_normalized_column(name): name for name in reader.fieldnames}
        selected = next((columns[name] for name in FRAME_TIME_COLUMNS if name in columns), None)
        if selected is None:
            raise ValueError(
                "No supported frametime column found. Expected MsBetweenPresents, "
                "MsBetweenDisplayChange, MsBetweenRenderCompletes or FrameTime."
            )
        for row_number, row in enumerate(reader, start=1):
            if row_number > max_rows:
                raise ValueError(f"Benchmark exceeds the {max_rows:,}-row safety limit")
            raw = str(row.get(selected) or "").strip()
            if not raw:
                continue
            try:
                value = float(raw)
            except ValueError:
                continue
            if math.isfinite(value) and 0.05 <= value <= 10_000:
                samples.append(value)
    if not samples:
        raise ValueError("Benchmark CSV contains no valid frame-time samples")
    ordered = sorted(samples)
    worst_one = ordered[-max(1, math.ceil(len(ordered) * 0.01)):]
    # A 0.1% low from fewer than 1,000 frames would overstate a single frame as
    # a percentile. Leave it unavailable until the sample actually supports it.
    worst_point_one = ordered[-max(1, math.ceil(len(ordered) * 0.001)):] if len(ordered) >= 1000 else []
    mean = sum(samples) / len(samples)

    def average(values: list[float]) -> float:
        return sum(values) / len(values)

    def low_fps(values: list[float]) -> float:
        return 1000.0 / average(values)

    p99_index = min(len(ordered) - 1, math.ceil(len(ordered) * 0.99) - 1)
    return {
        "source": path.name,
        "sample_count": len(samples),
        "mean_frametime_ms": round(mean, 4),
        "median_frametime_ms": round((ordered[(len(ordered) - 1) // 2] + ordered[len(ordered) // 2]) / 2, 4),
        "p99_frametime_ms": round(ordered[p99_index], 4),
        "average_fps": round(1000.0 / mean, 2),
        "one_percent_low_fps": round(low_fps(worst_one), 2),
        "point_one_percent_low_fps": round(low_fps(worst_point_one), 2) if worst_point_one else None,
        "metric_definition": "1% and 0.1% lows are the inverse mean frametime of the slowest 1% and 0.1% of frames",
    }


def compare_benchmarks(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    *,
    one_percent_drop: float = 5.0,
    point_one_drop: float = 7.0,
    p99_increase: float = 8.0,
) -> dict[str, Any]:
    """Flag regressions for operator review/rollback."""
    required = ("one_percent_low_fps", "point_one_percent_low_fps", "p99_frametime_ms")
    if any(key not in baseline or key not in candidate for key in required):
        raise ValueError("Both benchmark summaries must contain 1%/0.1% lows and p99 frametime")
    one_base = float(baseline["one_percent_low_fps"])
    one_new = float(candidate["one_percent_low_fps"])
    point_base_raw = baseline.get("point_one_percent_low_fps")
    point_new_raw = candidate.get("point_one_percent_low_fps")
    point_available = point_base_raw is not None and point_new_raw is not None
    point_base = float(point_base_raw) if point_available else 0.0
    point_new = float(point_new_raw) if point_available else 0.0
    p99_base = float(baseline["p99_frametime_ms"])
    p99_new = float(candidate["p99_frametime_ms"])
    one_drop = max(0.0, (one_base - one_new) / one_base * 100) if one_base > 0 else 0.0
    point_drop = max(0.0, (point_base - point_new) / point_base * 100) if point_available and point_base > 0 else None
    p99_rise = max(0.0, (p99_new - p99_base) / p99_base * 100) if p99_base > 0 else 0.0
    triggers = []
    if one_drop >= one_percent_drop:
        triggers.append("1% low dropped beyond threshold")
    if point_drop is not None and point_drop >= point_one_drop:
        triggers.append("0.1% low dropped beyond threshold")
    if p99_rise >= p99_increase:
        triggers.append("p99 frametime increased beyond threshold")
    return {
        "regression_detected": bool(triggers),
        "one_percent_low_drop_pct": round(one_drop, 2),
        "point_one_percent_low_drop_pct": round(point_drop, 2) if point_drop is not None else None,
        "point_one_percent_low_available": point_available,
        "p99_frametime_increase_pct": round(p99_rise, 2),
        "thresholds_pct": {
            "one_percent_low_drop": one_percent_drop,
            "point_one_percent_low_drop": point_one_drop,
            "p99_frametime_increase": p99_increase,
        },
        "reasons": triggers,
        "recommendation": (
            "Stop the current game session and restore its power plan, then repeat the same benchmark."
            if triggers else
            "No threshold regression detected; this does not prove a performance improvement."
        ),
        "automatic_rollback": False,
    }


def save_game_profile(
    *,
    game_id: str,
    game_name: str,
    hardware_hash: str,
    driver_version: str,
    settings: dict[str, Any],
    validated: bool = False,
    path: Path | None = None,
) -> dict[str, Any]:
    """Persist only operator-confirmed profiles for an exact hardware/driver/game tuple."""
    if not validated:
        raise ValueError("A profile can be cached only after an operator confirms a repeatable benchmark")
    values = (game_id, game_name, hardware_hash, driver_version)
    if any(not str(item or "").strip() for item in values):
        raise ValueError("Game, hardware fingerprint and driver version are required")
    if len(game_id) > 256 or len(game_name) > 128 or len(driver_version) > 128:
        raise ValueError("Profile identity fields exceed their size limits")
    if len(hardware_hash) != 64 or not re.fullmatch(r"[0-9a-fA-F]{64}", hardware_hash):
        raise ValueError("Hardware fingerprint must be a SHA-256 hex string")
    profile_key = hashlib.sha256(
        "|".join((game_id.casefold(), hardware_hash.casefold(), driver_version.casefold())).encode("utf-8")
    ).hexdigest()
    target = path or (_data_directory() / "profiles.json")
    payload = {"schema": SCHEMA_VERSION, "profiles": {}}
    if target.is_file():
        loaded = _read_json(target)
        if loaded.get("schema") != SCHEMA_VERSION or not isinstance(loaded.get("profiles"), dict):
            raise ValueError("Unsupported or malformed game profile cache")
        payload = loaded
    payload["profiles"][profile_key] = {
        "game_id": game_id,
        "game_name": game_name,
        "hardware_fingerprint": hardware_hash.lower(),
        "driver_version": driver_version,
        "settings": settings,
        "validated_at": utc_now(),
        "validation": "operator_confirmed",
    }
    ordered = sorted(
        payload["profiles"].items(),
        key=lambda item: str(item[1].get("validated_at", "")),
        reverse=True,
    )[:250]
    payload["profiles"] = dict(ordered)
    _atomic_write_json(target, payload)
    return {"profile_key": profile_key, "profile": payload["profiles"][profile_key], "cache_path": str(target)}


def find_game_profile(
    *,
    game_id: str,
    hardware_hash: str,
    driver_version: str,
    path: Path | None = None,
) -> dict[str, Any] | None:
    target = path or (_data_directory() / "profiles.json")
    if not target.is_file():
        return None
    payload = _read_json(target)
    if payload.get("schema") != SCHEMA_VERSION or not isinstance(payload.get("profiles"), dict):
        raise ValueError("Unsupported or malformed game profile cache")
    key = hashlib.sha256(
        "|".join((game_id.casefold(), hardware_hash.casefold(), driver_version.casefold())).encode("utf-8")
    ).hexdigest()
    return payload["profiles"].get(key)
