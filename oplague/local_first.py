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
import time
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
        if version not in (0, 1, 2):
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
            CREATE TABLE IF NOT EXISTS state_history (
                revision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_revision INTEGER REFERENCES state_history(revision_id),
                branch TEXT NOT NULL,
                action TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                created_ns INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS state_history_branch_revision
                ON state_history(branch, revision_id DESC);
            CREATE TABLE IF NOT EXISTS history_branches (
                branch TEXT PRIMARY KEY,
                head_revision INTEGER REFERENCES state_history(revision_id)
            );
            INSERT OR IGNORE INTO history_branches(branch, head_revision)
                VALUES ('main', NULL);
            PRAGMA user_version=2;
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


    @staticmethod
    def _validate_history_branch(branch: Any) -> str:
        if not isinstance(branch, str) or not _ACTOR_RE.fullmatch(branch):
            raise LocalFirstError("history branch must use 1..64 ASCII letters, digits, dot, underscore, or dash")
        return branch

    def commit_history(
        self,
        branch: str = "main",
        action: str = "checkpoint",
        state: Mapping[str, Any] | None = None,
    ) -> int:
        """Append an immutable workspace snapshot to a branch and advance its head."""
        branch = self._validate_history_branch(branch)
        if not isinstance(action, str) or not 1 <= len(action) <= 128 or "\x00" in action:
            raise LocalFirstError("history action must contain 1..128 non-NUL characters")
        if state is None:
            materialized = self.snapshot()
        else:
            if not isinstance(state, Mapping):
                raise LocalFirstError("history state must be a key/value mapping")
            materialized = {_validate_key(key): value for key, value in state.items()}
        snapshot_json = _canonical_json(materialized)

        with self._lock:
            self._ensure_open()
            self._begin()
            try:
                row = self._db.execute(
                    "SELECT head_revision FROM history_branches WHERE branch=?",
                    (branch,),
                ).fetchone()
                if row is None:
                    raise LocalFirstError(f"unknown history branch: {branch}")
                parent = row[0]
                cursor = self._db.execute(
                    """INSERT INTO state_history
                       (parent_revision, branch, action, snapshot_json, created_ns)
                       VALUES (?, ?, ?, ?, ?)""",
                    (parent, branch, action, snapshot_json, time.time_ns()),
                )
                revision_id = int(cursor.lastrowid)
                self._db.execute(
                    "UPDATE history_branches SET head_revision=? WHERE branch=?",
                    (revision_id, branch),
                )
                self._db.execute("COMMIT")
                return revision_id
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def create_history_branch(self, branch: str, from_revision: int) -> None:
        """Create an isolated history head at any existing immutable revision."""
        branch = self._validate_history_branch(branch)
        if branch == "main":
            raise LocalFirstError("the main history branch already exists")
        from_revision = _positive_integer(from_revision, "from_revision")
        with self._lock:
            self._ensure_open()
            self._begin()
            try:
                exists = self._db.execute(
                    "SELECT 1 FROM state_history WHERE revision_id=?",
                    (from_revision,),
                ).fetchone()
                if exists is None:
                    raise LocalFirstError(f"unknown history revision: {from_revision}")
                try:
                    self._db.execute(
                        "INSERT INTO history_branches(branch, head_revision) VALUES (?, ?)",
                        (branch, from_revision),
                    )
                except sqlite3.IntegrityError as error:
                    raise LocalFirstError(f"history branch already exists: {branch}") from error
                self._db.execute("COMMIT")
            except Exception:
                self._db.execute("ROLLBACK")
                raise

    def history_checkout(self, branch: str = "main", revision_id: int | None = None) -> dict[str, Any]:
        """Read the branch head or one of its ancestors without mutating live data."""
        branch = self._validate_history_branch(branch)
        if revision_id is not None:
            revision_id = _positive_integer(revision_id, "revision_id")
        with self._lock:
            self._ensure_open()
            branch_row = self._db.execute(
                "SELECT head_revision FROM history_branches WHERE branch=?",
                (branch,),
            ).fetchone()
            if branch_row is None:
                raise LocalFirstError(f"unknown history branch: {branch}")
            head = branch_row[0]
            target = head if revision_id is None else revision_id
            if target is None:
                raise LocalFirstError(f"history branch has no revisions: {branch}")
            row = self._db.execute(
                """WITH RECURSIVE lineage(revision_id, parent_revision) AS (
                       SELECT revision_id, parent_revision
                       FROM state_history WHERE revision_id=?
                       UNION ALL
                       SELECT parent.revision_id, parent.parent_revision
                       FROM state_history AS parent
                       JOIN lineage ON parent.revision_id=lineage.parent_revision
                   )
                   SELECT snapshot_json FROM state_history
                   WHERE revision_id=?
                     AND revision_id IN (SELECT revision_id FROM lineage)""",
                (head, target),
            ).fetchone()
            if row is None:
                raise LocalFirstError(
                    f"revision {target} is not in the ancestry of history branch {branch}"
                )
            try:
                decoded = json.loads(row[0])
            except (TypeError, ValueError) as error:
                raise LocalFirstError("stored history snapshot is invalid JSON") from error
            if not isinstance(decoded, dict):
                raise LocalFirstError("stored history snapshot is not a key/value object")
            return decoded

    def history_diff(self, before_revision: int, after_revision: int) -> dict[str, list[dict[str, Any]]]:
        """Return a deterministic key-level diff between two immutable revisions."""
        before_revision = _positive_integer(before_revision, "before_revision")
        after_revision = _positive_integer(after_revision, "after_revision")
        with self._lock:
            self._ensure_open()
            rows = self._db.execute(
                "SELECT revision_id, snapshot_json FROM state_history WHERE revision_id IN (?, ?)",
                (before_revision, after_revision),
            ).fetchall()
        snapshots = {int(row[0]): json.loads(row[1]) for row in rows}
        if before_revision not in snapshots or after_revision not in snapshots:
            raise LocalFirstError("history diff references an unknown revision")
        before, after = snapshots[before_revision], snapshots[after_revision]
        before_keys, after_keys = set(before), set(after)
        added = [{"key": key, "value": after[key]} for key in sorted(after_keys - before_keys)]
        removed = [{"key": key, "value": before[key]} for key in sorted(before_keys - after_keys)]
        changed = [
            {"key": key, "before": before[key], "after": after[key]}
            for key in sorted(before_keys & after_keys)
            if before[key] != after[key]
        ]
        return {"added": added, "removed": removed, "changed": changed}

    def history_restore_key(
        self, key: str, revision_id: int, branch: str = "main"
    ) -> dict[str, Any]:
        """Restore one historical key as a new CRDT operation; preserve later keys."""
        key = _validate_key(key)
        historical = self.history_checkout(branch, revision_id)
        if key in historical:
            operation = self.put(key, historical[key])
        else:
            operation = self.delete(key)
        self.commit_history(branch, "restore-key", self.snapshot())
        return operation

    def history_log(self, branch: str = "main", limit: int = 100) -> list[dict[str, Any]]:
        """Return newest-first revision metadata along a branch's parent chain."""
        branch = self._validate_history_branch(branch)
        limit = _positive_integer(limit, "limit")
        if limit > 1000:
            raise LocalFirstError("history log limit must not exceed 1000")
        with self._lock:
            self._ensure_open()
            row = self._db.execute(
                "SELECT head_revision FROM history_branches WHERE branch=?",
                (branch,),
            ).fetchone()
            if row is None:
                raise LocalFirstError(f"unknown history branch: {branch}")
            if row[0] is None:
                return []
            rows = self._db.execute(
                """WITH RECURSIVE lineage(revision_id, parent_revision, branch, action, created_ns) AS (
                       SELECT revision_id, parent_revision, branch, action, created_ns
                       FROM state_history WHERE revision_id=?
                       UNION ALL
                       SELECT parent.revision_id, parent.parent_revision,
                              parent.branch, parent.action, parent.created_ns
                       FROM state_history AS parent
                       JOIN lineage ON parent.revision_id=lineage.parent_revision
                   )
                   SELECT revision_id, parent_revision, branch, action, created_ns
                   FROM lineage ORDER BY revision_id DESC LIMIT ?""",
                (row[0], limit),
            ).fetchall()
            return [
                {
                    "revision_id": int(item[0]),
                    "parent_revision": None if item[1] is None else int(item[1]),
                    "branch": str(item[2]),
                    "action": str(item[3]),
                    "created_ns": int(item[4]),
                }
                for item in rows
            ]

    def checkpoint(self) -> tuple[int, int, int]:
        """Request a passive WAL checkpoint and return SQLite's result tuple."""
        with self._lock:
            self._ensure_open()
            row = self._db.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
            return tuple(int(value) for value in row)
