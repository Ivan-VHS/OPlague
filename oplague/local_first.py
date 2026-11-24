"""Offline-first, append-only LWW-register store for local OPlague evidence.

The module owns only its SQLite database. It does not synchronize over a
network, inspect devices, change drivers, or execute plugin code. Replication
is an explicit export/merge of immutable operations supplied by the caller.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable, Mapping

_MAX_KEY_CHARS = 256
_MAX_ACTOR_CHARS = 64
_MAX_VALUE_BYTES = 1024 * 1024
_MAX_MERGE_OPERATIONS = 100_000
_ACTOR_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


class LocalFirstError(ValueError):
    """Invalid local-first operation, payload, or replication conflict."""


def _positive_integer(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise LocalFirstError(f"{label} must be a positive integer")
    return value


def _canonical_json(value: Any) -> str:
    try:
        encoded = json.dumps(
            value, ensure_ascii=False, allow_nan=False,
            sort_keys=True, separators=(",", ":"),
        )
    except (TypeError, ValueError, RecursionError) as error:
        raise LocalFirstError(f"value must be finite JSON data: {error}") from error
    if len(encoded.encode("utf-8")) > _MAX_VALUE_BYTES:
        raise LocalFirstError(f"value exceeds {_MAX_VALUE_BYTES} UTF-8 bytes")
    return encoded


def _validate_key(key: Any) -> str:
    if not isinstance(key, str):
        raise LocalFirstError("key must be text")
    if not key or len(key) > _MAX_KEY_CHARS or "\x00" in key:
        raise LocalFirstError(f"key must contain 1..{_MAX_KEY_CHARS} non-NUL characters")
    return key


def _normalize_operation(raw: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise LocalFirstError("operation must be a mapping")
    required = {"op_id", "actor", "counter", "lamport", "key", "value", "deleted"}
    if set(raw) != required:
        raise LocalFirstError(f"operation fields must be exactly {sorted(required)}")
    actor = raw["actor"]
    if not isinstance(actor, str) or not _ACTOR_RE.fullmatch(actor):
        raise LocalFirstError("actor must use 1..64 ASCII letters, digits, dot, underscore, or dash")
    counter = _positive_integer(raw["counter"], "counter")
    lamport = _positive_integer(raw["lamport"], "lamport")
    op_id = raw["op_id"]
    if op_id != f"{actor}:{counter}":
        raise LocalFirstError("op_id must equal actor:counter")
    key = _validate_key(raw["key"])
    deleted = raw["deleted"]
    if not isinstance(deleted, bool):
        raise LocalFirstError("deleted must be a boolean")
    if deleted and raw["value"] is not None:
        raise LocalFirstError("tombstones must carry a null value")
    value_json = _canonical_json(raw["value"])
    return {
        "op_id": op_id, "actor": actor, "counter": counter,
        "lamport": lamport, "key": key, "value_json": value_json,
        "deleted": int(deleted),
    }


class LocalFirstStore:
    """Small SQLite WAL store with deterministic last-writer-wins registers.

    The merge order is total and deterministic: (Lamport clock, actor,
    counter, operation id). Tombstones participate in the same ordering.
    This is a single-value CRDT register, not a general-purpose CRDT framework.
    """

    def __init__(self, database: str | Path, actor_id: str, *, timeout: float = 5.0) -> None:
        if not isinstance(actor_id, str) or not _ACTOR_RE.fullmatch(actor_id):
            raise LocalFirstError("actor_id must use 1..64 ASCII letters, digits, dot, underscore, or dash")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
            raise LocalFirstError("timeout must be positive")
        self.actor_id = actor_id
        self._lock = threading.RLock()
        self._closed = False
        location = str(database)
        if location != ":memory:":
            Path(location).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(
            location, timeout=float(timeout), isolation_level=None,
            check_same_thread=False,
        )
        self._db.execute(f"PRAGMA busy_timeout={int(float(timeout) * 1000)}")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA synchronous=FULL")
        mode = self._db.execute("PRAGMA journal_mode=WAL").fetchone()
        if not mode or str(mode[0]).lower() not in {"wal", "memory"}:
            self._db.close()
            self._closed = True
            raise LocalFirstError("SQLite could not enable WAL journaling")
        self._db.execute("PRAGMA user_version")
        version = int(self._db.execute("PRAGMA user_version").fetchone()[0])
        if version not in (0, 1):
            self._db.close()
            self._closed = True
            raise LocalFirstError(f"unsupported local-first schema version: {version}")
        self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS operations (
                op_id TEXT PRIMARY KEY,
                actor TEXT NOT NULL,
                counter INTEGER NOT NULL CHECK(counter > 0),
                lamport INTEGER NOT NULL CHECK(lamport > 0),
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                deleted INTEGER NOT NULL CHECK(deleted IN (0, 1)),
                UNIQUE(actor, counter)
            );
            CREATE INDEX IF NOT EXISTS operations_key_order
                ON operations(key, lamport DESC, actor DESC, counter DESC, op_id DESC);
            PRAGMA user_version=1;
            """
        )

    def _ensure_open(self) -> None:
        if self._closed:
            raise LocalFirstError("local-first store is closed")

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._db.close()
                self._closed = True

    def __enter__(self) -> "LocalFirstStore":
        self._ensure_open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def _begin(self) -> None:
        self._db.execute("BEGIN IMMEDIATE")

    def _append(self, key: str, value: Any, deleted: bool) -> dict[str, Any]:
        key = _validate_key(key)
        value_json = _canonical_json(None if deleted else value)
        with self._lock:
            self._ensure_open()
            self._begin()
            try:
                row = self._db.execute(
                    "SELECT COALESCE(MAX(counter), 0) FROM operations WHERE actor=?",
                    (self.actor_id,),
                ).fetchone()
                counter = int(row[0]) + 1
                clock_row = self._db.execute(
                    "SELECT COALESCE(MAX(lamport), 0) FROM operations"
                ).fetchone()
                lamport = int(clock_row[0]) + 1
                operation = {
                    "op_id": f"{self.actor_id}:{counter}",
                    "actor": self.actor_id,
                    "counter": counter,
                    "lamport": lamport,
                    "key": key,
                    "value": json.loads(value_json),
                    "deleted": deleted,
                }
                normalized = _normalize_operation(operation)
                self._db.execute(
                    """INSERT INTO operations
                       (op_id, actor, counter, lamport, key, value_json, deleted)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    tuple(normalized[name] for name in (
                        "op_id", "actor", "counter", "lamport", "key", "value_json", "deleted"
                    )),
                )
                self._db.execute("COMMIT")
                return operation
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def put(self, key: str, value: Any) -> dict[str, Any]:
        """Append a local value operation and return its portable wire form."""
        return self._append(key, value, False)

    def delete(self, key: str) -> dict[str, Any]:
        """Append a tombstone; deletion is replicated like any other operation."""
        return self._append(key, None, True)

    def get(self, key: str, default: Any = None) -> Any:
        key = _validate_key(key)
        with self._lock:
            self._ensure_open()
            row = self._db.execute(
                """SELECT value_json, deleted FROM operations WHERE key=?
                   ORDER BY lamport DESC, actor DESC, counter DESC, op_id DESC LIMIT 1""",
                (key,),
            ).fetchone()
            if row is None or int(row[1]):
                return default
            return json.loads(row[0])

    def snapshot(self) -> dict[str, Any]:
        """Return the current materialized key/value view in stable key order."""
        with self._lock:
            self._ensure_open()
            rows = self._db.execute(
                """SELECT key, value_json, deleted FROM (
                       SELECT key, value_json, deleted,
                              ROW_NUMBER() OVER (
                                  PARTITION BY key
                                  ORDER BY lamport DESC, actor DESC, counter DESC, op_id DESC
                              ) AS rank
                       FROM operations
                   ) WHERE rank=1 ORDER BY key"""
            ).fetchall()
            return {
                key: json.loads(value_json)
                for key, value_json, deleted in rows if not int(deleted)
            }

    def export_operations(self) -> list[dict[str, Any]]:
        """Export immutable operations for an explicit offline sync transport."""
        with self._lock:
            self._ensure_open()
            rows = self._db.execute(
                """SELECT op_id, actor, counter, lamport, key, value_json, deleted
                   FROM operations ORDER BY lamport, actor, counter, op_id"""
            ).fetchall()
            return [
                {
                    "op_id": row[0], "actor": row[1], "counter": int(row[2]),
                    "lamport": int(row[3]), "key": row[4],
                    "value": json.loads(row[5]), "deleted": bool(row[6]),
                }
                for row in rows
            ]

    def merge(self, operations: Iterable[Mapping[str, Any]]) -> int:
        """Idempotently merge a bounded batch; reject operation-id equivocation."""
        if isinstance(operations, (str, bytes, Mapping)):
            raise LocalFirstError("operations must be an iterable of operation mappings")
        try:
            raw_batch = list(operations)
        except TypeError as error:
            raise LocalFirstError("operations must be iterable") from error
        if len(raw_batch) > _MAX_MERGE_OPERATIONS:
            raise LocalFirstError(f"merge exceeds {_MAX_MERGE_OPERATIONS} operations")
        normalized = [_normalize_operation(item) for item in raw_batch]
        seen: dict[str, dict[str, Any]] = {}
        for item in normalized:
            previous = seen.get(item["op_id"])
            if previous is not None and previous != item:
                raise LocalFirstError(f"conflicting payloads for operation {item['op_id']}")
            seen[item["op_id"]] = item

        inserted = 0
        with self._lock:
            self._ensure_open()
            self._begin()
            try:
                for item in seen.values():
                    existing = self._db.execute(
                        """SELECT actor, counter, lamport, key, value_json, deleted
                           FROM operations WHERE op_id=?""",
                        (item["op_id"],),
                    ).fetchone()
                    expected = (
                        item["actor"], item["counter"], item["lamport"], item["key"],
                        item["value_json"], item["deleted"],
                    )
                    if existing is not None:
                        if tuple(existing) != expected:
                            raise LocalFirstError(
                                f"conflicting payload for existing operation {item['op_id']}"
                            )
                        continue
                    self._db.execute(
                        """INSERT INTO operations
                           (op_id, actor, counter, lamport, key, value_json, deleted)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        tuple(item[name] for name in (
                            "op_id", "actor", "counter", "lamport", "key", "value_json", "deleted"
                        )),
                    )
                    inserted += 1
                self._db.execute("COMMIT")
            except Exception:
                self._db.execute("ROLLBACK")
                raise
        return inserted

    def checkpoint(self) -> tuple[int, int, int]:
        """Request a passive WAL checkpoint and return SQLite's result tuple."""
        with self._lock:
            self._ensure_open()
            row = self._db.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
            return tuple(int(value) for value in row)
