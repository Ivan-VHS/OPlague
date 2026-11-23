"""OPlague read-only Windows desktop workbench."""
from __future__ import annotations
import hashlib
import json
import os
import platform
import re
import subprocess
import stat
import tkinter as tk
import zipfile
from pathlib import Path, PurePosixPath
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
from tools.authenticode_inspector import inspect_signatures
from ui_theme import apply_ui_theme, load_preferred_theme, set_dpi_awareness
from ui_motion import MotionController, MotionPreferences, fade_in_window
from budget_planner import open_budget_planner
from typing import Any

from tools.report_composer import compose_inspection_reports
from tools.inspection_batch import inspect_batch
from tools.metric_analysis import analyze_device_profiles
from tools.architecture_profiles import current_host_architecture, detect_inf_target_architectures, evaluate_driver_targets
from tools.device_graph import extract_inf_compatibility, build_dry_run_plan
from tools.report_export import render_report
from tools.game_optimizer_ui import open_game_optimizer

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
    trimmed = normalized[:-1] if normalized.endswith("/") else normalized
    parts = trimmed.split("/")
    parsed = PurePosixPath(trimmed)
    if (
        not trimmed
        or any(part in {"", ".", ".."} for part in parts)
        or parsed.is_absolute()
        or "\x00" in normalized
        or re.match(r"^[A-Za-z]:", normalized)
    ):
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
        if size > MAX_INF_BYTES:
            raise ValueError(f"INF file is too large to inspect: {path.name}")
        raw_inf = path.read_bytes()
        report["inf_metadata"] = _inf(raw_inf, path.name)
        report["compatibility"] = extract_inf_compatibility(_decode_inf(raw_inf))
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
            seen_paths: set[str] = set()
            for entry in entries:
                _safe_archive_name(entry.filename)
                canonical_name = entry.filename.replace("\\", "/").rstrip("/")
                folded_name = canonical_name.casefold()
                if folded_name in seen_paths:
                    raise ValueError(f"Duplicate archive path detected: {entry.filename}")
                seen_paths.add(folded_name)

                mode = (entry.external_attr >> 16) & 0xFFFF
                file_type = stat.S_IFMT(mode)
                if file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise ValueError(f"Non-regular archive entry is not allowed: {entry.filename}")
                if entry.is_dir():
                    if file_type not in (0, stat.S_IFDIR):
                        raise ValueError(f"Archive directory has an invalid file type: {entry.filename}")
                    continue
                if entry.flag_bits & 0x1:
                    raise ValueError(f"Encrypted archive entry is not supported: {entry.filename}")

                expanded += entry.file_size
                if expanded > MAX_EXPANDED_BYTES:
                    raise ValueError("Archive exceeds the expanded-size inspection limit")
                if entry.file_size and not entry.compress_size:
                    raise ValueError(f"Suspicious compressed entry: {entry.filename}")
                if entry.compress_size and entry.file_size / entry.compress_size > MAX_COMPRESSION_RATIO:
                    raise ValueError(f"Suspicious compression ratio: {entry.filename}")
                if entry.filename.casefold().endswith(".inf"):
                    if entry.file_size > MAX_INF_BYTES:
                        raise ValueError(f"INF file is too large to inspect: {entry.filename}")
                    # Bound decompression as well as the declared ZIP size. A
                    # malformed central directory must not trigger an unbounded
                    # archive.read() allocation for an INF inspection.
                    with archive.open(entry, "r") as source:
                        raw_inf = source.read(MAX_INF_BYTES + 1)
                    if len(raw_inf) > MAX_INF_BYTES or len(raw_inf) != entry.file_size:
                        raise ValueError(f"INF entry size does not match its declared bound: {entry.filename}")
                    inf_files.append({
                        "file": entry.filename,
                        "metadata": _inf(raw_inf, entry.filename),
                        "compatibility": extract_inf_compatibility(_decode_inf(raw_inf)),
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

def _driver_records_from_report(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Turn inspected INF model declarations into candidate-only driver records."""
    items = []
    if report.get("format") == "INF":
        items.append((report.get("file_name", "driver.inf"), report.get("compatibility", {})))
    else:
        for inf in report.get("inf_files", []):
            if isinstance(inf, dict):
                items.append((inf.get("file", "driver.inf"), inf.get("compatibility", {})))
    records = []
    for filename, compatibility in items:
        if not isinstance(compatibility, dict):
            continue
        ids = compatibility.get("hardware_ids", [])
        if not ids:
            continue
        digest = str(report.get("sha256", "unknown"))
        records.append({
            "driver_id": f"{digest[:16]}:{filename}",
            "package_name": str(report.get("file_name", filename)),
            "package_sha256": digest,
            "hardware_ids": ids,
            "architectures": compatibility.get("architectures", ["unspecified"]),
        })
    return records

class OPlagueApp(tk.Tk):
    def __init__(self) -> None:
        set_dpi_awareness()
        super().__init__()
        self.title("OPlague — мастерская оборудования и драйверов · Ivan-VHS")
        self.geometry("1120x720")
        self.minsize(820, 540)
        self._theme_mode = load_preferred_theme()
        self._theme_cycle = ("system", "light", "dark")
        header = ttk.Frame(self, padding=(16, 12)); header.pack(fill="x")
        ttk.Label(header, text="OPLAGUE", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="Инвентаризация оборудования  /  Проверка пакетов драйверов", style="Muted.TLabel").pack(side="left", padx=16)
        self.theme_button = ttk.Button(header, text="Тема: системная", command=self.cycle_theme)
        self.theme_button.pack(side="right")
        self.motion_button = ttk.Button(header, text="Движение", command=self.show_motion_settings)
        self.motion_button.pack(side="right", padx=(0, 8))
        self.budget_button = ttk.Button(header, text="Бюджет 500 грн", command=lambda: open_budget_planner(self))        self.budget_button.pack(side="right", padx=(0, 8))
        self.game_button = ttk.Button(header, text="Игровая лаборатория", command=lambda: open_game_optimizer(self))
        self.game_button.pack(side="right", padx=(0, 8))
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        inventory = ttk.Frame(self.tabs, padding=12); packages = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(inventory, text="Устройства"); self.tabs.add(packages, text="Проверка пакетов")
        self.device_rows: list[dict[str, str]] = []
        self.current_report: dict[str, Any] | None = None
        self.inspected_drivers: list[dict[str, Any]] = []
        metrics = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(metrics, text="Лаборатория метрик")
        compatibility = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(compatibility, text="Проверка совместимости")
        ttk.Label(
            compatibility,
            text="Сопоставление выполняется только по точным аппаратным идентификаторам INF. Кандидат не является заключением о совместимости или безопасности; операции с драйверами не выполняются.",
            style="Muted.TLabel", wraplength=1000,
        ).pack(anchor="w", pady=(0, 8))
        ttk.Button(
            compatibility, text="Сформировать пробный план по текущему списку устройств",
            command=self.build_compatibility_plan, style="Primary.TButton",
        ).pack(anchor="w", pady=(0, 8))
        self.compatibility_result = ScrolledText(
            compatibility, wrap="word", font=("Consolas", 10), height=20, state="disabled"
        )
        self.compatibility_result.pack(fill="both", expand=True)
        ttk.Label(
            metrics,
            text="Сравнение нормализованных аппаратных и тестовых профилей по многомерным метрикам и взвешенному квадратичному расстоянию.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(0, 8))
        metric_inputs = ttk.Frame(metrics)
        metric_inputs.pack(fill="x", expand=False)
        profile_defaults = (
            ("reference", "Эталонный профиль", '{"cpu_score": 0.82, "memory_score": 0.71, "thermal_headroom": 0.68}'),
            ("candidate", "Проверяемый профиль", '{"cpu_score": 0.88, "memory_score": 0.66, "thermal_headroom": 0.74}'),
            ("weights", "Веса метрик (необязательно)", '{"cpu_score": 1.0, "memory_score": 1.5, "thermal_headroom": 1.0}'),
        )
        self.metric_input_panels: list[ttk.LabelFrame] = []
        for column, (key, label, default_value) in enumerate(profile_defaults):
            panel = ttk.LabelFrame(metric_inputs, text=label, padding=6)
            panel.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 6, 0))
            self.metric_input_panels.append(panel)
            editor = ScrolledText(panel, height=6, width=34, wrap="word", font=("Consolas", 9))
            editor.insert("1.0", default_value)
            editor.pack(fill="both", expand=True)
            setattr(self, f"metric_{key}", editor)
            metric_inputs.columnconfigure(column, weight=1)
        metric_inputs.bind("<Configure>", self._layout_metric_inputs, add="+")
        metric_actions = ttk.Frame(metrics)
        metric_actions.pack(fill="x", pady=8)
        ttk.Button(metric_actions, text="Сравнить профили", command=self.compare_profiles, style="Primary.TButton").pack(side="left")
        ttk.Label(
            metric_actions,
            text="Только JSON · значения должны быть нормированы к диапазону [0, 1] · большее значение означает лучший результат",
            style="Muted.TLabel",
        ).pack(side="left", padx=12)
        self.metric_result = ScrolledText(metrics, wrap="word", font=("Consolas", 10), height=14, state="disabled")
        self.metric_result.pack(fill="both", expand=True)
        bar = ttk.Frame(inventory); bar.pack(fill="x", pady=(0, 10))
        ttk.Button(bar, text="Обновить список устройств", command=self.refresh_devices, style="Primary.TButton").pack(side="left")
        ttk.Label(bar, text="Список устройств Windows Plug and Play — только чтение", style="Muted.TLabel").pack(side="left", padx=12)
        columns = ("name", "status", "manufacturer", "pnp_id")
        self.devices = ttk.Treeview(inventory, columns=columns, show="headings")
        for col, label, width in (("name","Устройство",280),("status","Состояние",90),("manufacturer","Производитель",170),("pnp_id","Аппаратный ID",410)):
            self.devices.heading(col, text=label); self.devices.column(col, width=width, minwidth=90, stretch=True)
        ybar = ttk.Scrollbar(inventory, orient="vertical", command=self.devices.yview)
        self.devices.configure(yscrollcommand=ybar.set); self.devices.pack(fill="both", expand=True); ybar.pack(side="right", fill="y")
        tools = ttk.Frame(packages); tools.pack(fill="x", pady=(0, 10))
        ttk.Button(tools, text="Проверить INF / ZIP…", command=self.choose_package, style="Primary.TButton").pack(side="left")
        ttk.Button(tools, text="Пакетная проверка…", command=self.choose_packages).pack(side="left", padx=(8, 0))
        ttk.Button(tools, text="Экспорт отчёта…", command=self.export_report).pack(side="left", padx=(8, 0))
        ttk.Button(tools, text="Проверить подписи…", command=self.choose_signatures).pack(side="left", padx=(8, 0))
        ttk.Label(tools, text="Только метаданные и хеши — без распаковки и запуска содержимого", style="Muted.TLabel").pack(side="left", padx=12)
        self.report = ScrolledText(packages, wrap="word", font=("Consolas", 10), state="disabled")
        self.report.pack(fill="both", expand=True)
        footer = ttk.Frame(self, padding=(14, 4, 14, 10)); footer.pack(fill="x")
        self.status = tk.StringVar(value="Только локальная проверка — установка и развёртывание драйверов не выполняются")
        ttk.Label(footer, textvariable=self.status, style="Muted.TLabel").pack(side="left")
        ttk.Label(footer, text="Разработчик: Ivan-VHS", style="Muted.TLabel").pack(side="right")
        self.apply_visual_theme()
        self._motion = MotionController(self, app_key="oplague")
        self._motion.fade_in()

    def show_motion_settings(self) -> None:
        """Configure persisted motion and visual-performance preferences."""
        window = tk.Toplevel(self)
        window.title("Настройки движения интерфейса")
        window.resizable(False, False)
        window.transient(self)
        current = self._motion.preferences
        fade_in_window(window, current, app_key="oplague")
        reduce_var = tk.BooleanVar(value=current.reduce_motion)
        eco_var = tk.BooleanVar(value=current.eco_visuals)
        expressive_var = tk.BooleanVar(value=current.expressive_motion)
        frame = ttk.Frame(window, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Кинетика интерфейса", style="Title.TLabel").pack(anchor="w", pady=(0, 8))
        ttk.Checkbutton(frame, text="Reduce Motion — убрать пространственное движение", variable=reduce_var).pack(anchor="w", pady=4)
        ttk.Checkbutton(frame, text="Eco / Low-CPU Visuals — отключить необязательные эффекты", variable=eco_var).pack(anchor="w", pady=4)
        ttk.Checkbutton(frame, text="Expressive Motion — усиленная пружинная кинетика", variable=expressive_var).pack(anchor="w", pady=4)
        buttons = ttk.Frame(frame)
        buttons.pack(fill="x")
        def apply() -> None:
            self._motion.update_preferences(MotionPreferences(
                reduce_motion=reduce_var.get(),
                eco_visuals=eco_var.get(),
                expressive_motion=expressive_var.get(),
            ))
            window.destroy()
        ttk.Button(buttons, text="Сохранить", style="Primary.TButton", command=apply).pack(side="right")
        ttk.Button(buttons, text="Отмена", command=window.destroy).pack(side="right", padx=(0, 8))
        window.grab_set()
        window.update_idletasks()
        window.geometry(f"+{self.winfo_rootx() + 120}+{self.winfo_rooty() + 100}")

    def apply_visual_theme(self) -> None:
        """Apply the selected appearance to tabs, tables and report editors."""
        apply_ui_theme(self, self._theme_mode)
        theme_title = {"system": "системная", "light": "светлая", "dark": "тёмная"}.get(self._theme_mode, "системная")
        self.theme_button.configure(text=f"Тема: {theme_title}")

    def cycle_theme(self) -> None:
        index = self._theme_cycle.index(self._theme_mode)
        self._theme_mode = self._theme_cycle[(index + 1) % len(self._theme_cycle)]
        self.apply_visual_theme()

    def _layout_metric_inputs(self, event: tk.Event | None = None) -> None:
        """Reflow Metric Lab editors without shrinking their text or hit areas."""
        width = int(getattr(event, "width", 0) or self.winfo_width())
        columns = 3 if width >= 1000 else 2 if width >= 640 else 1
        for index, panel in enumerate(self.metric_input_panels):
            panel.grid_configure(
                row=index // columns, column=index % columns,
                padx=(0 if index % columns == 0 else 6, 0), pady=4, sticky="nsew",
            )
        container = self.metric_input_panels[0].master if self.metric_input_panels else None
        if container is not None:
            for column in range(3):
                container.columnconfigure(column, weight=1 if column < columns else 0)

    def refresh_devices(self) -> None:        self.status.set("Получение локального списка устройств Windows…"); self.update_idletasks()
        self.devices.delete(*self.devices.get_children())
        try:
            devices = list_pnp_devices()
        except Exception as error:
            self.status.set("Не удалось получить список устройств")
            messagebox.showerror("Список устройств", str(error), parent=self); return
        self.device_rows = devices
        for row in devices:
            self.devices.insert("", "end", values=(row["name"], row["status"], row["manufacturer"], row["pnp_id"]))
        self.status.set(f"Найдено устройств Plug and Play: {len(devices)}")

    def compare_profiles(self) -> None:
        try:
            reference = json.loads(self.metric_reference.get("1.0", "end").strip())
            candidate = json.loads(self.metric_candidate.get("1.0", "end").strip())
            raw_weights = self.metric_weights.get("1.0", "end").strip()
            weights = json.loads(raw_weights) if raw_weights else None
            result = analyze_device_profiles(reference, candidate, weights)
        except (ValueError, TypeError, OverflowError, json.JSONDecodeError) as error:
            self.status.set("Не удалось сравнить профили метрик")
            messagebox.showerror("Анализ метрик", str(error), parent=self)
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

    def choose_signatures(self) -> None:
        """Inspect Windows Authenticode metadata without loading or installing files."""
        filenames = filedialog.askopenfilenames(
            parent=self,
            title="Проверить цифровые подписи",
            filetypes=[
                ("Файлы для проверки подписи", "*.cat *.sys *.dll *.exe"),
                ("Каталоги безопасности", "*.cat"),
                ("Драйверы", "*.sys"),
                ("Библиотеки", "*.dll"),
                ("Приложения", "*.exe"),
            ],
        )
        if not filenames:
            return
        try:
            report = inspect_signatures(filenames)
        except (OSError, ValueError, NotImplementedError, RuntimeError) as error:
            self.status.set("Не удалось проверить цифровые подписи")
            messagebox.showerror("Проверка Authenticode", str(error), parent=self)
            return
        self.report.configure(state="normal")
        self.report.delete("1.0", "end")
        self.report.insert("1.0", json.dumps(report, indent=2, ensure_ascii=False))
        self.report.configure(state="disabled")
        self.tabs.select(1)
        valid = sum(1 for item in report["results"] if item["status"] == "Valid")
        self.status.set(
            f"Authenticode: Valid — {valid} из {report['files_inspected']}; "
            "вердикт безопасности драйвера не выносится"
        )

    def choose_package(self) -> None:
        filename = filedialog.askopenfilename(parent=self, title="Выберите пакет драйвера",
          filetypes=[("Поддерживаемые пакеты", "*.inf *.zip"), ("Файлы INF", "*.inf"), ("Архивы ZIP", "*.zip"), ("Все файлы", "*.*")])
        if not filename:
            return
        try:
            data = inspect_package(filename)
        except Exception as error:
            self.status.set("Не удалось проверить пакет")
            messagebox.showerror("Не удалось проверить пакет", str(error), parent=self); return
        self.current_report = data
        self._remember_driver_records(data)
        self.report.configure(state="normal"); self.report.delete("1.0", "end")
        self.report.insert("1.0", json.dumps(data, indent=2, ensure_ascii=False))
        self.report.configure(state="disabled"); self.tabs.select(1)
        self.status.set(f"Проверен файл {data['file_name']} — SHA-256 рассчитан локально")



    def _remember_driver_records(self, report: dict[str, Any]) -> None:
        existing = {item["driver_id"] for item in self.inspected_drivers}
        for item in _driver_records_from_report(report):
            if item["driver_id"] not in existing:
                self.inspected_drivers.append(item)
                existing.add(item["driver_id"])

    def build_compatibility_plan(self) -> None:
        if not self.device_rows:
            messagebox.showinfo("План совместимости", "Сначала обновите список устройств в режиме чтения.", parent=self)
            return
        if not self.inspected_drivers:
            messagebox.showinfo("План совместимости", "Сначала проверьте хотя бы один пакет INF или ZIP с разделом Models.", parent=self)
            return
        try:
            plan = build_dry_run_plan(
                self.device_rows, self.inspected_drivers,
                host_architecture=platform.machine(),
            )
        except (TypeError, ValueError, OverflowError) as error:
            self.status.set("Не удалось сформировать план совместимости")
            messagebox.showerror("План совместимости", str(error), parent=self)
            return
        self.compatibility_result.configure(state="normal")
        self.compatibility_result.delete("1.0", "end")
        self.compatibility_result.insert("1.0", json.dumps(plan, indent=2, ensure_ascii=False))
        self.compatibility_result.configure(state="disabled")
        summary = plan["summary"]
        self.tabs.select(3)
        self.status.set(
            f"Пробный расчёт: кандидатов с точным ID — {summary['candidate_edges']}; система не изменена"
        )

    def export_report(self) -> None:
        if self.current_report is None:
            messagebox.showinfo("Экспорт отчёта", "Сначала проверьте INF или ZIP-пакет.", parent=self)
            return
        destination = filedialog.asksaveasfilename(
            parent=self,
            title="Экспортировать отчёт OPlague",
            defaultextension=".json",
            filetypes=[
                ("JSON report", "*.json"),
                ("CSV table", "*.csv"),
                ("Markdown report", "*.md"),
            ],
        )
        if not destination:
            return
        suffix = Path(destination).suffix.casefold()
        format_name = {".json": "json", ".csv": "csv", ".md": "markdown"}.get(suffix)
        if format_name is None:
            messagebox.showerror(
                "Экспорт отчёта",
                "Используйте расширение .json, .csv или .md.",
                parent=self,            )
            return
        anonymize = messagebox.askyesno(
            "Конфиденциальность отчёта",
            "Обезличить PnP и аппаратные идентификаторы перед экспортом?",
            parent=self,
        )
        try:
            content = render_report(self.current_report, format_name, anonymize=anonymize)
            Path(destination).write_text(content, encoding="utf-8")
        except (OSError, TypeError, ValueError) as error:
            self.status.set("Не удалось экспортировать отчёт")
            messagebox.showerror("Экспорт отчёта", str(error), parent=self)
            return
        self.status.set(f"Отчёт OPlague экспортирован: {Path(destination).name}")

    def choose_packages(self) -> None:
        filenames = filedialog.askopenfilenames(
            parent=self, title="Выберите пакеты драйверов",
            filetypes=[("Supported packages", "*.inf *.zip"), ("INF files", "*.inf"),
                       ("ZIP files", "*.zip"), ("All files", "*.*")])
        if not filenames:
            return
        try:
            reports = inspect_batch(filenames, inspect_package)
            data = compose_inspection_reports(reports)
        except Exception as error:
            self.status.set("Не удалось выполнить пакетную проверку")
            messagebox.showerror("Не удалось выполнить пакетную проверку", str(error), parent=self)
            return
        self.current_report = data
        for report in reports:
            self._remember_driver_records(report)
        self.report.configure(state="normal")
        self.report.delete("1.0", "end")
        self.report.insert("1.0", json.dumps(data, indent=2, ensure_ascii=False))
        self.report.configure(state="disabled")
        self.tabs.select(1)
        totals = data["totals"]
        self.status.set(
            f"Сформировано отчётов о пакетах: {totals['packages']} — SHA-256 набора {data['bundle_sha256'][:16]}…"
        )

def main() -> int:
    OPlagueApp().mainloop()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())