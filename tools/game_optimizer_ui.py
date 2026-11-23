"""Tk interface for OPlague's reversible game-session workbench."""
from __future__ import annotations

import csv
import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

from tools.game_optimizer import (
    collect_windows_devices,
    compare_benchmarks,
    create_snapshot,
    restore_game_session,
    start_game_session,
    summarize_frametime_csv,
)


def open_game_optimizer(parent: tk.Misc) -> None:
    """Open the gaming lab without blocking the existing device workbench."""
    window = tk.Toplevel(parent)
    window.title("OPlague — игровая лаборатория")
    window.geometry("900x680")
    window.minsize(680, 480)
    window.transient(parent)

    header = ttk.Frame(window, padding=(16, 12))
    header.pack(fill="x")
    ttk.Label(header, text="Игровая лаборатория", style="Title.TLabel").pack(anchor="w")
    ttk.Label(
        header,
        text=(
            "Снимки системы · точный отпечаток железа и драйверов · временный план питания · "
            "frametime / 1% low / 0.1% low"
        ),
        style="Muted.TLabel", wraplength=820,
    ).pack(anchor="w", pady=(6, 0))

    actions = ttk.Frame(window, padding=(16, 0, 16, 10))
    actions.pack(fill="x")
    output = ScrolledText(window, wrap="word", font=("Consolas", 10), height=24, state="disabled")
    output.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def show(value: object) -> None:
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.insert("1.0", json.dumps(value, indent=2, ensure_ascii=False, default=str))
        output.configure(state="disabled")

    def snapshot() -> None:
        try:
            devices = collect_windows_devices() if os.name == "nt" else []
            result = create_snapshot(devices=devices)
        except Exception as error:
            messagebox.showerror("Снимок системы", str(error), parent=window)
            return
        show(result)
        messagebox.showinfo(
            "Снимок сохранён",
            f"Снимок записан локально.\nОтпечаток: {result['hardware_fingerprint'][:16]}…",
            parent=window,
        )

    def start() -> None:
        game_name = simpledialog.askstring(
            "Игровая сессия", "Название игры или тестового сценария:",
            parent=window,
        )
        if not game_name:
            return
        try:
            result = start_game_session(game_name, power_mode="performance")
        except Exception as error:
            messagebox.showerror("Не удалось включить игровой режим", str(error), parent=window)
            return
        show(result)
        messagebox.showinfo(
            "Игровой режим включён",
            "Снимок создан до переключения. Используйте «Завершить и восстановить» после игры.",
            parent=window,
        )

    def restore() -> None:
        try:
            result = restore_game_session()
        except Exception as error:
            messagebox.showerror("Восстановление", str(error), parent=window)
            return
        show(result)
        if result["restored"]:
            messagebox.showinfo("Восстановление", "Исходный план электропитания восстановлен.", parent=window)
        else:
            messagebox.showwarning(
                "Внешнее изменение обнаружено",
                "План питания был изменён вне OPlague. Текущий выбор оставлен без изменений.",
                parent=window,
            )

    def benchmark() -> None:
        baseline_file = filedialog.askopenfilename(
            parent=window, title="Выберите исходный CSV",
            filetypes=[("Benchmark CSV", "*.csv"), ("All files", "*.*")],
        )
        if not baseline_file:
            return
        candidate_file = filedialog.askopenfilename(
            parent=window, title="Выберите CSV после изменения",
            filetypes=[("Benchmark CSV", "*.csv"), ("All files", "*.*")],
        )
        if not candidate_file:
            return
        try:
            baseline = summarize_frametime_csv(baseline_file)
            candidate = summarize_frametime_csv(candidate_file)
            comparison = compare_benchmarks(baseline, candidate)
        except (OSError, ValueError, csv.Error) as error:
            messagebox.showerror("Анализ frametime", str(error), parent=window)
            return
        rollback = None
        if comparison["regression_detected"]:
            try:
                rollback = restore_game_session()
            except FileNotFoundError:
                rollback = {"restored": False, "reason": "no_active_session"}
            except (OSError, RuntimeError, ValueError) as error:
                rollback = {"restored": False, "reason": str(error)}
        show({"baseline": baseline, "candidate": candidate, "comparison": comparison, "rollback": rollback})
        if comparison["regression_detected"]:
            if rollback and rollback.get("restored"):
                notice = "Обнаружено ухудшение. OPlague восстановил прежний план питания игрового сеанса."
            else:
                notice = "Обнаружено ухудшение. Автооткат не выполнен: нет активной сессии или план менялся извне."
            messagebox.showwarning("Обнаружено ухудшение", notice, parent=window)

    ttk.Button(actions, text="Снять состояние", command=snapshot, style="Primary.TButton").pack(side="left", padx=(0, 8))
    ttk.Button(actions, text="Игровой режим", command=start, style="Primary.TButton").pack(side="left", padx=(0, 8))
    ttk.Button(actions, text="Завершить и восстановить", command=restore).pack(side="left", padx=(0, 8))
    ttk.Button(actions, text="Сравнить frametime CSV…", command=benchmark).pack(side="left")
    ttk.Label(
        window,
        text=(
            "Безопасность: драйверы не устанавливаются и не патчатся; разгон, IRQ/MSI, реестр, службы и сеть "
            "не меняются. Температуры и GPU-счётчики не выдумываются: используйте реальные логи мониторинга."
        ),
        style="Muted.TLabel", wraplength=850,
    ).pack(fill="x", padx=16, pady=(0, 12))
