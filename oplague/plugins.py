"""Read-only built-in plugin adapters for the OPlague workbench.

The adapters use only the Python standard library. They never load extensions,
execute inspected project code, access the network, install drivers, or modify
the inspected workspace.
"""
from __future__ import annotations

import ast
import hashlib
import os
import re
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class PluginSpec:
    plugin_id: str
    name: str
    domain: str
    operation: str
    capabilities: tuple[str, ...]
    version: str = "1.0.0"


PLUGIN_SPECS = (
    PluginSpec("operandu", "Operandu", "Data & logic", "inspect_value", ("value.validation", "schema.inspection")),
    PluginSpec("dropaul", "Dropaul", "Actions & workflows", "plan_workflow", ("workflow.validation", "dependency.ordering", "dry_run")),
    PluginSpec("zdoro", "Zdoro", "Integrity & diagnostics", "inspect_workspace", ("workspace.inspection", "baseline.check")),
    PluginSpec("pyemont", "Pyemont", "Development", "inspect_project", ("source.inventory", "module.discovery")),
    PluginSpec("dilly", "Dilly", "Interface & experience", "lint_design_tokens", ("token.validation", "duplicate.detection")),
    PluginSpec("baplap", "Baplap", "Data infrastructure", "index_files", ("file.catalog", "sha256.fingerprint")),
    PluginSpec("sretuo", "Sretuo", "Quality engineering", "plan_tests", ("test.discovery", "verification.plan")),
    PluginSpec("kali", "Kali", "Security", "scan_security", ("secret.pattern.scan", "static.findings")),
    PluginSpec("zalam", "Zalam", "Connectivity", "inspect_contracts", ("contract.validation", "version.check")),
    PluginSpec("liur", "Liur", "Runtime resources", "measure_resources", ("source.size.metrics", "resource.budget")),
    PluginSpec("keel-koh", "Keel Koh", "Knowledge", "index_knowledge", ("documentation.index", "heading.extraction", "local.link.inventory")),
    PluginSpec("vorof", "Vorof", "Reverse engineering", "inspect_structure", ("ast.inventory", "symbol.discovery", "dependency.outline")),
    PluginSpec("vprof", "Vprof", "Profiling & metrics", "profile_source", ("ast.metrics", "complexity.estimate")),
    PluginSpec("profe", "Profe", "Engineering standards", "check_standards", ("repository.conventions", "baseline.check")),
    PluginSpec("prossee", "Prossee", "Project planning", "plan_project", ("task.graph", "critical.path.estimate")),
    PluginSpec("vprossee", "Vprossee", "Verification & validation", "verify_evidence", ("evidence.matrix", "acceptance.check")),
    PluginSpec("professiya", "Professiya", "Learning", "learning_paths", ("learning.paths", "topic.map")),
    PluginSpec("profevo", "Profevo", "Evolution", "plan_evolution", ("version.compare", "migration.plan")),
)

_BY_ID = {spec.plugin_id: spec for spec in PLUGIN_SPECS}
_BY_NAME = {spec.name.casefold(): spec for spec in PLUGIN_SPECS}
_MAX_FILES = 5000
_MAX_FILE_BYTES = 2 * 1024 * 1024
_MAX_TOTAL_BYTES = 50 * 1024 * 1024
_IGNORED = {".git", ".venv", "venv", "__pycache__", "build", "dist", ".pytest_cache"}
_SECRET_PATTERNS = (
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("token-assignment", re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"][^'\"]{12,}")),
)


class PluginError(ValueError):
    """Invalid plugin name, disabled state, or bounded inspection input."""


def _root(path: str | Path | None) -> Path:
    root = Path(path or ".").expanduser().resolve()
    if not root.is_dir():
        raise PluginError(f"workspace directory does not exist: {root}")
    return root


def _files(root: Path, suffixes: tuple[str, ...] | None = None) -> list[Path]:
    result: list[Path] = []
    for current, dirs, names in os.walk(root, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in _IGNORED and not (Path(current) / d).is_symlink())
        for name in sorted(names):
            file = Path(current) / name
            if file.is_symlink() or not file.is_file():
                continue
            if suffixes is not None and file.suffix.lower() not in suffixes:
                continue
            result.append(file)
            if len(result) > _MAX_FILES:
                raise PluginError(f"workspace exceeds {_MAX_FILES} indexed files")
    return sorted(result)


