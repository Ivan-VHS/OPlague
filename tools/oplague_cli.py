"""OPlague JSON registry, snapshot diff, INF evidence, and dry-run CLI."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from tools.device_registry import (
    RegistryError, append_snapshot, create_snapshot, load_registry, new_registry,
    save_registry, snapshot_diff,
)
from tools.dry_run import DryRunError, build_dry_run_plan, check_plan_freshness
from tools.inf_catalog import parse_inf_document
from tools.driver_compatibility import rank_inf_candidates


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_json(path: str) -> Any:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read {path}: {error}") from error


def _emit(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="oplague", description="Read-only OPlague registry and driver analysis tools")
    commands = parser.add_subparsers(dest="command", required=True)

    registry_parser = commands.add_parser("registry", help="create or validate a versioned JSON registry")
    registry_parser.add_argument("action", choices=("init", "validate"))
    registry_parser.add_argument("path")

    snapshot_parser = commands.add_parser("snapshot", help="create or compare device snapshots")
    snapshot_parser.add_argument("action", choices=("create", "diff"))
    snapshot_parser.add_argument("first", help="registry path for create; before snapshot for diff")
    snapshot_parser.add_argument("second", nargs="?", help="input JSON for create; after snapshot for diff")
    snapshot_parser.add_argument("--label", default="")

    dry_parser = commands.add_parser("dry-run", help="build or validate a non-applying operation plan")
    dry_parser.add_argument("action", choices=("plan", "freshness"))
    dry_parser.add_argument("input", help="plan input JSON or serialized plan JSON")
    dry_parser.add_argument("--current-digest")
    dry_parser.add_argument("--current-device")
    dry_parser.add_argument("--current-revision")

    compatibility_parser = commands.add_parser("compatibility", help="rank package INF ID evidence for one device")
    compatibility_parser.add_argument("device", help="device JSON file")
    compatibility_parser.add_argument("packages", help="package candidate JSON file")

    inf_parser = commands.add_parser("inf", help="extract direct device-ID evidence from an INF")
    inf_parser.add_argument("action", choices=("inspect",))
    inf_parser.add_argument("path")

    args = parser.parse_args(argv)
    try:
        if args.command == "registry":
            if args.action == "init":
                if Path(args.path).exists() or Path(args.path).is_symlink():
                    raise ValueError("registry init refuses to overwrite an existing path")
                registry = new_registry()
                save_registry(args.path, registry)
            else:
                registry = load_registry(args.path)
            _emit({"status": "valid", "schema": registry["schema"], "schema_version": registry["schema_version"],
                   "revision": registry["revision"], "devices": len(registry["devices"]),
                   "packages": len(registry["packages"]), "snapshots": len(registry["snapshots"])})
        elif args.command == "snapshot":
            if args.action == "diff":
                if not args.second:
                    raise ValueError("snapshot diff requires before and after JSON files")
                _emit(snapshot_diff(_read_json(args.first), _read_json(args.second)))
            else:
                if not args.second:
                    raise ValueError("snapshot create requires registry and snapshot-input JSON files")
                registry = load_registry(args.first)
                payload = _read_json(args.second)
                if not isinstance(payload, dict):
                    raise ValueError("snapshot input must be a JSON object")
                snapshot = create_snapshot(payload.get("devices", []), payload.get("packages", []),
                                           payload.get("metrics", {}), args.label or payload.get("label", ""),
                                           payload.get("captured_at"))
                updated = append_snapshot(registry, snapshot)
                save_registry(args.first, updated)
                _emit({"status": "saved", "revision": updated["revision"], "snapshot": snapshot})
        elif args.command == "dry-run":
            payload = _read_json(args.input)
            if not isinstance(payload, dict):
                raise ValueError("dry-run input must be a JSON object")
            if args.action == "plan":
                plan = build_dry_run_plan(**payload)
                _emit(plan)
                return 2 if plan["status"] == "blocked" else 0
            if not args.current_digest or not args.current_device:
                raise ValueError("dry-run freshness requires --current-digest and --current-device")
            revision: str | int | None = args.current_revision
            if revision is not None and revision.isdecimal():
                revision = int(revision)
            result = check_plan_freshness(payload, current_package_sha256=args.current_digest,
                                          current_device_instance_id=args.current_device,
                                          current_inventory_revision=revision)
            _emit(result)
            return 0 if result["fresh"] else 3
        elif args.command == "compatibility":
            device = _read_json(args.device)
            packages = _read_json(args.packages)
            if not isinstance(device, dict) or not isinstance(packages, list):
                raise ValueError("compatibility input must be a device object and package array")
            _emit({"schema": "oplage.compatibility-ranking.v1",
                   "results": rank_inf_candidates(device, packages)})
        elif args.command == "inf":
            raw = Path(args.path).read_bytes()
            if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
                content = raw.decode("utf-16")
            else:
                try:
                    content = raw.decode("utf-8-sig")
                except UnicodeDecodeError:
                    content = raw.decode("cp1252", errors="replace")
            _emit(parse_inf_document(content))
        return 0
    except (OSError, ValueError, TypeError, RegistryError, DryRunError) as error:
        print(f"oplague: error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
