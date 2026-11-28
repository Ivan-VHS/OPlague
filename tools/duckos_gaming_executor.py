"""Consent-gated Windows power-plan execution for DuckOS game sessions.

OPlague reuses its snapshot-first, compare-before-restore session operations.
No driver, registry, clock, fan, service, scheduler or network setting is changed.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tools import game_optimizer

SESSION_SCHEMA = "duckos.gaming-session-profile.v1"
EXECUTOR_SCHEMA = "oplague.duckos-gaming-session.v1"
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
POWER_MODES = {"performance", "balanced", "none"}


class GamingSessionExecutionError(ValueError):
    """Raised when a DuckOS session cannot be safely handed to OPlague."""


def _validate_profile(profile: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(profile, dict) or profile.get("schema") != SESSION_SCHEMA:
        raise GamingSessionExecutionError(f"expected a {SESSION_SCHEMA} profile")
    game_id = profile.get("game_id")
    engine = profile.get("engine")
    worker_count = profile.get("worker_count")
    multithreaded = profile.get("multithreaded")
    audio_enabled = profile.get("audio_enabled")
    if not isinstance(game_id, str) or not SAFE_ID.fullmatch(game_id):
        raise GamingSessionExecutionError("game_id must be a safe identifier")
    if not isinstance(engine, str) or not SAFE_ID.fullmatch(engine):
        raise GamingSessionExecutionError("engine must be a safe identifier")
    if isinstance(worker_count, bool) or not isinstance(worker_count, int) or not 1 <= worker_count <= 64:
        raise GamingSessionExecutionError("worker_count must be between 1 and 64")
    if not isinstance(multithreaded, bool) or not isinstance(audio_enabled, bool):
        raise GamingSessionExecutionError("multithreaded and audio_enabled must be booleans")
    if profile.get("execution_performed") is not False:
        raise GamingSessionExecutionError("DuckOS session profiles must be declarative")
    return profile


def start_duckos_game_session(
    profile: dict[str, Any],
    *,
    consent: bool,
    power_mode: str = "performance",
    directory: Path | None = None,
    runner: Any = None,
    device_reader: Any = None,
) -> dict[str, Any]:
    """Start a snapshot-first power session only after explicit user consent."""
    validated = _validate_profile(profile)
    if consent is not True:
        raise PermissionError("Explicit user consent is required before changing the Windows power plan")
    if power_mode not in POWER_MODES:
        raise GamingSessionExecutionError("power_mode must be performance, balanced or none")

    session = game_optimizer.start_game_session(
        validated["game_id"],
        power_mode=power_mode,
        directory=directory,
        runner=runner,
        device_reader=device_reader,
    )
    previous_guid = str((session.get("previous_power_scheme") or {}).get("guid") or "")
    applied_guid = str(session.get("applied_power_scheme_guid") or previous_guid)
    return {
        "schema": EXECUTOR_SCHEMA,
        "game_id": validated["game_id"],
        "session_id": session.get("session_id"),
        "status": session.get("status"),
        "snapshot_id": session.get("snapshot_id"),
        "power_mode": power_mode,
        "power_plan_changed": bool(applied_guid and applied_guid.casefold() != previous_guid.casefold()),
        "automatic_cpu_or_gpu_overclock": False,
        "driver_state_changed": False,
        "registry_changed": False,
        "execution_performed": True,
        "restore_on_exit_required": True,
        "session": session,
    }


def restore_duckos_game_session(
    *,
    directory: Path | None = None,
    runner: Any = None,
) -> dict[str, Any]:
    """Restore only the power plan still owned by this OPlague session."""
    result = game_optimizer.restore_game_session(directory=directory, runner=runner)
    session = result.get("session") or {}
    return {
        "schema": EXECUTOR_SCHEMA,
        "game_id": session.get("game_name"),
        "session_id": session.get("session_id"),
        "status": session.get("status"),
        "restored": bool(result.get("restored")),
        "reason": result.get("reason"),
        "active_external_plan_left_untouched": result.get("reason") == "external_power_plan_change",
        "execution_performed": True,
        "driver_state_changed": False,
        "registry_changed": False,
        "session": session,
    }