def _read_text(path: Path) -> str:
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            raise PluginError(f"file exceeds {_MAX_FILE_BYTES} byte inspection limit: {path.name}")
        return path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise PluginError(f"file is not valid UTF-8: {path.name}") from exc


def inspect_value(value: Any, *, max_depth: int = 24, max_items: int = 20_000) -> dict[str, Any]:
    count = 0
    def visit(item: Any, depth: int) -> dict[str, Any]:
        nonlocal count
        count += 1
        if count > max_items or depth > max_depth:
            raise PluginError("value exceeds the configured inspection bounds")
        if item is None or isinstance(item, (str, bool, int, float)):
            if isinstance(item, str) and len(item) > 250_000:
                raise PluginError("string exceeds 250000 characters")
            if isinstance(item, float) and (item != item or abs(item) == float("inf")):
                raise PluginError("non-finite numbers are not supported")
            return {"type": type(item).__name__, "value": item}
        if isinstance(item, list):
            return {"type": "list", "length": len(item), "items": [visit(x, depth + 1) for x in item]}
        if isinstance(item, tuple):
            return {"type": "tuple", "length": len(item), "items": [visit(x, depth + 1) for x in item]}
        if isinstance(item, dict):
            if not all(isinstance(k, str) for k in item):
                raise PluginError("mapping keys must be strings")
            return {"type": "mapping", "length": len(item), "items": {k: visit(v, depth + 1) for k, v in item.items()}}
        raise PluginError(f"unsupported value type: {type(item).__name__}")
    return visit(value, 0)


def _topological_order(steps: list[dict[str, Any]]) -> tuple[list[str], dict[str, int]]:
    if not isinstance(steps, list) or len(steps) > 5000:
        raise PluginError("steps must be a list containing at most 5000 entries")
    by_id: dict[str, dict[str, Any]] = {}
    for step in steps:
        if not isinstance(step, dict):
            raise PluginError("each step must be an object")
        key = step.get("id")
        deps = step.get("depends_on", [])
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", key):
            raise PluginError(f"invalid step id: {key!r}")
        if key in by_id:
            raise PluginError(f"duplicate step id: {key}")
        if not isinstance(deps, list) or not all(isinstance(dep, str) for dep in deps):
            raise PluginError(f"depends_on for {key} must be a string list")
        duration = step.get("duration", 1)
        if isinstance(duration, bool) or not isinstance(duration, int) or not 0 <= duration <= 1_000_000:
            raise PluginError(f"invalid duration for {key}")
        by_id[key] = step
    incoming = {key: set(item.get("depends_on", [])) for key, item in by_id.items()}
    for key, deps in incoming.items():
        missing = deps - by_id.keys()
        if missing:
            raise PluginError(f"{key} depends on unknown step(s): {', '.join(sorted(missing))}")
        if key in deps:
            raise PluginError(f"{key} cannot depend on itself")
    ready = deque(sorted(k for k, deps in incoming.items() if not deps))
    order: list[str] = []
    finish: dict[str, int] = {}
    while ready:
        current = ready.popleft()
        order.append(current)
        duration = int(by_id[current].get("duration", 1))
        start = max((finish[d] for d in by_id[current].get("depends_on", [])), default=0)
        finish[current] = start + duration
        for candidate in sorted(incoming):
            if current in incoming[candidate]:
                incoming[candidate].remove(current)
                if not incoming[candidate] and candidate not in order and candidate not in ready:
                    ready.append(candidate)
    if len(order) != len(by_id):
        raise PluginError("workflow contains a dependency cycle")
    return order, finish


def plan_workflow(steps: list[dict[str, Any]]) -> dict[str, Any]:
    order, _ = _topological_order(steps)
    return {"valid": True, "dry_run": True, "step_count": len(order), "execution_order": order}


def inspect_workspace(path: str | Path | None = None) -> dict[str, Any]:
    root = _root(path)
    required = ("README.md", "LICENSE", "tests", "docs")
    missing = [item for item in required if not (root / item).exists()]
    files = _files(root, (".py",))
    return {"root": str(root), "python_files": len(files), "test_directory": (root / "tests").is_dir(),
            "docs_directory": (root / "docs").is_dir(), "missing_baseline": missing, "healthy_baseline": not missing}


