"""Offline 500 UAH budget planner for the OPlague desktop workbench.

The monetary figures are editable estimates supplied in the accompanying article.
No external prices, accounts or network services are queried.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

DEFAULT_AMOUNT = 500
MAX_AMOUNT = 1_000_000
CATEGORIES = ("food", "transport", "household", "digital", "leisure", "reserve")
LABELS = {
    "food": "Продукты и питание",
    "transport": "Транспорт",
    "household": "Быт и здоровье",
    "digital": "Связь и обучение",
    "leisure": "Досуг и кофе",
    "reserve": "Резерв",
}
SCENARIOS: dict[str, dict[str, int]] = {
    "weekly": {"food": 280, "transport": 120, "household": 0, "digital": 0, "leisure": 50, "reserve": 50},
    "groceries": {"food": 500, "transport": 0, "household": 0, "digital": 0, "leisure": 0, "reserve": 0},
    "transport": {"food": 0, "transport": 500, "household": 0, "digital": 0, "leisure": 0, "reserve": 0},
    "coffee": {"food": 0, "transport": 0, "household": 0, "digital": 0, "leisure": 460, "reserve": 40},
    "household": {"food": 0, "transport": 0, "household": 500, "digital": 0, "leisure": 0, "reserve": 0},
    "learning": {"food": 0, "transport": 0, "household": 0, "digital": 500, "leisure": 0, "reserve": 0},
    "reserve": {"food": 0, "transport": 0, "household": 0, "digital": 0, "leisure": 0, "reserve": 500},
}
SCENARIO_LABELS = {
    "weekly": "Недельный баланс",
    "groceries": "Продуктовый минимум",
    "transport": "Транспортный запас",
    "coffee": "Кофе и перезагрузка",
    "household": "Бытовой рефилл",
    "learning": "Инвестиция в себя",
    "reserve": "Неприкосновенный резерв",
}
PRICE_REFERENCE = (
    ("Эспрессо", "за чашку", 46, 46),
    ("Гречка", "за кг", 75, 88),
    ("Рис", "за кг", 52, 61),
    ("Макароны", "за кг", 40, 43),
    ("Мука", "за кг", 23, 24),
    ("Хлеб", "за кг", 50, 68),
    ("Капучино или латте", "за чашку, расчётный ориентир", 64, 74),
    ("Батон", "за 500 г", 33, 35),
    ("Молоко", "за литр", 50, 54),
    ("Яйца", "за 10 шт.", 40, 61),
    ("Картофель", "за кг", 16, 24),
    ("Яблоки", "за кг", 35, 57),
    ("Курица", "за кг", 110, 116),
    ("Куриное филе", "за кг", 208, 220),
)
TRANSPORT_ESTIMATES = {
    "Киев": {"метро/коммунальный транспорт": 30},
    "Днепр": {"автобус": 23, "трамвай/троллейбус": 25, "метро": 10},
    "Львов": {"электронный билет": "23–30"},
}
PRICE_BASIS = "Все цены — ориентиры из предоставленного материала; они не являются проверенными текущими тарифами или предложениями."


class BudgetError(ValueError):
    """Invalid budget amount, scenario or category allocation."""


def calculate_budget(
    amount: int = DEFAULT_AMOUNT,
    scenario: str = "weekly",
    overrides: Mapping[str, int] | None = None,
) -> dict[str, Any]:
    if isinstance(amount, bool) or not isinstance(amount, int) or not 0 <= amount <= MAX_AMOUNT:
        raise BudgetError(f"Лимит должен быть целым числом от 0 до {MAX_AMOUNT} грн")
    if scenario not in SCENARIOS:
        raise BudgetError(f"Неизвестный сценарий: {scenario}")
    allocations = dict(SCENARIOS[scenario])
    if overrides:
        for category, value in overrides.items():
            if category not in CATEGORIES:
                raise BudgetError(f"Неизвестная категория: {category}")
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_AMOUNT:
                raise BudgetError(f"Некорректная сумма для категории {category}")
            allocations[category] = value
    planned = sum(allocations.values())
    remaining = amount - planned
    return {
        "schema": "oplague.microbudget.v1",
        "currency": "UAH",
        "budget_uah": amount,
        "scenario": scenario,
        "scenario_label": SCENARIO_LABELS[scenario],
        "allocations": [
            {"id": key, "label": LABELS[key], "amount_uah": allocations[key]}
            for key in CATEGORIES
        ],
        "planned_uah": planned,
        "remaining_uah": remaining,
        "over_budget_uah": max(0, -remaining),
        "within_budget": remaining >= 0,
        "reference_prices": [
            {"item": name, "unit": unit, "min_uah": low, "max_uah": high}
            for name, unit, low, high in PRICE_REFERENCE
        ],
        "transport_estimates": TRANSPORT_ESTIMATES,
        "price_basis": PRICE_BASIS,
    }


def open_budget_planner(parent: Any) -> None:
    """Open an editable Tk planner; imports Tk only when the desktop action is used."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    window = tk.Toplevel(parent)
    window.title("OPlague — планировщик бюджета 500 грн")
    window.geometry("760x690")
    window.minsize(620, 560)
    window.transient(parent)

    root = ttk.Frame(window, padding=18)
    root.pack(fill="both", expand=True)
    ttk.Label(root, text="МИКРОБЮДЖЕТ · 500 UAH", font=("Segoe UI", 16, "bold")).pack(anchor="w")
    ttk.Label(
        root,
        text="Выберите сценарий или измените суммы вручную. Все расчёты локальные; справочные цены редактируемы и не являются live-котировками.",
        wraplength=700,
    ).pack(anchor="w", pady=(6, 14))

    controls = ttk.Frame(root)
    controls.pack(fill="x")
    amount_var = tk.StringVar(value=str(DEFAULT_AMOUNT))
    scenario_var = tk.StringVar(value="weekly")
    ttk.Label(controls, text="Лимит, грн").grid(row=0, column=0, sticky="w", padx=(0, 8))
    amount_box = ttk.Spinbox(controls, from_=0, to=MAX_AMOUNT, increment=50, textvariable=amount_var, width=12)
    amount_box.grid(row=0, column=1, sticky="w", padx=(0, 20))
    ttk.Label(controls, text="Сценарий").grid(row=0, column=2, sticky="w", padx=(0, 8))
    scenario_box = ttk.Combobox(
        controls, state="readonly", textvariable=scenario_var, width=28,
        values=tuple(SCENARIO_LABELS.values()),
    )
    scenario_box.grid(row=0, column=3, sticky="ew")
    controls.columnconfigure(3, weight=1)
    key_by_label = {label: key for key, label in SCENARIO_LABELS.items()}
    allocations = {key: tk.StringVar(value=str(value)) for key, value in SCENARIOS["weekly"].items()}

    rows = ttk.LabelFrame(root, text="Распределение по категориям", padding=12)
    rows.pack(fill="x", pady=14)
    for row_index, key in enumerate(CATEGORIES):
        ttk.Label(rows, text=LABELS[key]).grid(row=row_index, column=0, sticky="w", pady=4)
        spin = ttk.Spinbox(rows, from_=0, to=MAX_AMOUNT, increment=10, textvariable=allocations[key], width=14)
        spin.grid(row=row_index, column=1, sticky="e", padx=(12, 0), pady=4)
        ttk.Label(rows, text="грн").grid(row=row_index, column=2, sticky="w", padx=(6, 0))
    rows.columnconfigure(0, weight=1)

    summary = ttk.LabelFrame(root, text="Расчёт", padding=12)
    summary.pack(fill="x")
    total_var = tk.StringVar()
    status_var = tk.StringVar()
    ttk.Label(summary, textvariable=total_var, font=("Segoe UI", 11, "bold")).pack(anchor="w")
    ttk.Label(summary, textvariable=status_var, wraplength=690).pack(anchor="w", pady=(5, 0))

    reference = ttk.LabelFrame(root, text="Справочные ориентиры из статьи", padding=10)
    reference.pack(fill="both", expand=True, pady=14)
    reference_text = tk.Text(reference, height=8, wrap="word", relief="flat")
    reference_text.pack(fill="both", expand=True)
    price_lines = [f"{name}: {low}–{high} грн {unit}" for name, unit, low, high in PRICE_REFERENCE]
    price_lines.extend([
        "",
        "Транспорт (из статьи): Киев — 30 грн; Днепр — автобус 23, трамвай/троллейбус 25, метро 10; Львов — 23–30 грн.",
        PRICE_BASIS,
    ])
    reference_text.insert("1.0", "\n".join(price_lines))
    reference_text.configure(state="disabled")

    def refresh(*_args: Any) -> None:
        try:
            amount = int(amount_var.get())
            values = {key: int(allocations[key].get()) for key in CATEGORIES}
            result = calculate_budget(amount, key_by_label.get(scenario_var.get(), "weekly"), values)
        except (ValueError, BudgetError):
            total_var.set("Введите целые неотрицательные суммы в допустимом диапазоне.")
            status_var.set("Расчёт ожидает корректных значений.")
            return
        total_var.set(f"Запланировано: {result['planned_uah']} грн из {result['budget_uah']} грн")
        if result["within_budget"]:
            status_var.set(f"Остаток: {result['remaining_uah']} грн · использовано {round(result['planned_uah'] / amount * 100, 1) if amount else 0}%")
        else:
            status_var.set(f"Превышение лимита: {result['over_budget_uah']} грн")

    def apply_scenario(_event: Any = None) -> None:
        key = key_by_label.get(scenario_var.get(), "weekly")
        for category, value in SCENARIOS[key].items():
            allocations[category].set(str(value))
        refresh()

    scenario_box.current(0)
    scenario_box.bind("<<ComboboxSelected>>", apply_scenario)
    amount_var.trace_add("write", refresh)
    for value in allocations.values():
        value.trace_add("write", refresh)

    actions = ttk.Frame(root)
    actions.pack(fill="x")
    ttk.Button(actions, text="Недельный баланс", command=lambda: (scenario_var.set(SCENARIO_LABELS["weekly"]), apply_scenario())).pack(side="left")
    def export_plan() -> None:
        try:
            amount = int(amount_var.get())
            values = {key: int(allocations[key].get()) for key in CATEGORIES}
            result = calculate_budget(amount, "weekly", values)
        except (ValueError, BudgetError) as error:
            messagebox.showerror("Некорректный бюджет", str(error), parent=window)
            return
        path = filedialog.asksaveasfilename(
            parent=window, title="Сохранить план бюджета",
            defaultextension=".json", filetypes=[("JSON", "*.json")],
        )
        if path:
            Path(path).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            messagebox.showinfo("План сохранён", f"Файл записан:\n{path}", parent=window)
    ttk.Button(actions, text="Экспорт JSON…", command=export_plan).pack(side="right")
    ttk.Button(actions, text="Закрыть", command=window.destroy).pack(side="right", padx=8)
    refresh()
    window.grab_set()
