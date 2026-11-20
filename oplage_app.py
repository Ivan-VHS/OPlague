"""OPlague read-only Windows desktop workbench."""
from __future__ import annotations
import hashlib
import json
import os
import re
import subprocess
import tkinter as tk
import zipfile
from pathlib import Path, PurePosixPath
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any

from tools.report_composer import compose_inspection_reports
from tools.metric_analysis import analyze_device_profiles
from tools.architecture_profiles import current_host_architecture, detect_inf_target_architectures, evaluate_driver_targets

MAX_PACKAGE_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 10_000
MAX_EXPANDED_BYTES = 2 * 1024 * 1024 * 1024
MAX_INF_BYTES = 2 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200

def parse_inf_text(content: str) -> dict[str, str]:
    """Extract selected values from the [Version] section of a Windows INF."""
    values: dict[str, str] = {}
    active = False
    wanted = {"provider", "class", "classguid", "driverver", "catalogfile", "catalogfile.nt"}
    for raw in content.lstrip("\ufeff").splitlines():
        line = raw.strip()
        if not line or line.startswith((";", "#")):
            continue
        if line.startswith("[") and line.endswith("]"):
            active = line[1:-1].strip().casefold() == "version"
        elif active and "=" in line:
            key, value = line.split("=", 1)
            key = key.strip().casefold()
            if key in wanted and key not in values:
                values[key] = value.strip().strip('"')
    return values

def _decode_inf(data: bytes) -> str:
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")

def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def _inf(data: bytes, label: str) -> dict[str, str]:
    if len(data) > MAX_INF_BYTES:
        raise ValueError(f"INF file is too large to inspect: {label}")
    return parse_inf_text(_decode_inf(data))

def _safe_archive_name(name: str) -> None:
    normalized = name.replace("\\", "/")
    parsed = PurePosixPath(normalized)
    if parsed.is_absolute() or ".." in parsed.parts or "\x00" in normalized or re.match(r"^[A-Za-z]:", normalized):
        raise ValueError(f"Unsafe archive path detected: {name}")

def inspect_package(filename: str | Path) -> dict[str, Any]:
    """Inspect INF or ZIP metadata without extracting or executing driver content."""
    path = Path(filename).expanduser()
    if not path.is_file():
        raise FileNotFoundError(f"Package file not found: {path}")
    size = path.stat().st_size
    if size > MAX_PACKAGE_BYTES:
        raise ValueError("Package exceeds the 512 MiB inspection limit")
    suffix = path.suffix.casefold()
    report: dict[str, Any] = {
        "file_name": path.name, "path": str(path.resolve()), "size_bytes": size,
        "sha256": _hash_file(path), "format": suffix.lstrip(".").upper(),
    }
    if suffix == ".inf":
        raw_inf = path.read_bytes()
        report["inf_metadata"] = _inf(raw_inf, path.name)
        targets = detect_inf_target_architectures(_decode_inf(raw_inf))
        report["architecture_targets"] = targets
        report["target_analysis"] = evaluate_driver_targets(current_host_architecture() or "unknown", targets)
        return report
    if suffix != ".zip":
        raise ValueError("Supported package formats are .inf and .zip")
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ARCHIVE_ENTRIES:
                raise ValueError("Archive contains more than 10,000 entries")
            expanded, inf_files = 0, []
            for entry in entries:
                _safe_archive_name(entry.filename)
                if entry.is_dir():
                    continue
                expanded += entry.file_size
                if expanded > MAX_EXPANDED_BYTES:
                    raise ValueError("Archive exceeds the expanded-size inspection limit")
                if entry.file_size and not entry.compress_size:
                    raise ValueError(f"Suspicious compressed entry: {entry.filename}")
                if entry.compress_size and entry.file_size / entry.compress_size > MAX_COMPRESSION_RATIO:
                    raise ValueError(f"Suspicious compression ratio: {entry.filename}")
                if entry.filename.casefold().endswith(".inf"):
                    if entry.file_size > MAX_INF_BYTES:
                        raise ValueError(f"INF file exceeds the 2 MiB inspection limit: {entry.filename}")
                    raw_inf = archive.read(entry)
                    metadata = _inf(raw_inf, entry.filename)
                    targets = detect_inf_target_architectures(_decode_inf(raw_inf))
                    inf_files.append({
                        "file": entry.filename,
                        "metadata": metadata,
                        "architecture_targets": targets,
                        "target_analysis": evaluate_driver_targets(current_host_architecture() or "unknown", targets),
                    })
            report.update({
                "entry_count": len(entries), "expanded_size_bytes": expanded,
                "inf_files": inf_files,
                "catalog_files": [item.filename for item in entries if not item.is_dir() and item.filename.casefold().endswith(".cat")],
                "inspection": "Metadata-only; contents were not extracted or executed",
            })
            return report
    except zipfile.BadZipFile as error:
        raise ValueError(f"Invalid ZIP archive: {error}") from error

