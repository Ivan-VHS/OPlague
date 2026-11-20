"""Read-only Windows Plug and Play inventory adapter with normalized properties."""
from __future__ import annotations

import json
import os
import subprocess
from typing import Any

MAX_DEVICES = 100_000
MAX_IDS_PER_DEVICE = 512

# Fixed PowerShell source: no user-provided text is interpolated or executed.
_POWERSHELL_QUERY = r"""
$ErrorActionPreference = 'Stop'
$keys = @(
  'DEVPKEY_Device_HardwareIds', 'DEVPKEY_Device_CompatibleIds',
  'DEVPKEY_Device_Manufacturer', 'DEVPKEY_Device_ClassGuid',
  'DEVPKEY_Device_Parent', 'DEVPKEY_Device_Service',
  'DEVPKEY_Device_DriverVersion', 'DEVPKEY_Device_DriverDate',
  'DEVPKEY_Device_DriverProvider'
)
$devices = @(Get-PnpDevice | ForEach-Object {
  $device = $_
  $properties = @{}
  foreach ($key in $keys) {
    try {
      $property = Get-PnpDeviceProperty -InstanceId $device.InstanceId -KeyName $key -ErrorAction Stop
      $properties[$key] = $property.Data
    } catch { }
  }
  [pscustomobject]@{
    name = [string]$device.FriendlyName
    status = [string]$device.Status
    class = [string]$device.Class
    class_guid = [string]$properties['DEVPKEY_Device_ClassGuid']
    manufacturer = [string]$properties['DEVPKEY_Device_Manufacturer']
    instance_id = [string]$device.InstanceId
    problem_code = $device.Problem
    present = [bool]$device.Present
    hardware_ids = @($properties['DEVPKEY_Device_HardwareIds'])
    compatible_ids = @($properties['DEVPKEY_Device_CompatibleIds'])
    parent_instance_id = [string]$properties['DEVPKEY_Device_Parent']
    service = [string]$properties['DEVPKEY_Device_Service']
    driver_version = [string]$properties['DEVPKEY_Device_DriverVersion']
    driver_date = [string]$properties['DEVPKEY_Device_DriverDate']
    driver_provider = [string]$properties['DEVPKEY_Device_DriverProvider']
  }
})
ConvertTo-Json -InputObject $devices -Depth 6 -Compress
"""


def _as_strings(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, (list, tuple)) else [value]
    if len(values) > MAX_IDS_PER_DEVICE:
        raise ValueError(f"{field} contains too many values")
    result = []
    for item in values:
        if item is None:
            continue
        text = str(item).strip()
        if text:
            if len(text) > 4096:
                raise ValueError(f"{field} contains an overlong value")
            result.append(text)
    return result


def normalize_pnp_devices(payload: Any) -> list[dict[str, Any]]:
    """Normalize PowerShell JSON output; safe for synthetic fixtures on any OS."""
    if isinstance(payload, dict):
        rows = [payload]
    elif isinstance(payload, list):
        rows = payload
    else:
        raise ValueError("PnP inventory response must be an object or array")
    if len(rows) > MAX_DEVICES:
        raise ValueError("PnP inventory exceeds the device limit")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"PnP inventory entry {index} is not an object")
        instance_id = str(row.get("instance_id") or row.get("pnp_id") or "").strip()
        if not instance_id:
            instance_id = ""
        key = instance_id.casefold()
        if key and key in seen:
            raise ValueError(f"duplicate PnP instance ID: {instance_id}")
        if key:
            seen.add(key)
        problem = row.get("problem_code")
        if isinstance(problem, bool):
            problem = None
        elif problem is not None:
            try:
                problem = int(problem)
            except (TypeError, ValueError):
                problem = None
        result.append({
            "name": str(row.get("name") or "Unknown device")[:1024],
            "status": str(row.get("status") or "Unknown")[:128],
            "manufacturer": str(row.get("manufacturer") or "")[:512],
            "class": str(row.get("class") or "")[:256],
            "class_guid": str(row.get("class_guid") or "")[:128],
            "instance_id": instance_id[:2048],
            "pnp_id": instance_id[:2048],
            "problem_code": problem,
            "present": bool(row.get("present", True)),
            "hardware_ids": _as_strings(row.get("hardware_ids"), "hardware_ids"),
            "compatible_ids": _as_strings(row.get("compatible_ids"), "compatible_ids"),
            "parent_instance_id": str(row.get("parent_instance_id") or "")[:2048],
            "service": str(row.get("service") or "")[:512],
            "driver_version": str(row.get("driver_version") or "")[:128],
            "driver_date": str(row.get("driver_date") or "")[:128],
            "driver_provider": str(row.get("driver_provider") or "")[:512],
        })
    return result


def query_windows_pnp_devices(timeout_seconds: int = 45) -> list[dict[str, Any]]:
    """Query local PnP properties using a fixed, read-only PowerShell command."""
    if os.name != "nt":
        raise RuntimeError("Hardware inventory is currently available only on Windows")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 300:
        raise ValueError("timeout_seconds must be an integer in 1..300")
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", _POWERSHELL_QUERY],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout_seconds, check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Windows PnP query failed")
    output = result.stdout.strip().lstrip("\ufeff")
    if not output:
        return []
    try:
        payload = json.loads(output)
    except json.JSONDecodeError as error:
        raise RuntimeError(f"Windows PnP query returned invalid JSON: {error}") from error
    return normalize_pnp_devices(payload)