def inspect_project(path: str | Path | None = None) -> dict[str, Any]:
    root = _root(path)
    files = _files(root)
    by_ext: dict[str, int] = {}
    for file in files:
        ext = file.suffix.lower() or "[no extension]"
        by_ext[ext] = by_ext.get(ext, 0) + 1
    return {"root": str(root), "file_count": len(files), "by_extension": dict(sorted(by_ext.items())),
            "top_level": sorted(item.name for item in root.iterdir())}


def lint_design_tokens(tokens: dict[str, str]) -> dict[str, Any]:
    if not isinstance(tokens, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in tokens.items()):
        raise PluginError("tokens must be a string-to-string mapping")
    values: dict[str, list[str]] = {}
    for key, value in tokens.items():
        values.setdefault(value.casefold(), []).append(key)
    return {"token_count": len(tokens), "empty_tokens": sorted(k for k, v in tokens.items() if not v.strip()),
            "duplicate_values": [names for names in values.values() if len(names) > 1]}


def index_files(path: str | Path | None = None, *, suffixes: tuple[str, ...] = (".py", ".md", ".json", ".toml")) -> dict[str, Any]:
    root = _root(path)
    rows = []
    total = 0
    for file in _files(root, suffixes):
        with file.open("rb") as stream:
            payload = stream.read(_MAX_FILE_BYTES + 1)
        size = len(payload)
        if size > _MAX_FILE_BYTES:
            raise PluginError(f"file exceeds {_MAX_FILE_BYTES} byte limit: {file.name}")
        total += size
        if total > _MAX_TOTAL_BYTES:
            raise PluginError(f"index exceeds {_MAX_TOTAL_BYTES} total bytes")
        rows.append({"path": file.relative_to(root).as_posix(), "size_bytes": size, "sha256": hashlib.sha256(payload).hexdigest()})
    return {"root": str(root), "count": len(rows), "total_bytes": total, "entries": rows}


def plan_tests(path: str | Path | None = None) -> dict[str, Any]:
    root = _root(path)
    test_root = root / "tests"
    files = _files(test_root, (".py",)) if test_root.is_dir() else []
    names = [file.relative_to(root).as_posix() for file in files if file.name.startswith("test_")]
    return {"discovered": len(names), "tests": names, "recommendation": "Add regression coverage for every changed public behavior."}


def scan_security(path: str | Path | None = None) -> dict[str, Any]:
    root = _root(path)
    findings = []
    scanned = 0
    for file in _files(root, (".py", ".toml", ".yml", ".yaml", ".json", ".env")):
        try:
            source = _read_text(file)
        except (OSError, PluginError):
            continue
        scanned += 1
        for rule, pattern in _SECRET_PATTERNS:
            for match in pattern.finditer(source):
                findings.append({"rule": rule, "path": file.relative_to(root).as_posix(),
                                 "line": source.count("\n", 0, match.start()) + 1})
    return {"scanned_files": scanned, "finding_count": len(findings), "findings": findings,
            "scope": "bounded static pattern scan; not a complete security audit"}