def list_pnp_devices(timeout_seconds: int = 30) -> list[dict[str, str]]:
    """Read local Plug and Play data through a fixed Windows CIM query."""
    if os.name != "nt":
        raise RuntimeError("Hardware inventory is currently available only on Windows")
    command = ("$ErrorActionPreference = 'Stop'; "
      "$devices = @(Get-CimInstance -ClassName Win32_PnPEntity | "
      "Select-Object Name, Status, Manufacturer, PNPDeviceID); "
      "ConvertTo-Json -InputObject $devices -Depth 3 -Compress")
    result = subprocess.run(
      ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
      capture_output=True, text=True, encoding="utf-8", errors="replace",
      timeout=timeout_seconds, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Windows device query failed")
    output = result.stdout.strip().lstrip("\ufeff")
    if not output:
        return []
    payload = json.loads(output)
    if isinstance(payload, dict):
        payload = [payload]
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected device inventory response")
    return [{
      "name": str(row.get("Name") or "Unknown device"),
      "status": str(row.get("Status") or "Unknown"),
      "manufacturer": str(row.get("Manufacturer") or ""),
      "pnp_id": str(row.get("PNPDeviceID") or ""),
    } for row in payload if isinstance(row, dict)]

class OPlagueApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("OPlague — Driver Workbench")
        self.geometry("1120x720")
        self.minsize(820, 540)
        self.option_add("*Font", ("Segoe UI", 10))
        header = ttk.Frame(self, padding=(16, 12)); header.pack(fill="x")
        ttk.Label(header, text="OPLAGUE", font=("Segoe UI Semibold", 20)).pack(side="left")
        ttk.Label(header, text="Hardware inventory  /  Driver package inspection", foreground="#526174").pack(side="left", padx=16)
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        inventory = ttk.Frame(self.tabs, padding=12); packages = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(inventory, text="Device inventory"); self.tabs.add(packages, text="Package inspector")
        metrics = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(metrics, text="Metric Lab")
        ttk.Label(
            metrics,
            text="Compare normalized hardware / benchmark profiles using n-D metrics and weighted quadratic distance.",
            foreground="#526174",
        ).pack(anchor="w", pady=(0, 8))
        metric_inputs = ttk.Frame(metrics)
        metric_inputs.pack(fill="x", expand=False)
        profile_defaults = (
            ("reference", "Reference profile", '{"cpu_score": 0.82, "memory_score": 0.71, "thermal_headroom": 0.68}'),
            ("candidate", "Candidate profile", '{"cpu_score": 0.88, "memory_score": 0.66, "thermal_headroom": 0.74}'),
            ("weights", "Metric weights (optional)", '{"cpu_score": 1.0, "memory_score": 1.5, "thermal_headroom": 1.0}'),
        )
        for column, (key, label, default_value) in enumerate(profile_defaults):
            panel = ttk.LabelFrame(metric_inputs, text=label, padding=6)
            panel.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
            editor = ScrolledText(panel, height=6, width=34, wrap="word", font=("Consolas", 9))
            editor.insert("1.0", default_value)
            editor.pack(fill="both", expand=True)
            setattr(self, f"metric_{key}", editor)
            metric_inputs.columnconfigure(column, weight=1)
        metric_actions = ttk.Frame(metrics)
        metric_actions.pack(fill="x", pady=8)
        ttk.Button(metric_actions, text="Compare profiles", command=self.compare_profiles).pack(side="left")
        ttk.Label(
            metric_actions,
            text="JSON only · values must be normalized to [0, 1] · higher means better",
            foreground="#526174",
        ).pack(side="left", padx=12)
        self.metric_result = ScrolledText(metrics, wrap="word", font=("Consolas", 10), height=14, state="disabled")
        self.metric_result.pack(fill="both", expand=True)
        bar = ttk.Frame(inventory); bar.pack(fill="x", pady=(0, 10))
        ttk.Button(bar, text="Refresh hardware", command=self.refresh_devices).pack(side="left")
        ttk.Label(bar, text="Read-only Windows Plug and Play inventory", foreground="#526174").pack(side="left", padx=12)
        columns = ("name", "status", "manufacturer", "pnp_id")
        self.devices = ttk.Treeview(inventory, columns=columns, show="headings")
        for col, label, width in (("name","Device",280),("status","Status",90),("manufacturer","Manufacturer",170),("pnp_id","Hardware ID",410)):
            self.devices.heading(col, text=label); self.devices.column(col, width=width, minwidth=90, stretch=True)
        ybar = ttk.Scrollbar(inventory, orient="vertical", command=self.devices.yview)
        self.devices.configure(yscrollcommand=ybar.set); self.devices.pack(fill="both", expand=True); ybar.pack(side="right", fill="y")
        tools = ttk.Frame(packages); tools.pack(fill="x", pady=(0, 10))
        ttk.Button(tools, text="Inspect INF / ZIP…", command=self.choose_package).pack(side="left")
        ttk.Button(tools, text="Batch inspect…", command=self.choose_packages).pack(side="left", padx=(8, 0))
        ttk.Label(tools, text="Metadata and hashes only — no extraction or execution", foreground="#526174").pack(side="left", padx=12)
        self.report = ScrolledText(packages, wrap="word", font=("Consolas", 10), state="disabled")
        self.report.pack(fill="both", expand=True)
        footer = ttk.Frame(self, padding=(14, 4, 14, 10)); footer.pack(fill="x")
        self.status = tk.StringVar(value="Local inspection only — no driver installation or deployment")
        ttk.Label(footer, textvariable=self.status, foreground="#526174").pack(side="left")

    def refresh_devices(self) -> None:
        self.status.set("Querying local Windows device inventory…"); self.update_idletasks()
        self.devices.delete(*self.devices.get_children())
        try:
            devices = list_pnp_devices()
        except Exception as error:
            self.status.set("Device inventory query failed")
            messagebox.showerror("Device inventory", str(error), parent=self); return
        for row in devices:
            self.devices.insert("", "end", values=(row["name"], row["status"], row["manufacturer"], row["pnp_id"]))
        self.status.set(f"Found {len(devices)} Plug and Play devices")

    def compare_profiles(self) -> None:
        try:
            reference = json.loads(self.metric_reference.get("1.0", "end").strip())
            candidate = json.loads(self.metric_candidate.get("1.0", "end").strip())
            raw_weights = self.metric_weights.get("1.0", "end").strip()
            weights = json.loads(raw_weights) if raw_weights else None
            result = analyze_device_profiles(reference, candidate, weights)
        except (ValueError, TypeError, OverflowError, json.JSONDecodeError) as error:
            self.status.set("Metric profile comparison failed")
            messagebox.showerror("Metric analysis", str(error), parent=self)
            return
        self.metric_result.configure(state="normal")
        self.metric_result.delete("1.0", "end")
        self.metric_result.insert("1.0", json.dumps(result, indent=2, ensure_ascii=False))
        self.metric_result.configure(state="disabled")
        self.tabs.select(2)
        self.status.set(
            f"Compared {result['dimension_count']} normalized metrics — "
            f"distance {result['euclidean_distance']:.6f}"
        )

    def choose_package(self) -> None:
        filename = filedialog.askopenfilename(parent=self, title="Select a driver package",
          filetypes=[("Supported packages", "*.inf *.zip"), ("INF files", "*.inf"), ("ZIP files", "*.zip"), ("All files", "*.*")])
        if not filename:
            return
        try:
            data = inspect_package(filename)
        except Exception as error:
            self.status.set("Package inspection failed")
            messagebox.showerror("Package inspection failed", str(error), parent=self); return
        self.report.configure(state="normal"); self.report.delete("1.0", "end")
        self.report.insert("1.0", json.dumps(data, indent=2, ensure_ascii=False))
        self.report.configure(state="disabled"); self.tabs.select(1)
        self.status.set(f"Inspected {data['file_name']} — SHA-256 calculated locally")


    def choose_packages(self) -> None:
        filenames = filedialog.askopenfilenames(
            parent=self, title="Select driver packages",
            filetypes=[("Supported packages", "*.inf *.zip"), ("INF files", "*.inf"),
                       ("ZIP files", "*.zip"), ("All files", "*.*")])
        if not filenames:
            return
        try:
            reports = [inspect_package(filename) for filename in filenames]
            data = compose_inspection_reports(reports)
        except Exception as error:
            self.status.set("Batch package inspection failed")
            messagebox.showerror("Batch package inspection failed", str(error), parent=self)
            return
        self.report.configure(state="normal")
        self.report.delete("1.0", "end")
        self.report.insert("1.0", json.dumps(data, indent=2, ensure_ascii=False))
        self.report.configure(state="disabled")
        self.tabs.select(1)
        totals = data["totals"]
        self.status.set(
            f"Composed {totals['packages']} package reports — bundle SHA-256 {data['bundle_sha256'][:16]}…"
        )

def main() -> int:
    OPlagueApp().mainloop()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
