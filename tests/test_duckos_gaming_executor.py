from __future__ import annotations

import unittest
from unittest.mock import patch

from tools import game_optimizer
from tools.duckos_gaming_executor import (
    EXECUTOR_SCHEMA,
    GamingSessionExecutionError,
    restore_duckos_game_session,
    start_duckos_game_session,
)


class DuckOSGamingExecutorTests(unittest.TestCase):
    def profile(self):
        return {
            "schema": "duckos.gaming-session-profile.v1",
            "game_id": "sample-game",
            "engine": "directx12",
            "worker_count": 8,
            "multithreaded": True,
            "audio_enabled": True,
            "source_rules": ["GPR-13"],
            "execution_performed": False,
        }

    def test_start_requires_explicit_consent_before_power_plan_change(self):
        with patch.object(game_optimizer, "start_game_session") as start:
            with self.assertRaises(PermissionError):
                start_duckos_game_session(self.profile(), consent=False)
        start.assert_not_called()

    def test_start_delegates_to_snapshot_first_session_after_consent(self):
        session = {
            "session_id": "session-1",
            "status": "active",
            "snapshot_id": "snapshot-1",
            "previous_power_scheme": {"guid": "old-plan"},
            "applied_power_scheme_guid": "new-plan",
        }
        with patch.object(game_optimizer, "start_game_session", return_value=session) as start:
            result = start_duckos_game_session(
                self.profile(), consent=True, power_mode="performance"
            )
        start.assert_called_once()
        self.assertEqual(start.call_args.args[0], "sample-game")
        self.assertEqual(start.call_args.kwargs["power_mode"], "performance")
        self.assertEqual(result["schema"], EXECUTOR_SCHEMA)
        self.assertTrue(result["power_plan_changed"])
        self.assertTrue(result["restore_on_exit_required"])
        self.assertFalse(result["driver_state_changed"])

    def test_invalid_profiles_and_modes_are_rejected_before_execution(self):
        bad = self.profile()
        bad["game_id"] = "../escape"
        with patch.object(game_optimizer, "start_game_session") as start:
            with self.assertRaises(GamingSessionExecutionError):
                start_duckos_game_session(bad, consent=True)
            with self.assertRaises(GamingSessionExecutionError):
                start_duckos_game_session(self.profile(), consent=True, power_mode="overclock")
        start.assert_not_called()

    def test_restore_delegates_to_compare_before_restore_session(self):
        restored = {"session": {"game_name": "sample-game", "session_id": "session-1", "status": "restored"}}
        with patch.object(game_optimizer, "restore_game_session", return_value={"restored": True, **restored}) as restore:
            result = restore_duckos_game_session()
        restore.assert_called_once()
        self.assertTrue(result["restored"])
        self.assertEqual(result["status"], "restored")
        self.assertFalse(result["registry_changed"])

    def test_external_power_plan_change_is_reported_not_overwritten(self):
        session = {"game_name": "sample-game", "session_id": "session-1", "status": "restore_skipped_external_change"}
        with patch.object(
            game_optimizer, "restore_game_session",
            return_value={"restored": False, "reason": "external_power_plan_change", "session": session},
        ):
            result = restore_duckos_game_session()
        self.assertFalse(result["restored"])
        self.assertTrue(result["active_external_plan_left_untouched"])


if __name__ == "__main__":
    unittest.main()
