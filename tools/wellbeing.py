"""Read-only mental wellbeing awareness reference for OPlague.

The bundle is educational, transcript-attributed content, not a clinical system.
It is intentionally separate from device and driver telemetry.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

RESOURCE_PATH = Path(__file__).resolve().parents[1] / "data" / "wellbeing" / "depression-awareness.v1.json"
MAX_RESOURCE_BYTES = 256 * 1024


class WellbeingReferenceError(ValueError):
    """Invalid source bundle or missing safety boundary."""


def load_reference(path: Path = RESOURCE_PATH) -> dict[str, Any]:
    try:
        if path.stat().st_size > MAX_RESOURCE_BYTES:
            raise WellbeingReferenceError("reference exceeds 256 KiB")
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise WellbeingReferenceError(f"cannot read reference: {error}") from error
    except (UnicodeError, json.JSONDecodeError) as error:
        raise WellbeingReferenceError(f"invalid reference JSON: {error}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise WellbeingReferenceError("unsupported reference schema")
    source = payload.get("source")
    coverage = payload.get("transcript_coverage")
    topics = payload.get("topics")
    guardrails = payload.get("guardrails")
    if not isinstance(source, dict) or not str(source.get("video_url", "")).startswith("https://www.youtube.com/watch?v="):
        raise WellbeingReferenceError("source provenance is missing")
    if not isinstance(coverage, dict) or coverage.get("missing_middle") is not True:
        raise WellbeingReferenceError("missing transcript interval must remain explicit")
    segments = coverage.get("available_segments")
    if not isinstance(segments, list) or not segments:
        raise WellbeingReferenceError("transcript segment metadata is missing")
    for segment in segments:
        if not isinstance(segment, dict):
            raise WellbeingReferenceError("invalid transcript segment")
        start, end = segment.get("start_seconds"), segment.get("end_seconds")
        if type(start) is not int or type(end) is not int or start < 0 or end <= start:
            raise WellbeingReferenceError("invalid transcript segment bounds")
    if not isinstance(topics, list) or not topics:
        raise WellbeingReferenceError("topic catalogue is empty")
    identifiers: set[str] = set()
    for topic in topics:
        if not isinstance(topic, dict):
            raise WellbeingReferenceError("topic entries must be objects")
        key = topic.get("id")
        if not isinstance(key, str) or not key or key in identifiers:
            raise WellbeingReferenceError("topic IDs must be unique non-empty strings")
        identifiers.add(key)
        if topic.get("evidence_status") not in {"transcript_excerpt", "insufficient_transcript"}:
            raise WellbeingReferenceError(f"unknown evidence status for {key}")
        if not isinstance(topic.get("summary"), str) or not topic["summary"].strip():
            raise WellbeingReferenceError(f"empty topic summary: {key}")
        stamps = topic.get("timestamps_seconds")
        if not isinstance(stamps, list) or any(type(x) is not int or x < 0 for x in stamps):
            raise WellbeingReferenceError(f"invalid timestamps for {key}")
    missing = next((x for x in topics if x["id"] == "antidepressant-myths"), None)
    if missing and (missing["evidence_status"] != "insufficient_transcript" or missing["timestamps_seconds"]):
        raise WellbeingReferenceError("antidepressant-myths is not evidenced by the supplied excerpts")
    if not isinstance(guardrails, list) or len(guardrails) < 6:
        raise WellbeingReferenceError("safety guardrails are missing")
    joined = " ".join(x for x in guardrails if isinstance(x, str)).casefold()
    for phrase in ("не медичний", "не проводити самодіагностику", "не призначати", "домислами"):
        if phrase not in joined:
            raise WellbeingReferenceError(f"safety guardrail is missing: {phrase}")
    return payload


def get_topic(topic_id: str) -> dict[str, Any]:
    payload = load_reference()
    for topic in payload["topics"]:
        if topic["id"] == topic_id:
            return topic
    raise KeyError(f"unknown wellbeing topic: {topic_id}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect the offline mental wellbeing awareness reference.")
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--catalog", action="store_true")
    choice.add_argument("--topic", metavar="ID")
    parser.add_argument("--json", action="store_true", help="emit structured JSON")
    args = parser.parse_args(argv)
    try:
        payload = load_reference()
        if args.topic:
            topic = get_topic(args.topic)
            result = {"source": payload["source"], "topic": topic}
            output = json.dumps(result, ensure_ascii=False, indent=2) if args.json else (
                f"{topic['title']}\n{topic['summary']}\nEvidence: {topic['evidence_status']}"
            )
        else:
            result = payload
            output = json.dumps(result, ensure_ascii=False, indent=2) if args.json else (
                "Mental Wellbeing & Depression Awareness v1\n"
                f"Source: {payload['source']['channel']} — {payload['source']['title']}\n"
                "Transcript excerpts only: 00:00–00:07:55 and 01:17:16–01:19:53.\n"
                "Middle section unavailable; no diagnosis, screening or treatment advice.\n"
                + "\n".join(f"- {x['id']} [{x['evidence_status']}]: {x['title']}" for x in payload["topics"])
            )
    except (WellbeingReferenceError, KeyError) as error:
        parser.exit(2, f"oplague wellbeing: {error}\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
