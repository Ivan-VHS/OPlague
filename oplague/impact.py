"""OPlague's read-only semantic impact-profile registry.

This first functional slice supports searchable diagnostic/event labels. It does not
inspect hardware, infer driver compatibility, install drivers, or modify devices.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "impact_profiles.json"
DIMENSIONS = ("acoustic", "scale", "kinetic", "reach", "impulse")


def load_profiles(path: Path = REGISTRY_PATH) -> tuple[dict[str, Any], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("unsupported impact-profile registry schema")
    rows = payload.get("profiles")
    if not isinstance(rows, list) or len(rows) != 20:
        raise ValueError("registry must contain exactly 20 profiles")
    profiles = []
    seen_ids: set[int] = set()
    seen_terms: set[tuple[str, str, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("profile entries must be objects")
        profile_id = row.get("id")
        if isinstance(profile_id, bool) or not isinstance(profile_id, int) or profile_id in seen_ids:
            raise ValueError("profile IDs must be unique integers")
        if not all(isinstance(row.get(key), str) and row[key].strip() for key in ("sound", "scale", "motion")):
            raise ValueError(f"profile {profile_id} has an empty lexical component")
        terms = tuple(row[key].casefold() for key in ("sound", "scale", "motion"))
        if terms in seen_terms:
            raise ValueError("profile terms must be unique")
        seen_terms.add(terms)
        seen_ids.add(profile_id)
        ranks = row.get("ranks")
        if not isinstance(ranks, dict) or set(ranks) != set(DIMENSIONS):
            raise ValueError(f"profile {profile_id} has invalid dimensions")
        for dimension, rank in ranks.items():
            if isinstance(rank, bool) or not isinstance(rank, int) or not 1 <= rank <= 5:
                raise ValueError(f"profile {profile_id} has invalid {dimension} rank")
        profiles.append({
            "id": profile_id,
            "sound": row["sound"],
            "scale": row["scale"],
            "motion": row["motion"],
            "ranks": dict(ranks),
        })
    if seen_ids != set(range(1, 21)):
        raise ValueError("profile IDs must be sequential from 1 to 20")
    return tuple(profiles)


PROFILES = load_profiles()


def search_profiles(query: str) -> list[dict[str, Any]]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must be non-empty text")
    terms = query.casefold().split()
    result = []
    for profile in PROFILES:
        haystack = " ".join(profile[key] for key in ("sound", "scale", "motion")).casefold()
        if all(term in haystack for term in terms):
            result.append({**profile, "ranks": dict(profile["ranks"])})
    return result


def get_profile(query: str | int) -> dict[str, Any]:
    if isinstance(query, bool):
        raise ValueError("profile query must be an ID or text")
    if isinstance(query, int):
        matches = [p for p in PROFILES if p["id"] == query]
    else:
        matches = search_profiles(query)
    if not matches:
        raise KeyError(f"no impact profile matches {query!r}")
    if len(matches) != 1:
        raise ValueError(f"ambiguous impact profile query {query!r}")
    profile = matches[0]
    return {**profile, "ranks": dict(profile["ranks"])}


def rank_profiles(dimension: str, profiles: tuple[dict[str, Any], ...] | list[dict[str, Any]] = PROFILES) -> list[dict[str, Any]]:
    if dimension not in DIMENSIONS:
        raise ValueError(f"dimension must be one of: {', '.join(DIMENSIONS)}")
    checked = []
    for profile in profiles:
        ranks = profile.get("ranks") if isinstance(profile, dict) else None
        value = ranks.get(dimension) if isinstance(ranks, dict) else None
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
            raise ValueError(f"profile has an invalid {dimension!r} rank")
        checked.append(profile)
    return sorted(checked, key=lambda item: item["ranks"][dimension], reverse=True)


def format_catalog() -> str:
    lines = ["OPlague impact profile registry — 20 semantic profiles"]
    for p in PROFILES:
        r = p["ranks"]
        lines.append(
            f'{p["id"]:02d} | {p["sound"]} | {p["scale"]} | {p["motion"]} | '
            + " ".join(str(r[key]) for key in DIMENSIONS)
        )
    lines.append("Ordinal lexical ranks only; no hardware or physical measurement is implied.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect OPlague's semantic impact-profile registry.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--catalog", action="store_true", help="list all 20 profiles")
    group.add_argument("--search", metavar="TEXT", help="search profile terms")
    group.add_argument("--profile", metavar="ID_OR_TERM", help="show one profile")
    group.add_argument("--rank", choices=DIMENSIONS, help="rank profiles by an ordinal dimension")
    parser.add_argument("--verify", action="store_true", help="validate the on-disk registry")
    args = parser.parse_args(argv)
    if args.verify:
        load_profiles()
        print("Impact profile registry: PASS (20 profiles)")
    elif args.catalog:
        print(format_catalog())
    elif args.search:
        print(json.dumps(search_profiles(args.search), ensure_ascii=False, indent=2))
    elif args.profile:
        query: str | int = int(args.profile) if args.profile.isdigit() else args.profile
        print(json.dumps(get_profile(query), ensure_ascii=False, indent=2))
    elif args.rank:
        print(json.dumps(rank_profiles(args.rank), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