def inspect_contracts(contracts: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(contracts, list) or len(contracts) > 5000:
        raise PluginError("contracts must be a list of at most 5000 entries")
    seen: set[str] = set()
    issues = []
    for index, item in enumerate(contracts):
        if not isinstance(item, dict):
            issues.append({"index": index, "issue": "entry is not an object"})
            continue
        name, version = item.get("name"), item.get("version")
        if not isinstance(name, str) or not name.strip():
            issues.append({"index": index, "issue": "missing contract name"})
        elif name in seen:
            issues.append({"index": index, "issue": f"duplicate contract name: {name}"})
        else:
            seen.add(name)
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", version):
            issues.append({"index": index, "issue": "version must use numeric semantic components"})
    return {"contract_count": len(contracts), "valid": not issues, "issues": issues}


def measure_resources(path: str | Path | None = None) -> dict[str, Any]:
    root = _root(path)
    files = _files(root)
    total = 0
    largest = []
    for file in files:
        size = file.stat().st_size
        total += size
        largest.append((size, file.relative_to(root).as_posix()))
    largest.sort(reverse=True)
    return {"file_count": len(files), "total_bytes": total,
            "largest_files": [{"path": name, "size_bytes": size} for size, name in largest[:10]],
            "scope": "on-disk source tree sizes; no process or hardware telemetry"}


def index_knowledge(path: str | Path | None = None) -> dict[str, Any]:
    root = _root(path)
    docs = root / "docs"
    files = _files(docs, (".md", ".mdx")) if docs.is_dir() else []
    rows = []
    for file in files:
        text = _read_text(file)
        headings = [line.lstrip("# ").strip() for line in text.splitlines() if re.match(r"^#{1,6}\s+", line)]
        links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
        local = [link.split("#", 1)[0] for link in links if link and not re.match(r"^[a-z][a-z0-9+.-]*:", link, re.I) and not link.startswith("#")]
        rows.append({"path": file.relative_to(root).as_posix(), "headings": headings[:100], "local_links": local[:200]})
    return {"documents": len(rows), "index": rows}


def inspect_structure(path: str | Path | None = None) -> dict[str, Any]:
    root = _root(path)
    modules = []
    for file in _files(root, (".py",)):
        source = _read_text(file)
        try:
            tree = ast.parse(source, filename=str(file))
        except SyntaxError as exc:
            modules.append({"path": file.relative_to(root).as_posix(), "syntax_error": exc.msg, "line": exc.lineno})
            continue
        imports = []
        symbols = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbols.append({"kind": "class" if isinstance(node, ast.ClassDef) else "function", "name": node.name, "line": node.lineno})
        modules.append({"path": file.relative_to(root).as_posix(), "imports": sorted(set(imports)), "symbols": symbols[:500]})
    return {"module_count": len(modules), "modules": modules, "execution": "source parsed as syntax only; no project code executed"}


def profile_source(path: str | Path | None = None) -> dict[str, Any]:
    structure = inspect_structure(path)
    functions = classes = branches = syntax_errors = 0
    for module in structure["modules"]:
        syntax_errors += int("syntax_error" in module)
        for symbol in module.get("symbols", []):
            functions += symbol["kind"] == "function"
            classes += symbol["kind"] == "class"
    root = _root(path)
    for file in _files(root, (".py",)):
        try:
            tree = ast.parse(_read_text(file), filename=str(file))
        except SyntaxError:
            continue
        branches += sum(isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.Match)) for node in ast.walk(tree))
    return {"modules": structure["module_count"], "functions": functions, "classes": classes,
            "branch_nodes": branches, "syntax_error_modules": syntax_errors,
            "scope": "AST estimates; not runtime profiling"}


def check_standards(path: str | Path | None = None) -> dict[str, Any]:
    root = _root(path)
    required = ("README.md", "LICENSE", "pyproject.toml", "tests", "docs")
    missing = [item for item in required if not (root / item).exists()]
    readme = root / "README.md"
    has_heading = readme.is_file() and any(line.startswith("# ") for line in _read_text(readme).splitlines())
    return {"valid": not missing and has_heading, "missing": missing,
            "readme_has_title": has_heading, "checks": list(required) + ["README title"]}


def plan_project(steps: list[dict[str, Any]]) -> dict[str, Any]:
    order, finish = _topological_order(steps)
    return {"valid": True, "dry_run": True, "ordered_steps": order,
            "estimated_critical_path_units": max(finish.values(), default=0),
            "finish_by_step": finish, "no_tasks_executed": True}


