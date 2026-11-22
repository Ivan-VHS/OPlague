"""Read-only Windows Authenticode inspection for local driver-related files.

The helper asks Windows PowerShell for the platform's signature verdict. It
never installs, loads, extracts, modifies, or sends the inspected file anywhere.
"""
from __future__ import annotations

import json
from pathlib import Path
import platform
import subprocess
from typing import Any, Iterable

SCHEMA = "oplague.authenticode-report.v1"
SUPPORTED_SUFFIXES = {".cat", ".sys", ".dll", ".exe"}
MAX_FILES = 100
MAX_PATH_LENGTH = 4096

# Paths are supplied as JSON on stdin. They are never interpolated into script
# source or shell arguments, which avoids quoting and command-injection issues.
_POWERSHELL_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$paths = [Console]::In.ReadToEnd() | ConvertFrom-Json
$results = @(
    foreach ($path in $paths) {
        try {
            $signature = Get-AuthenticodeSignature -LiteralPath ([string]$path)
            $signer = $signature.SignerCertificate
            $timestamp = $signature.TimeStamperCertificate
            [pscustomobject]@{
                path = [string]$path
                status = [string]$signature.Status
                status_message = [string]$signature.StatusMessage
                signer_subject = if ($signer) { [string]$signer.Subject } else { $null }
                signer_issuer = if ($signer) { [string]$signer.Issuer } else { $null }
                signer_thumbprint = if ($signer) { [string]$signer.Thumbprint } else { $null }
                signer_not_before = if ($signer) { $signer.NotBefore.ToUniversalTime().ToString('o') } else { $null }
                signer_not_after = if ($signer) { $signer.NotAfter.ToUniversalTime().ToString('o') } else { $null }
                timestamp_subject = if ($timestamp) { [string]$timestamp.Subject } else { $null }
            }
        }
        catch {
            [pscustomobject]@{
                path = [string]$path
                status = 'InspectionError'
                status_message = [string]$_.Exception.Message
                signer_subject = $null
                signer_issuer = $null
                signer_thumbprint = $null
                signer_not_before = $null
                signer_not_after = $null
                timestamp_subject = $null
            }
        }
    }
)
ConvertTo-Json -InputObject $results -Depth 4 -Compress
"""


class AuthenticodeError(ValueError):
    """Raised when local signature inspection cannot be completed."""


def _validated_paths(paths: Iterable[str | Path]) -> list[str]:
    if isinstance(paths, (str, bytes, Path)):
        raise AuthenticodeError("provide a sequence of file paths, not one path string")
    try:
        supplied = list(paths)
    except TypeError as error:
        raise AuthenticodeError("file paths must be supplied as a sequence") from error
    if not supplied or len(supplied) > MAX_FILES:
        raise AuthenticodeError(f"select between 1 and {MAX_FILES} files")

    validated = []
    for item in supplied:
        if not isinstance(item, (str, Path)):
            raise AuthenticodeError("each file path must be text or a Path")
        path = Path(item).expanduser()
        if len(str(path)) > MAX_PATH_LENGTH:
            raise AuthenticodeError("a file path exceeds the supported length")
        if path.suffix.casefold() not in SUPPORTED_SUFFIXES:
            raise AuthenticodeError(
                f"unsupported file type {path.suffix or '(no extension)'}: {path.name}"
            )
        if not path.is_file():
            raise AuthenticodeError(f"file does not exist or is not a regular file: {path}")
        validated.append(str(path.resolve()))
    return validated


def inspect_signatures(paths: Iterable[str | Path], timeout_seconds: int = 45) -> dict[str, Any]:
    """Return local Authenticode signature metadata for selected Windows files."""
    validated = _validated_paths(paths)
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 300:
        raise AuthenticodeError("timeout must be an integer between 1 and 300 seconds")
    if platform.system() != "Windows":
        raise NotImplementedError("Authenticode inspection is available only on Windows")

    try:
        completed = subprocess.run(
            [
                "powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "RemoteSigned", "-Command", _POWERSHELL_SCRIPT,
            ],
            input=json.dumps(validated, ensure_ascii=False),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise AuthenticodeError(f"Windows signature query failed: {error}") from error
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise AuthenticodeError(detail or "Windows PowerShell could not inspect signatures")

    try:
        decoded = json.loads(completed.stdout.lstrip("\ufeff"))
    except json.JSONDecodeError as error:
        raise AuthenticodeError("PowerShell returned invalid JSON for signature results") from error

    if isinstance(decoded, dict):
        records = [decoded]
    elif isinstance(decoded, list):
        records = decoded
    else:
        raise AuthenticodeError("PowerShell returned an unexpected signature result")
    if len(records) != len(validated) or not all(isinstance(item, dict) for item in records):
        raise AuthenticodeError("PowerShell returned an incomplete signature result")

    normalized = []
    for item in records:
        status = str(item.get("status") or "Unknown")
        normalized.append({
            "path": str(item.get("path") or ""),
            "status": status,
            "status_message": str(item.get("status_message") or ""),
            "signer_subject": item.get("signer_subject"),
            "signer_issuer": item.get("signer_issuer"),
            "signer_thumbprint": item.get("signer_thumbprint"),
            "signer_not_before": item.get("signer_not_before"),
            "signer_not_after": item.get("signer_not_after"),
            "timestamp_subject": item.get("timestamp_subject"),
        })

    return {
        "schema": SCHEMA,
        "read_only": True,
        "source": "Windows Get-AuthenticodeSignature",
        "files_inspected": len(normalized),
        "results": normalized,
        "interpretation": (
            "The status is Windows' Authenticode result for each selected file. "
            "It is not a driver safety, compatibility, publisher trust, or package-catalog verdict."
        ),
    }
