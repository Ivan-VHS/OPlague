"""Small synchronous AppGuard adapter for Python application trust boundaries."""
from __future__ import annotations

import logging
import re
from pathlib import PurePosixPath
from typing import Callable, Any

_ALLOWED_RULE = re.compile(r"^(?:A|M|Я|K|O)-[0-9]{2}$")
_ALLOWED_IDENTIFIER = re.compile(r"^[A-Za-z0-9_.:-]+$")
_LOGGER = logging.getLogger("veelsevul.appguard")


class AppGuard:
    """Bounded checks with structured, secret-free verdict evidence."""

    def __init__(self, audit_sink: Callable[[dict[str, Any]], None] | None = None) -> None:
        self._audit_sink = audit_sink

    @staticmethod
    def _context(level_id: int, rule_id: str, object_id: str) -> bool:
        return (
            isinstance(level_id, int)
            and 1 <= level_id <= 666
            and isinstance(rule_id, str)
            and bool(_ALLOWED_RULE.fullmatch(rule_id))
            and isinstance(object_id, str)
            and 0 < len(object_id) <= 128
            and all(ord(ch) >= 0x20 and ord(ch) != 0x7F for ch in object_id)
        )

    def _emit(self, level_id: int, rule_id: str, object_id: str,
              decision: str, reason: str) -> bool:
        if not self._context(level_id, rule_id, object_id):
            return False
        finding = {
            "policy_id": "veelsevul.appguard",
            "policy_version": "1.0.0",
            "level_id": f"L{level_id:03d}",
            "rule_id": rule_id,
            "object_id": object_id,
            "decision": decision,
            "reason": reason,
        }
        try:
            if self._audit_sink is not None:
                self._audit_sink(finding)
            else:
                _LOGGER.info("AppGuard verdict", extra={"appguard_finding": finding})
        except Exception:
            # An audit sink failure must not silently authorize the operation.
            return False
        return decision == "allow"

    def check_payload(self, actual_bytes: int, maximum_bytes: int, *,
                      level_id: int, rule_id: str, object_id: str) -> bool:
        valid = (
            isinstance(actual_bytes, int) and not isinstance(actual_bytes, bool)
            and isinstance(maximum_bytes, int) and not isinstance(maximum_bytes, bool)
            and actual_bytes >= 0 and maximum_bytes >= 0 and actual_bytes <= maximum_bytes
        )
        return self._emit(
            level_id, rule_id, object_id,
            "allow" if valid else "deny",
            "payload size within configured ceiling" if valid else "payload size invalid or ceiling exceeded",
        )

    def check_collection(self, actual_items: int, maximum_items: int, *,
                         level_id: int, rule_id: str, object_id: str) -> bool:
        valid = (
            isinstance(actual_items, int) and not isinstance(actual_items, bool)
            and isinstance(maximum_items, int) and not isinstance(maximum_items, bool)
            and actual_items >= 0 and maximum_items >= 0 and actual_items <= maximum_items
        )
        return self._emit(
            level_id, rule_id, object_id,
            "allow" if valid else "degrade",
            "collection count within configured ceiling" if valid else "collection count invalid or ceiling exceeded",
        )

    def check_identifier(self, value: str, *, maximum_bytes: int = 80,
                         level_id: int, rule_id: str, object_id: str) -> bool:
        valid = (
            isinstance(value, str)
            and 0 < len(value.encode("utf-8", errors="replace")) <= maximum_bytes
            and bool(_ALLOWED_IDENTIFIER.fullmatch(value))
            and not value.startswith(".")
        )
        return self._emit(
            level_id, rule_id, object_id,
            "allow" if valid else "deny",
            "identifier satisfies ASCII allowlist" if valid else "identifier rejected by length or ASCII allowlist",
        )

    def check_relative_path(self, value: str, *, maximum_bytes: int = 1024,
                            level_id: int, rule_id: str, object_id: str) -> bool:
        valid = isinstance(value, str) and bool(value)
        normalized = value.replace("\\", "/") if isinstance(value, str) else ""
        trimmed = normalized.rstrip("/")
        parts = trimmed.split("/") if trimmed else []
        if (
            not valid
            or len(normalized.encode("utf-8", errors="replace")) > maximum_bytes
            or "\x00" in normalized
            or PurePosixPath(normalized).is_absolute()
            or re.match(r"^[A-Za-z]:", normalized) is not None
            or any(part in ("", ".", "..") for part in parts)
            or any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in normalized)
        ):
            valid = False
        return self._emit(
            level_id, rule_id, object_id,
            "allow" if valid else "deny",
            "relative path stays within its archive boundary" if valid else "absolute, traversing or malformed path rejected",
        )
