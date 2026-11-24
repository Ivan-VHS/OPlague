#!/usr/bin/env python3
"""Read-only Red Sparrow content guard for repository safety triage."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "security" / "red_sparrow.v1.json"


class PolicyError(ValueError):
    """Invalid or inconsistent defender policy."""


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PolicyError(f"duplicate JSON property: {key}")
        result[key] = value
    return result


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).casefold()).strip()


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        policy = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_pairs,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyError(f"cannot read defender policy: {exc}") from exc

    if not isinstance(policy, dict) or policy.get("schema") != "bav.red-sparrow-defender.v1":
        raise PolicyError("unsupported Red Sparrow policy schema")
    if not isinstance(policy.get("policy_id"), str) or not policy["policy_id"].strip():
        raise PolicyError("policy_id must be a non-empty string")
    if not isinstance(policy.get("categories"), list) or not policy["categories"]:
        raise PolicyError("at least one topic category is required")
    seen_ids: set[str] = set()
    for category in policy["categories"]:
        if not isinstance(category, dict):
            raise PolicyError("each category must be an object")
        category_id = category.get("id")
        terms = category.get("terms")
        if not isinstance(category_id, str) or not category_id.strip() or category_id in seen_ids:
            raise PolicyError("category IDs must be unique non-empty strings")
        if not isinstance(terms, list) or not terms or any(not isinstance(term, str) or not term.strip() for term in terms):
            raise PolicyError(f"category {category_id} must contain non-empty terms")
        seen_ids.add(category_id)

    for key in ("operational_intent_patterns", "defensive_context_patterns", "negation_patterns"):
        values = policy.get(key)
        if not isinstance(values, list) or any(not isinstance(item, str) or not item.strip() for item in values):
            raise PolicyError(f"{key} must be a list of non-empty strings")

    limits = policy.get("limits")
    decision = policy.get("decision")
    if not isinstance(limits, dict) or not isinstance(decision, dict):
        raise PolicyError("limits and decision must be objects")
    if decision.get("automatic_block") is not False or decision.get("automatic_quarantine") is not False:
        raise PolicyError("Red Sparrow triage must never automatically block or quarantine")
    for key in ("max_files", "max_file_bytes", "max_total_bytes"):
        if not isinstance(limits.get(key), int) or limits[key] <= 0:
            raise PolicyError(f"limits.{key} must be a positive integer")
    return policy


def _contains_any(text: str, patterns: list[str]) -> list[str]:
    return [pattern for pattern in patterns if _normalize(pattern) in text]


def _unnegated_intent(text: str, patterns: list[str], negations: list[str]) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        needle = _normalize(pattern)
        start = 0
        while True:
            index = text.find(needle, start)
            if index < 0:
                break
            prefix = text[max(0, index - 64):index]
            if not any(_normalize(negation) in prefix for negation in negations):
                found.append(pattern)
                break
            start = index + len(needle)
    return found


def _tracked_paths(root: Path, policy: dict[str, Any]) -> list[Path]:
    excluded = set(policy["limits"].get("excluded_directories", []))
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=5,
    )
    if result.returncode == 0 and result.stdout:
        paths = [Path(item.decode("utf-8", "surrogateescape"))
                 for item in result.stdout.split(b"\0") if item]
    else:
        paths = []
        for current, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(
                name for name in dirs
                if name not in excluded and not (Path(current) / name).is_symlink()
            )
            paths.extend((Path(current) / name).relative_to(root) for name in files)

    selected: list[Path] = []
    for path in paths:
        if any(part in excluded for part in path.parts) or path.as_posix().startswith(".git/"):
            continue
        if path.suffix.lower() not in set(policy["limits"]["text_extensions"]):
            continue
        selected.append(path)
        if len(selected) > int(policy["limits"]["max_files"]):
            raise PolicyError("workspace exceeds configured file scan limit")
    return sorted(selected, key=lambda item: item.as_posix())


def scan_repository(root: Path, policy_path: Path = POLICY_PATH) -> dict[str, Any]:
    root = root.resolve()
    policy = load_policy(policy_path)
    limits = policy["limits"]
    findings: list[dict[str, Any]] = []
    files_seen = text_files_scanned = total_bytes = 0

    for relative in _tracked_paths(root, policy):
        path = root / relative
        try:
            if path.is_symlink():
                continue
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(root):
                continue
            size = path.stat().st_size
            files_seen += 1
            total_bytes += size
            if total_bytes > int(limits["max_total_bytes"]):
                raise PolicyError("workspace exceeds configured total byte scan limit")
            if size > int(limits["max_file_bytes"]):
                continue
            raw = path.read_bytes()
            if b"\0" in raw:
                continue
            content = raw.decode("utf-8", errors="strict")
        except (OSError, RuntimeError, UnicodeDecodeError):
            continue

        text_files_scanned += 1
        for line_number, line in enumerate(content.splitlines(), 1):
            normalized = _normalize(line)
            if not normalized:
                continue
            topic_ids = [
                category["id"]
                for category in policy["categories"]
                if _contains_any(normalized, category["terms"])
            ]
            if not topic_ids:
                continue
            intent_matches = _unnegated_intent(
                normalized,
                policy["operational_intent_patterns"],
                policy["negation_patterns"],
            )
            if not intent_matches:
                continue
            context_matches = _contains_any(
                normalized,
                policy["defensive_context_patterns"],
            )
            findings.append({
                "rule_id": "RS-01",
                "severity": "high",
                "enforcement": "review",
                "path": relative.as_posix(),
                "line": line_number,
                "topic_ids": sorted(set(topic_ids)),
                "intent_categories": ["actionable_operational_language"],
                "defensive_context_present": bool(context_matches),
                "message": (
                    "Sensitive military/WMD topic and actionable operational language occur together; "
                    "manual safety review is required."
                ),
                "remediation": (
                    "Keep discussion at a non-operational, defensive, historical or policy level; "
                    "remove procedural weapon-use or construction guidance."
                ),
            })

    findings.sort(key=lambda item: (item["path"], item["line"], item["topic_ids"]))
    verdict = "review" if findings else "clear"
    return {
        "schema": "bav.red-sparrow-report.v1",
        "scanner": {"name": "Red Sparrow Guard", "version": policy["version"], "policy_id": policy["policy_id"]},
        "repository": root.name,
        "scan": {
            "files_seen": files_seen,
            "text_files_scanned": text_files_scanned,
            "read_only": True,
            "remote_access": False,
        },
        "verdict": verdict,
        "risk_score": min(100, len(findings) * 20),
        "findings_count": len(findings),
        "findings": findings,
        "safety": {
            "automatic_block": False,
            "automatic_quarantine": False,
            "country_or_nationality_alone_is_a_signal": False,
            "topic_reference_alone_is_a_finding": False,
            "human_review_required_for_findings": True,
        },
        "notes": [
            "A topic reference alone is not treated as harmful intent.",
            "A country or nationality is never a risk verdict.",
            "The scanner does not evaluate weapon capability, targeting, guidance or military readiness.",
            "A clean result is not a security certification.",
        ],
    }


def format_text(report: dict[str, Any]) -> str:
    lines = [
        f"Red Sparrow Guard {report['scanner']['version']} — {report['repository']}",
        f"Verdict: {report['verdict'].upper()} | risk score: {report['risk_score']}/100",
        f"Scanned: {report['scan']['text_files_scanned']} text files",
        f"Findings: {report['findings_count']} | automatic block: no",
    ]
    for item in report["findings"]:
        topics = ", ".join(item["topic_ids"])
        lines.append(
            f"[REVIEW] RS-01 {item['path']}:{item['line']} — topics: {topics}; "
            "manual review required"
        )
    if not report["findings"]:
        lines.append("No actionable topic/context combinations found.")
    lines.append("Read-only triage only; a clean scan is not a security certification.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only content-risk triage based on the Red Sparrow defender doctrine."
    )
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--strict-review", action="store_true")
    args = parser.parse_args(argv)

    try:
        report = scan_repository(args.root, args.policy)
    except (PolicyError, OSError, subprocess.TimeoutExpired) as exc:
        print(f"RED SPARROW POLICY ERROR: {exc}", file=sys.stderr)
        return 2

    encoded = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    print(encoded if args.json else format_text(report))
    return 1 if args.strict_review and report["verdict"] == "review" else 0


if __name__ == "__main__":
    raise SystemExit(main())
