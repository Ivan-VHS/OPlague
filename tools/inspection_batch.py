"""Bounded, ordered batch preflight for read-only driver package inspection.

The batch runner intentionally processes one file at a time. This keeps the
memory/IO footprint predictable and gives slow consumers natural backpressure.
It does not extract, execute, load, install, or modify package contents.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_PACKAGES = 64
MAX_PACKAGE_BYTES = 512 * 1024 * 1024
MAX_BATCH_SOURCE_BYTES = 8 * 1024 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class BatchInspectionBudget:
    max_packages: int = MAX_PACKAGES
    max_package_bytes: int = MAX_PACKAGE_BYTES
    max_total_source_bytes: int = MAX_BATCH_SOURCE_BYTES

    def validate(self) -> None:
        for name, value in (
            ("max_packages", self.max_packages),
            ("max_package_bytes", self.max_package_bytes),
            ("max_total_source_bytes", self.max_total_source_bytes),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")


def inspect_batch(
    sources: Sequence[str | Path],
    inspector: Callable[[str | Path], dict[str, Any]],
    *,
    budget: BatchInspectionBudget = BatchInspectionBudget(),
) -> list[dict[str, Any]]:
    """Preflight the full batch, then inspect in supplied order, one at a time.

    No package is inspected until every selected path and aggregate byte budget
    has passed preflight. The injected inspector must itself remain read-only.
    """
    budget.validate()
    if not isinstance(sources, (list, tuple)) or not sources:
        raise ValueError("select at least one driver package")
    if len(sources) > budget.max_packages:
        raise ValueError(f"batch contains more than {budget.max_packages} packages")
    if not callable(inspector):
        raise TypeError("inspector must be callable")

    normalized: list[Path] = []
    total_bytes = 0
    for source in sources:
        path = Path(source).expanduser()
        if path.is_symlink():
            raise ValueError(f"symbolic-link package paths are not allowed: {path}")
        if not path.is_file():
            raise FileNotFoundError(f"package is not a regular file: {path}")
        suffix = path.suffix.casefold()
        if suffix not in {".inf", ".zip"}:
            raise ValueError(f"unsupported package extension: {path.suffix or '<none>'}")
        size = path.stat().st_size
        if size > budget.max_package_bytes:
            raise ValueError(f"package exceeds the {budget.max_package_bytes}-byte batch limit: {path.name}")
        total_bytes += size
        if total_bytes > budget.max_total_source_bytes:
            raise ValueError("selected packages exceed the aggregate batch byte budget")
        normalized.append(path)

    # Deliberately synchronous: at most one inspector call is active, results
    # remain ordered, and no unbounded worker or result queue can accumulate.
    return [inspector(path) for path in normalized]
