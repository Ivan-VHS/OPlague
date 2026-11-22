"""Read-only Authenticode inspection for local Windows driver artifacts.

The module asks Windows to verify signatures of selected files. It never
installs, extracts, loads, modifies, or executes the inspected artifacts.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Callable, Sequence

MAX_FILES = 128
MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
SUPPORTED_SUFFIXES = {".cat", ".sys", ".dll", ".exe", ".efi"}

_POWERSHELL_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
$results = @(
    foreach ($candidate in @($payload.paths)) {
        $file = Get-Item -LiteralPath ([string]$candidate) -Force -ErrorAction Stop
        if ($file.PSIsContainer) { throw "Not a regular file: $candidate" }
        $signature = Get-AuthenticodeSignature -FilePath $file.FullName
        $signer = $signature.SignerCertificate
        $timestamp = $signature.TimeStamperCertificate
        [pscustomobject]@{
            path = $file.FullName
            status = [string]$signature.Status
            status_message = [string]$signature.StatusMessage
            signer_subject = if ($signer) { [string]$signer.Subject } else { $null }
            signer_issuer = if ($signer) { [string]$signer.Issuer } else { $null }
            signer_thumbprint = if ($signer) { [string]$signer.Thumbprint } else { $null }
            timestamp_subject = if ($timestamp) { [string]$timestamp.Subject } else { $null }
        }
    }
)
[pscustomobject]@{
    schema = 'oplage.authenticode-audit.v1'
    results = @($results)
} | ConvertTo-Json -Depth 5 -Compress
"""


class AuthenticodeAuditError(RuntimeError):
    """The local operating system could not complete signature inspection."""


def _preflight(paths: Sequence[str | Path]) -> list[Path]:
    if not isinstance(paths, (list, tuple)) or not paths:
        raise ValueError("select at least one file for signature inspection")
    if len(paths) > MAX_FILES:
        raise ValueError(f"select no more than {MAX_FILES} files")

    selected: list[Path] = []
    seen: set[Path] = set()
    total_bytes = 0
    for value in paths:
        path = Path(value).expanduser()
        if path.is_symlink():
            raise ValueError(f"symbolic-link paths are not allowed: {path}")
        if path.suffix.casefold() not in SUPPORTED_SUFFIXES:
            raise ValueError(f"unsupported Authenticode file type: {path.suffix or '<none>'}")
        if not path.is_file():
            raise FileNotFoundError(f"not a regular file: {path}")
        resolved = path.resolve(strict=True)
        if resolved in seen:
            raise ValueError(f"duplicate file selected: {path}")
        seen.add(resolved)
        size = resolved.stat().st_size
        if size > MAX_FILE_BYTES:
            raise ValueError(f"file exceeds the {MAX_FILE_BYTES}-byte limit: {path.name}")
        total_bytes += size
        if total_bytes > MAX_TOTAL_BYTES:
            raise ValueError("selected files exceed the aggregate byte limit")
        selected.append(resolved)
    return selected


def inspect_authenticode_files(
    paths: Sequence[str | Path],
    *,
    runner: Callable[..., Any] = subprocess.run,
    platform_name: str = os.name,
    timeout_seconds: int = 45,
) -> dict[str, Any]:
    """Return OS signature status for selected files without changing the system."""
    if platform_name != "nt":
        raise AuthenticodeAuditError(
            "Authenticode inspection requires Windows PowerShell and is unavailable on this platform"
        )
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 300:
        raise ValueError("timeout_seconds must be between 1 and 300")
    selected = _preflight(paths)
    payload = json.dumps({"paths": [str(path) for path in selected]}, ensure_ascii=False)
    try:
        completed = runner(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", _POWERSHELL_SCRIPT],
            input=payload,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise AuthenticodeAuditError("Windows signature inspection timed out") from error
    except OSError as error:
        raise AuthenticodeAuditError(f"could not start Windows PowerShell: {error}") from error

    if completed.returncode != 0:
        detail = (completed.stderr or "").strip() or f"PowerShell exited with code {completed.returncode}"
        raise AuthenticodeAuditError(detail)
    try:
        response = json.loads(completed.stdout.lstrip("\ufeff"))
    except (TypeError, json.JSONDecodeError) as error:
        raise AuthenticodeAuditError("PowerShell returned invalid signature audit JSON") from error
    if not isinstance(response, dict) or response.get("schema") != "oplage.authenticode-audit.v1":
        raise AuthenticodeAuditError("PowerShell returned an unexpected signature audit schema")
    rows = response.get("results")
    if not isinstance(rows, list) or len(rows) != len(selected):
        raise AuthenticodeAuditError("PowerShell returned an incomplete signature audit")
    normalized = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not isinstance(row.get("status"), str):
            raise AuthenticodeAuditError(f"invalid signature result at index {index}")
        normalized.append({
            "path": str(row.get("path") or selected[index]),
            "status": row["status"],
            "status_message": str(row.get("status_message") or ""),
            "signer_subject": row.get("signer_subject"),
            "signer_issuer": row.get("signer_issuer"),
            "signer_thumbprint": row.get("signer_thumbprint"),
            "timestamp_subject": row.get("timestamp_subject"),
        })

    counts: dict[str, int] = {}
    for row in normalized:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {
        "schema": "oplage.authenticode-audit.v1",
        "mode": "read_only",
        "platform": "Windows Authenticode",
        "installation_attempted": False,
        "system_modified": False,
        "results": normalized,
        "summary": {"files": len(normalized), "statuses": dict(sorted(counts.items()))},
        "semantics": (
            "Reports the local Windows trust-provider status at inspection time. "
            "A valid signature is not a driver compatibility, quality, or safety verdict."
        ),
    }
