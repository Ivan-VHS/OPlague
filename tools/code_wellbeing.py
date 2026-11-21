"""Codebase wellbeing inventory for OPlague.

This is an explicitly non-clinical, read-only engineering metaphor. It is
separate from device inspection, driver analytics and contributor telemetry.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

CHARTER_PATH = Path(__file__).resolve().parents[1] / "data" / "code-wellbeing" / "codebase-wellbeing.v1.json"
MAX_FILES = 5000
MAX_DEPTH = 16
MAX_FILE_BYTES = 1024 * 1024
SKIP_DIRS = {".git", "build", "dist", "target", "vendor", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache"}
SOURCE_EXTENSIONS = {".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hxx", ".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go", ".java", ".cs", ".rpr", ".qcs", ".lua"}
DOC_EXTENSIONS = {".md", ".mdx", ".rst", ".adoc"}
DEPENDENCY_FILES = {"pyproject.toml", "requirements.txt", "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "Cargo.toml", "Cargo.lock", "go.mod", "go.sum", "poetry.lock", "Pipfile", "Pipfile.lock", "vcpkg.json", "conanfile.py", "conanfile.txt"}
MARKERS = ("TODO", "FIXME", "HACK", "XXX")


class CodeWellbeingError(ValueError):
    """Invalid scan root or code-wellbeing charter."""


def load_charter(path: Path = CHARTER_PATH) -> dict[str, Any]:
    try:
        if path.stat().st_size > 256 * 1024:
            raise CodeWellbeingError("charter exceeds 256 KiB")
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise CodeWellbeingError(f"cannot read charter: {error}") from error
    except (UnicodeError, json.JSONDecodeError) as error:
        raise CodeWellbeingError(f"invalid charter JSON: {error}") from error
    concept = value.get("concept") if isinstance(value, dict) else None
    if (not isinstance(concept, dict) or concept.get("id") != "code-mental-health"
            or concept.get("is_engineering_metaphor") is not True
            or concept.get("clinical_equivalence") is not False):
        raise CodeWellbeingError("charter must remain a non-clinical engineering metaphor")
    return value


def _is_test_file(path: Path) -> bool:
    parts = {x.casefold() for x in path.parts}
    name = path.name.casefold()
    return bool(parts & {"test", "tests", "testing", "spec", "specs"}) or name.startswith(("test_", "test.")) or name.endswith(("_test.py", ".spec.js", ".test.js", ".spec.ts", ".test.ts"))


def scan_project(root: str | Path = ".") -> dict[str, Any]:
    charter = load_charter()
    requested_root = Path(root).expanduser()
    if requested_root.is_symlink():
        raise CodeWellbeingError("project root must not be a symbolic link")
    project = requested_root.resolve()
    if not project.is_dir():
        raise CodeWellbeingError(f"project root is not a directory: {project}")
    files: list[Path] = []
    truncated = False
    for current, dirs, filenames in os.walk(project, topdown=True, followlinks=False):
        here = Path(current)
        depth = len(here.relative_to(project).parts)
        dirs[:] = sorted(name for name in dirs
                         if name.casefold() not in SKIP_DIRS and not (here / name).is_symlink())
        if depth >= MAX_DEPTH:
            dirs[:] = []
        for filename in sorted(filenames):
            path = here / filename
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                files.append(path)
            except OSError:
                continue
            if len(files) >= MAX_FILES:
                truncated = True
                break
        if truncated:
            break
    relative = [path.relative_to(project) for path in files]
    source = [p for p in relative if p.suffix.casefold() in SOURCE_EXTENSIONS]
    tests = [p for p in source if _is_test_file(p)]
    docs = [p for p in relative if p.suffix.casefold() in DOC_EXTENSIONS]
    readmes = [p for p in relative if p.name.casefold().startswith("readme")]
    workflows = [p for p in relative if ".github/workflows" in p.as_posix().casefold()
                 or p.name.casefold() in {".gitlab-ci.yml", "azure-pipelines.yml", "bitbucket-pipelines.yml"}]
    owners = [p for p in relative if p.name.casefold() == "codeowners"]
    dependencies = [p for p in relative if p.name in DEPENDENCY_FILES]
    recovery = [p for p in relative if any(k in p.name.casefold() for k in ("rollback", "runbook", "recovery", "release-process"))]
    learning = [p for p in relative if any(k in p.name.casefold() for k in ("postmortem", "post-mortem", "incident", "adr"))]

    markers = {marker: 0 for marker in MARKERS}
    large: list[str] = []
    scanned = 0
    for item in source:
        absolute = project / item
        try:
            if absolute.stat().st_size > MAX_FILE_BYTES:
                continue
            lines = absolute.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        scanned += 1
        if len(lines) > 1000 and len(large) < 100:
            large.append(item.as_posix())
        for line in lines:
            for marker in MARKERS:
                if marker in line:
                    markers[marker] += 1

    signals = [
        {"id":"verification","status":"observed" if tests and workflows else "missing",
         "evidence":[p.as_posix() for p in tests[:5]+workflows[:5]],
         "note":"Test and CI file presence does not prove coverage, test quality or passing status."},
        {"id":"documentation","status":"observed" if readmes else "missing",
         "evidence":[p.as_posix() for p in readmes[:5]],
         "note":"README presence does not prove accuracy or freshness."},
        {"id":"ownership-and-support","status":"observed" if owners else "unknown",
         "evidence":[p.as_posix() for p in owners[:5]],
         "note":"No ownership file is not proof that maintainers are unavailable."},
        {"id":"dependency-care","status":"observed" if dependencies else "unknown",
         "evidence":[p.as_posix() for p in dependencies[:10]],
         "note":"Manifest presence does not prove dependency freshness or safety."},
        {"id":"change-safety","status":"observed" if recovery else "unknown",
         "evidence":[p.as_posix() for p in recovery[:10]],
         "note":"A runbook name does not prove recovery has been rehearsed."},
        {"id":"incident-learning","status":"observed" if learning else "unknown",
         "evidence":[p.as_posix() for p in learning[:10]],
         "note":"Record presence does not prove that lessons have been applied."},
        {"id":"maintainability-review-cues","status":"observed",
         "evidence":[f"{k}={v}" for k,v in markers.items()]+[f"large_source_units_over_1000_lines={len(large)}"],
         "note":"Maintenance markers and large files are review prompts, not automatic defects."}
    ]
    return {
        "schema_version":1,"concept":charter["concept"]["name"],"project":project.name,
        "scan":{"read_only":True,"truncated_at_file_limit":truncated,"file_limit":MAX_FILES,
                "depth_limit":MAX_DEPTH,"max_source_file_bytes_scanned":MAX_FILE_BYTES},
        "inventory":{"total_files":len(files),"source_files":len(source),"test_files":len(tests),
                     "documentation_files":len(docs),"readme_files":len(readmes),"ci_workflow_files":len(workflows),
                     "ownership_files":len(owners),"dependency_manifest_files":len(dependencies),
                     "recovery_guides":len(recovery),"incident_or_decision_records":len(learning),
                     "source_files_text_scanned":scanned,"maintenance_markers":markers,
                     "large_source_units_over_1000_lines":large},
        "signals":signals,
        "reporting_note":"No overall mental-health or code-quality score is computed. Signals describe visible repository evidence only.",
        "privacy_note":"No contributor activity, commit timing, device, hardware, audio or external-service telemetry is inspected."
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Code Mental Health / Codebase Wellbeing inventory.")
    parser.add_argument("path", nargs="?", default=".", help="repository root (default: current directory)")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args(argv)
    try:
        report = scan_project(args.path)
    except CodeWellbeingError as error:
        parser.exit(2, f"code-wellbeing: {error}\n")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        inv = report["inventory"]
        print("Code Mental Health / Codebase Wellbeing v1")
        print(f"Project: {report['project']} | files: {inv['total_files']} | source: {inv['source_files']} | tests: {inv['test_files']}")
        print(f"Docs: {inv['documentation_files']} | CI workflows: {inv['ci_workflow_files']} | source text inspected: {inv['source_files_text_scanned']}")
        for signal in report["signals"]:
            print(f"- {signal['id']}: {signal['status']} — {signal['note']}")
        print(f"Review markers: {inv['maintenance_markers']}")
        print(report["reporting_note"])
        print(report["privacy_note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
