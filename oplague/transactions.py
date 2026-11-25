"""Transactional transformations for in-memory OPlague evidence reports.

This is deliberately NOT a driver, registry, device, filesystem, or firmware writer.
Only caller-owned JSON report data is staged and committed in process memory.
"""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import threading
from dataclasses import dataclass
from typing import Any, Callable, Iterable


class EvidenceTransitionError(ValueError):
    """Invalid or failed evidence-state transition."""


class EvidenceConflict(EvidenceTransitionError):
    """Optimistic generation check failed."""


@dataclass(frozen=True, slots=True)
class EvidenceSnapshot:
    generation: int
    schema_version: int
    sha256: str
    data: Any


def _seal(value: Any, max_bytes: int) -> tuple[Any, str]:
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, RecursionError) as error:
        raise EvidenceTransitionError(f"evidence must be finite JSON data: {error}") from error
    if len(raw) > max_bytes:
        raise EvidenceTransitionError(f"evidence exceeds {max_bytes} bytes")
    return copy.deepcopy(value), hashlib.sha256(raw).hexdigest()


class EvidenceTransaction:
    """A bounded, in-memory transaction for reports and evidence snapshots."""

    def __init__(
        self,
        data: Any,
        *,
        schema_version: int = 1,
        max_bytes: int = 8 * 1024 * 1024,
        event_sink: Callable[[str, int], None] | None = None,
    ) -> None:
        if isinstance(schema_version, bool) or not isinstance(schema_version, int) or schema_version < 1:
            raise EvidenceTransitionError("schema_version must be a positive integer")
        if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes < 1:
            raise EvidenceTransitionError("max_bytes must be a positive integer")
        self._lock = threading.RLock()
        self._max_bytes = max_bytes
        self._events = event_sink
        self._generation = 0
        self._staged_schema = schema_version
        self._committed_schema = schema_version
        self._committed, self._committed_hash = _seal(data, max_bytes)
        self._staged = copy.deepcopy(self._committed)
        self._staged_hash = self._committed_hash
        self._binding: str | None = None

    def _emit(self, event: str) -> None:
        if self._events:
            self._events(event, self._generation)

    def _stage(self, value: Any) -> None:
        self._staged, self._staged_hash = _seal(value, self._max_bytes)

    @property
    def staged(self) -> Any:
        with self._lock:
            return copy.deepcopy(self._staged)

    def rebind(self, evidence_id: str, value: Any) -> None:
        if not isinstance(evidence_id, str) or not evidence_id or len(evidence_id) > 128:
            raise EvidenceTransitionError("evidence_id must contain 1..128 characters")
        with self._lock:
            if not isinstance(self._staged, dict):
                raise EvidenceTransitionError("rebind requires a mapping report")
            candidate = copy.deepcopy(self._staged)
            candidate[evidence_id] = value
            self._stage(candidate)
            self._binding = evidence_id
            self._emit("EVIDENCE_REBOUND")

    def patch(self, path: Iterable[str | int], value: Any) -> None:
        parts = tuple(path)
        if not parts:
            raise EvidenceTransitionError("patch path cannot be empty")
        with self._lock:
            candidate = copy.deepcopy(self._staged)
            parent = candidate
            for part in parts[:-1]:
                try:
                    parent = parent[part]
                except (KeyError, IndexError, TypeError) as error:
                    raise EvidenceTransitionError(f"invalid evidence path at {part!r}") from error
            leaf = parts[-1]
            try:
                if isinstance(parent, dict) and isinstance(leaf, str) and leaf in parent:
                    parent[leaf] = value
                elif isinstance(parent, list) and isinstance(leaf, int) and not isinstance(leaf, bool) and 0 <= leaf < len(parent):
                    parent[leaf] = value
                else:
                    raise EvidenceTransitionError("patch target must be an existing mapping key or list index")
            except (IndexError, TypeError) as error:
                raise EvidenceTransitionError("invalid evidence patch target") from error
            self._stage(candidate)
            self._emit("EVIDENCE_PATCH_STAGED")

    def remap(self, key_map: dict[str, str]) -> None:
        if not isinstance(key_map, dict) or not all(
            isinstance(old, str) and old and isinstance(new, str) and new for old, new in key_map.items()
        ):
            raise EvidenceTransitionError("key_map must map non-empty strings")
        with self._lock:
            if not isinstance(self._staged, dict):
                raise EvidenceTransitionError("remap requires a mapping report")
            if len(set(key_map.values())) != len(key_map):
                raise EvidenceTransitionError("remap destinations must be unique")
            if not set(key_map).issubset(self._staged):
                raise EvidenceTransitionError("remap source key is missing")
            candidate = copy.deepcopy(self._staged)
            moved = {new: candidate[old] for old, new in key_map.items()}
            for old in key_map:
                del candidate[old]
            if set(moved) & candidate.keys():
                raise EvidenceTransitionError("remap destination already exists")
            candidate.update(moved)
            self._stage(candidate)
            self._emit("EVIDENCE_REMAP_STAGED")

    def hot_swap(self, replacement_report: Any) -> None:
        with self._lock:
            self._stage(replacement_report)
            self._emit("REPORT_DRAFT_SWAPPED")

    def migrate(self, target_schema: int, transform: Callable[[Any], Any]) -> None:
        if isinstance(target_schema, bool) or not isinstance(target_schema, int) or target_schema <= self._staged_schema:
            raise EvidenceTransitionError("target schema must be a higher integer version")
        if not callable(transform):
            raise EvidenceTransitionError("transform must be callable")
        with self._lock:
            candidate, digest = _seal(transform(copy.deepcopy(self._staged)), self._max_bytes)
            self._staged = candidate
            self._staged_hash = digest
            self._staged_schema = target_schema
            self._emit("EVIDENCE_SCHEMA_MIGRATED")

    def flash(self, expected_generation: int | None = None) -> EvidenceSnapshot:
        """Commit the staged report in memory; no device or disk writes occur."""
        with self._lock:
            expected = self._generation if expected_generation is None else expected_generation
            if expected != self._generation:
                raise EvidenceConflict(f"expected generation {expected}, current {self._generation}")
            _, actual = _seal(self._staged, self._max_bytes)
            if actual != self._staged_hash:
                raise EvidenceTransitionError("staged evidence digest mismatch")
            self._committed = copy.deepcopy(self._staged)
            self._committed_hash = actual
            self._committed_schema = self._staged_schema
            self._generation += 1
            self._emit("EVIDENCE_SNAPSHOT_COMMITTED")
            return self.snapshot()

    def reflash(self, expected_generation: int | None = None) -> EvidenceSnapshot:
        return self.flash(expected_generation)

    def sync(self) -> EvidenceSnapshot:
        return self.flash()

    async def async_flash(self, expected_generation: int | None = None) -> EvidenceSnapshot:
        return await asyncio.to_thread(self.flash, expected_generation)

    @staticmethod
    async def await_result(task: "asyncio.Future[EvidenceSnapshot]") -> EvidenceSnapshot:
        return await task

    def rollback(self) -> EvidenceSnapshot:
        with self._lock:
            self._staged = copy.deepcopy(self._committed)
            self._staged_hash = self._committed_hash
            self._staged_schema = self._committed_schema
            self._emit("EVIDENCE_ROLLBACK")
            return self.snapshot()

    def snapshot(self) -> EvidenceSnapshot:
        with self._lock:
            return EvidenceSnapshot(
                generation=self._generation,
                schema_version=self._committed_schema,
                sha256=self._committed_hash,
                data=copy.deepcopy(self._committed),
            )

    def emit(self, name: str) -> None:
        if not isinstance(name, str) or not name or len(name) > 128:
            raise EvidenceTransitionError("event name must contain 1..128 characters")
        with self._lock:
            self._emit(name)

    def yield_checkpoint(self, label: str) -> str:
        self.emit("CHECKPOINT:" + label)
        return label

    @staticmethod
    def return_value(value: Any = None) -> Any:
        return value

    @staticmethod
    def throw(message: str) -> None:
        raise EvidenceTransitionError(str(message))

    @staticmethod
    def panic(message: str) -> None:
        raise EvidenceTransitionError(f"guarded panic: {message}")

    @staticmethod
    def assert_condition(condition: Any, message: str = "evidence assertion failed") -> None:
        if not condition:
            raise EvidenceTransitionError(message)

    @staticmethod
    def catch(operation: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, str | None]:
        try:
            return operation(*args, **kwargs), None
        except EvidenceTransitionError as error:
            return None, str(error)