def verify_evidence(evidence: list[dict[str, Any]], path: str | Path | None = None) -> dict[str, Any]:
    if not isinstance(evidence, list) or len(evidence) > 5000:
        raise PluginError("evidence must be a list of at most 5000 entries")
    root = _root(path)
    rows = []
    for index, item in enumerate(evidence):
        issues = []
        if not isinstance(item, dict):
            rows.append({"index": index, "valid": False, "issues": ["entry is not an object"]})
            continue
        for key in ("id", "claim", "source"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                issues.append(f"missing {key}")
        source = item.get("source")
        if isinstance(source, str) and source:
            candidate = (root / source).resolve()
            try:
                candidate.relative_to(root)
            except ValueError:
                issues.append("source escapes workspace root")
            else:
                if not candidate.is_file():
                    issues.append("source file does not exist")
        rows.append({"index": index, "id": item.get("id"), "valid": not issues, "issues": issues,
                     "verified": bool(item.get("verified", False))})
    return {"valid": all(row["valid"] for row in rows), "evidence_count": len(rows), "rows": rows,
            "note": "source existence is checked; claim truth is not independently certified"}


def learning_paths(path: str | Path | None = None) -> dict[str, Any]:
    root = _root(path)
    index = index_knowledge(root)
    paths = []
    for doc in index["index"]:
        topics = doc["headings"]
        if topics:
            paths.append({"document": doc["path"], "steps": topics[:20]})
    return {"learning_paths": len(paths), "paths": paths,
            "basis": "repository documentation headings; no external content is fetched"}


def plan_evolution(current_version: str, target_version: str) -> dict[str, Any]:
    pattern = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
    current = pattern.fullmatch(current_version) if isinstance(current_version, str) else None
    target = pattern.fullmatch(target_version) if isinstance(target_version, str) else None
    if not current or not target:
        raise PluginError("versions must use MAJOR.MINOR.PATCH semantic form")
    old = tuple(map(int, current.groups()))
    new = tuple(map(int, target.groups()))
    if new <= old:
        raise PluginError("target version must be greater than current version")
    if new[0] > old[0]:
        level = "major"
        actions = ["review breaking API changes", "prepare migration notes", "add compatibility tests", "stage deprecations"]
    elif new[1] > old[1]:
        level = "minor"
        actions = ["review additive API changes", "preserve existing defaults", "add feature tests", "update documentation"]
    else:
        level = "patch"
        actions = ["review fixes", "add regression tests", "update changelog"]
    return {"current": current_version, "target": target_version, "change_level": level,
            "dry_run": True, "actions": actions, "files_modified": False}


_HANDLERS: dict[str, Callable[..., Any]] = {
    "inspect_value": inspect_value, "plan_workflow": plan_workflow,
    "inspect_workspace": inspect_workspace, "inspect_project": inspect_project,
    "lint_design_tokens": lint_design_tokens, "index_files": index_files,
    "plan_tests": plan_tests, "scan_security": scan_security,
    "inspect_contracts": inspect_contracts, "measure_resources": measure_resources,
    "index_knowledge": index_knowledge, "inspect_structure": inspect_structure,
    "profile_source": profile_source, "check_standards": check_standards,
    "plan_project": plan_project, "verify_evidence": verify_evidence,
    "learning_paths": learning_paths, "plan_evolution": plan_evolution,
}


class PluginManager:
    """Dispatch the 18 reviewed OPlague adapters; arbitrary extensions stay disabled."""

    def __init__(self, enabled: Iterable[str] | None = None) -> None:
        self._enabled = set(_BY_ID) if enabled is None else set()
        if enabled is not None:
            for name in enabled:
                self._enabled.add(self._resolve(name).plugin_id)

    def _resolve(self, name: str) -> PluginSpec:
        if not isinstance(name, str):
            raise PluginError("plugin identifier must be text")
        key = name.strip().casefold()
        spec = _BY_ID.get(key) or _BY_NAME.get(key)
        if spec is None:
            raise PluginError(f"unknown OPlague plugin: {name!r}")
        return spec

    def list_plugins(self) -> list[dict[str, Any]]:
        rows = []
        for spec in PLUGIN_SPECS:
            row = asdict(spec)
            row.update(enabled=spec.plugin_id in self._enabled,
                       host="oplague-python", mode="read-only-adapter")
            rows.append(row)
        return rows

    def get_plugin(self, name: str) -> PluginSpec:
        return self._resolve(name)

    def set_enabled(self, name: str, enabled: bool) -> bool:
        spec = self._resolve(name)
        if not isinstance(enabled, bool):
            raise PluginError("enabled state must be boolean")
        if enabled:
            self._enabled.add(spec.plugin_id)
        else:
            self._enabled.discard(spec.plugin_id)
        return enabled

    def run(self, name: str, **arguments: Any) -> Any:
        spec = self._resolve(name)
        if spec.plugin_id not in self._enabled:
            raise PluginError(f"plugin {spec.name} is disabled")
        try:
            return _HANDLERS[spec.operation](**arguments)
        except PluginError:
            raise
        except (TypeError, ValueError, OSError) as exc:
            raise PluginError(f"{spec.name} rejected the request: {exc}") from exc


def list_plugins() -> list[dict[str, Any]]:
    return PluginManager().list_plugins()
