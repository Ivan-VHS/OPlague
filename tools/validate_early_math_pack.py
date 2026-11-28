"""Read-only validation for bounded, offline early-math activity packs.

The validator accepts static teaching content only. It does not execute,
render, transmit, score, or collect information about children.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_ID = "dak.education.early-math-pack.v1"
MAX_PACK_BYTES = 256 * 1024
MAX_STAGES = 8
MAX_ACTIVITIES = 48
MAX_STEPS = 8
MAX_TEXT = 500
_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_LOCALE_PATTERN = re.compile(r"^[a-z]{2}(?:-[A-Z]{2})?$")
_UNSAFE_TEXT = re.compile(
    r"(?:https?://|javascript:|data:text/html|<\s*/?\s*(?:script|iframe|object|embed)\b)",
    re.IGNORECASE,
)

PRINCIPLES = {
    "objects_before_symbols",
    "short_child_paced_sessions",
    "play_over_speed",
    "everyday_math",
    "varied_materials",
    "errors_are_exploration",
}
CONCEPTS = {
    "quantity",
    "comparison",
    "sorting",
    "geometry",
    "one_to_one_matching",
    "spatial_language",
    "number_bonds",
    "measurement",
    "patterns",
}
TOP_KEYS = {
    "schema", "pack_id", "title", "locale", "age_months",
    "principles", "session_policy", "stages",
}
POLICY_KEYS = {
    "adult_guided", "child_paced", "timed", "scored",
    "personal_data_collection", "network_required", "duration_guidance",
}
STAGE_KEYS = {"id", "title", "age_months", "focus", "activities"}
ACTIVITY_KEYS = {
    "id", "title", "concepts", "materials", "steps",
    "adult_prompt", "adaptation",
}


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number is not allowed: {value}")


def load_pack(path: str | Path) -> Any:
    source = Path(path).expanduser()
    if source.is_symlink():
        raise ValueError("activity pack must not be a symbolic link")
    if not source.is_file():
        raise ValueError("activity pack path must be an existing regular file")
    raw = source.read_bytes()
    if len(raw) > MAX_PACK_BYTES:
        raise ValueError(f"activity pack exceeds {MAX_PACK_BYTES} bytes")
    try:
        decoded = raw.decode("utf-8", errors="strict")
        return json.loads(
            decoded,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"activity pack is not valid UTF-8 JSON: {error}") from error


def _keys(
    value: Any,
    allowed: set[str],
    required: set[str],
    label: str,
    errors: list[str],
) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        errors.append(f"{label} has unsupported fields: {', '.join(unknown)}")
    if missing:
        errors.append(f"{label} is missing fields: {', '.join(missing)}")
    return not unknown and not missing


def _integer(value: Any, label: str, low: int, high: int, errors: list[str]) -> bool:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        errors.append(f"{label} must be an integer from {low} through {high}")
        return False
    return True


def _plain_text(value: Any, label: str, errors: list[str], limit: int = MAX_TEXT) -> bool:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        errors.append(f"{label} must be non-empty text of at most {limit} characters")
        return False
    if _UNSAFE_TEXT.search(value):
        errors.append(f"{label} must not contain external links, executable URLs, or embedded markup")
        return False
    return True


def _text_list(
    value: Any,
    label: str,
    errors: list[str],
    *,
    minimum: int,
    maximum: int,
    allowed: set[str] | None = None,
) -> bool:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        errors.append(f"{label} must contain {minimum}..{maximum} entries")
        return False
    valid = True
    seen: set[str] = set()
    for index, item in enumerate(value):
        if allowed is None:
            valid = _plain_text(item, f"{label}[{index}]", errors, 160) and valid
        elif not isinstance(item, str) or item not in allowed:
            errors.append(f"{label}[{index}] is not a supported concept")
            valid = False
        if isinstance(item, str):
            if item in seen:
                errors.append(f"{label} must not contain duplicate entries")
                valid = False
            seen.add(item)
    return valid


def _age_range(value: Any, label: str, errors: list[str]) -> tuple[int, int] | None:
    if not _keys(value, {"min", "max"}, {"min", "max"}, label, errors):
        return None
    minimum_ok = _integer(value["min"], f"{label}.min", 18, 72, errors)
    maximum_ok = _integer(value["max"], f"{label}.max", 18, 72, errors)
    if not minimum_ok or not maximum_ok:
        return None
    if value["min"] >= value["max"]:
        errors.append(f"{label}.min must be lower than {label}.max")
        return None
    return value["min"], value["max"]


def validate_early_math_pack(payload: Any) -> list[str]:
    errors: list[str] = []
    if not _keys(payload, TOP_KEYS, TOP_KEYS, "pack", errors):
        return errors

    if payload["schema"] != SCHEMA_ID:
        errors.append(f"pack.schema must equal {SCHEMA_ID}")
    if not isinstance(payload["pack_id"], str) or not _ID_PATTERN.fullmatch(payload["pack_id"]):
        errors.append("pack.pack_id must be a lowercase kebab-case identifier")
    _plain_text(payload["title"], "pack.title", errors, 120)
    if not isinstance(payload["locale"], str) or not _LOCALE_PATTERN.fullmatch(payload["locale"]):
        errors.append("pack.locale must be a simple language or language-region tag")

    pack_age = _age_range(payload["age_months"], "pack.age_months", errors)
    _text_list(
        payload["principles"], "pack.principles", errors,
        minimum=4, maximum=6, allowed=PRINCIPLES,
    )

    policy = payload["session_policy"]
    if _keys(policy, POLICY_KEYS, POLICY_KEYS, "pack.session_policy", errors):
        expected = {
            "adult_guided": True,
            "child_paced": True,
            "timed": False,
            "scored": False,
            "personal_data_collection": False,
            "network_required": False,
        }
        for key, expected_value in expected.items():
            if policy[key] is not expected_value:
                errors.append(f"pack.session_policy.{key} must be {str(expected_value).lower()}")

        guidance = policy["duration_guidance"]
        if not isinstance(guidance, list) or len(guidance) > 3:
            errors.append("pack.session_policy.duration_guidance must contain at most three ranges")
        else:
            for index, item in enumerate(guidance):
                label = f"pack.session_policy.duration_guidance[{index}]"
                fields = {"age_min_months", "age_max_months", "minutes_min", "minutes_max"}
                if not _keys(item, fields, fields, label, errors):
                    continue
                age_min_ok = _integer(item["age_min_months"], f"{label}.age_min_months", 18, 72, errors)
                age_max_ok = _integer(item["age_max_months"], f"{label}.age_max_months", 18, 72, errors)
                minute_min_ok = _integer(item["minutes_min"], f"{label}.minutes_min", 1, 20, errors)
                minute_max_ok = _integer(item["minutes_max"], f"{label}.minutes_max", 1, 20, errors)
                if age_min_ok and age_max_ok and item["age_min_months"] >= item["age_max_months"]:
                    errors.append(f"{label} age minimum must be lower than age maximum")
                if minute_min_ok and minute_max_ok and item["minutes_min"] > item["minutes_max"]:
                    errors.append(f"{label} minute minimum must not exceed minute maximum")
                if pack_age and age_min_ok and age_max_ok:
                    if item["age_min_months"] < pack_age[0] or item["age_max_months"] > pack_age[1]:
                        errors.append(f"{label} must stay within the pack age range")

    stages = payload["stages"]
    if not isinstance(stages, list) or not 3 <= len(stages) <= MAX_STAGES:
        errors.append(f"pack.stages must contain 3..{MAX_STAGES} age bands")
        return errors

    stage_ids: set[str] = set()
    activity_ids: set[str] = set()
    previous_max: int | None = None
    activity_count = 0
    for stage_index, stage in enumerate(stages):
        label = f"pack.stages[{stage_index}]"
        if not _keys(stage, STAGE_KEYS, STAGE_KEYS, label, errors):
            continue
        stage_id = stage["id"]
        if not isinstance(stage_id, str) or not _ID_PATTERN.fullmatch(stage_id):
            errors.append(f"{label}.id must be a lowercase kebab-case identifier")
        elif stage_id in stage_ids:
            errors.append(f"{label}.id must be unique")
        else:
            stage_ids.add(stage_id)
        _plain_text(stage["title"], f"{label}.title", errors, 120)
        stage_age = _age_range(stage["age_months"], f"{label}.age_months", errors)
        if stage_age and pack_age:
            if stage_age[0] < pack_age[0] or stage_age[1] > pack_age[1]:
                errors.append(f"{label}.age_months must stay within the pack age range")
            if previous_max is not None and stage_age[0] < previous_max:
                errors.append("pack.stages must be ordered and must not overlap")
            previous_max = stage_age[1]
        _text_list(stage["focus"], f"{label}.focus", errors, minimum=1, maximum=9, allowed=CONCEPTS)

        activities = stage["activities"]
        if not isinstance(activities, list) or not 1 <= len(activities) <= 12:
            errors.append(f"{label}.activities must contain 1..12 activities")
            continue
        activity_count += len(activities)
        for activity_index, activity in enumerate(activities):
            activity_label = f"{label}.activities[{activity_index}]"
            required = ACTIVITY_KEYS - {"adaptation"}
            if not _keys(activity, ACTIVITY_KEYS, required, activity_label, errors):
                continue
            activity_id = activity["id"]
            if not isinstance(activity_id, str) or not _ID_PATTERN.fullmatch(activity_id):
                errors.append(f"{activity_label}.id must be a lowercase kebab-case identifier")
            elif activity_id in activity_ids:
                errors.append(f"{activity_label}.id must be unique across the pack")
            else:
                activity_ids.add(activity_id)
            _plain_text(activity["title"], f"{activity_label}.title", errors, 120)
            _text_list(activity["concepts"], f"{activity_label}.concepts", errors, minimum=1, maximum=9, allowed=CONCEPTS)
            _text_list(activity["materials"], f"{activity_label}.materials", errors, minimum=1, maximum=12)
            _text_list(activity["steps"], f"{activity_label}.steps", errors, minimum=2, maximum=MAX_STEPS)
            _plain_text(activity["adult_prompt"], f"{activity_label}.adult_prompt", errors, 240)
            if "adaptation" in activity:
                _plain_text(activity["adaptation"], f"{activity_label}.adaptation", errors, 300)

    if activity_count > MAX_ACTIVITIES:
        errors.append(f"pack contains more than {MAX_ACTIVITIES} activities")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a bounded, offline early-math activity pack without executing it."
    )
    parser.add_argument("pack", type=Path, help="path to the selected activity-pack JSON file")
    args = parser.parse_args(argv)
    try:
        payload = load_pack(args.pack)
    except (OSError, ValueError) as error:
        print(f"Early-math pack: FAIL: {error}", file=sys.stderr)
        return 1

    errors = validate_early_math_pack(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Early-math pack: FAIL ({len(errors)} finding(s))", file=sys.stderr)
        return 1
    print("Early-math pack: PASS (bounded static content; no child data or executable payload)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
