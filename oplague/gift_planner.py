"""Read-only discrete budget, candy inventory and greeting-plan reports.

No purchase, device write, driver operation or network request is performed.
All monetary values are integer units chosen by the caller (whole UAH or kopiykas).
"""
from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Sequence

MAX_BUDGET = 10_000_000
MAX_ITEMS = 256
MAX_EDGES = 65_536


@dataclass(frozen=True, slots=True)
class Candy:
    name: str
    category: str
    unit_price: int
    stock: int
    preference: int = 1
    weight_grams: int = 0

    def validate(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("candy name must be non-empty text")
        if not isinstance(self.category, str) or not self.category.strip():
            raise ValueError("candy category must be non-empty text")
        for key, value, minimum in (
            ("unit_price", self.unit_price, 1),
            ("stock", self.stock, 0),
            ("preference", self.preference, 1),
            ("weight_grams", self.weight_grams, 0),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                raise ValueError(f"{key} must be an integer >= {minimum}")


@dataclass(frozen=True, slots=True)
class CandyLine:
    catalog_index: int
    name: str
    category: str
    unit_price: int
    quantity: int
    line_total: int
    weight_grams: int


@dataclass(frozen=True, slots=True)
class GreetingEdge:
    sender_index: int
    recipient_index: int
    template_index: int


@dataclass(frozen=True, slots=True)
class GiftPlan:
    budget: int
    allocations: tuple[int, ...]
    baskets: tuple[tuple[CandyLine, ...], ...]
    spent: int
    remaining: int
    greeting_edges: tuple[GreetingEdge, ...]

    def verify(self) -> bool:
        if len(self.allocations) != len(self.baskets):
            return False
        if sum(self.allocations) != self.budget:
            return False
        if self.spent + self.remaining != self.budget:
            return False
        if not 0 <= self.spent <= self.budget:
            return False
        return all(
            sum(line.line_total for line in basket) <= share
            for basket, share in zip(self.baskets, self.allocations)
        )


def _budget(value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_BUDGET:
        raise ValueError(f"budget must be an integer from 0 to {MAX_BUDGET}")


def _count(value: int, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_ITEMS:
        raise ValueError(f"{label} must be an integer from 1 to {MAX_ITEMS}")


def allocate_equal(total: int, count: int) -> tuple[int, ...]:
    """Allocate whole units equally; earlier indexes receive remainder units."""
    _budget(total)
    _count(count, "count")
    quotient, remainder = divmod(total, count)
    return tuple(quotient + (index < remainder) for index in range(count))


def allocate_weighted(total: int, weights: Sequence[int]) -> tuple[int, ...]:
    """Largest-remainder allocation with deterministic input-order tie breaking."""
    _budget(total)
    if not isinstance(weights, (list, tuple)) or not 1 <= len(weights) <= MAX_ITEMS:
        raise ValueError(f"weights must contain 1 to {MAX_ITEMS} entries")
    if any(isinstance(item, bool) or not isinstance(item, int) or item < 0 for item in weights):
        raise ValueError("weights must be non-negative integers")
    weight_sum = sum(weights)
    if weight_sum == 0:
        raise ValueError("at least one weight must be positive")
    bases: list[int] = []
    remainders: list[int] = []
    for weight in weights:
        quotient, remainder = divmod(total * weight, weight_sum)
        bases.append(quotient)
        remainders.append(remainder)
    units_left = total - sum(bases)
    order = sorted(range(len(weights)), key=lambda index: (-remainders[index], index))
    for index in order[:units_left]:
        bases[index] += 1
    return tuple(bases)


def percent_of(total: int, percent: int) -> int:
    _budget(total)
    if isinstance(percent, bool) or not isinstance(percent, int) or not 0 <= percent <= 100:
        raise ValueError("percent must be an integer from 0 to 100")
    return total * percent // 100


def combination_count(n: int, k: int) -> int:
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in (n, k)):
        raise ValueError("n and k must be non-negative integers")
    if n > 1_000_000 or k > n:
        raise ValueError("require 0 <= k <= n <= 1000000")
    return math.comb(n, k)


def build_candy_basket(
    budget: int, catalog: Sequence[Candy]
) -> tuple[tuple[CandyLine, ...], int]:
    """Return a stock-limited, explainable preference/price greedy basket."""
    _budget(budget)
    if not isinstance(catalog, (list, tuple)) or not 1 <= len(catalog) <= MAX_ITEMS:
        raise ValueError(f"catalog must contain 1 to {MAX_ITEMS} candy types")
    for item in catalog:
        if not isinstance(item, Candy):
            raise TypeError("catalog entries must be Candy objects")
        item.validate()
    order = sorted(
        enumerate(catalog),
        key=lambda pair: (-Fraction(pair[1].preference, pair[1].unit_price), pair[0]),
    )
    remaining = budget
    lines: list[CandyLine] = []
    for index, candy in order:
        quantity = min(candy.stock, remaining // candy.unit_price)
        if quantity == 0:
            continue
        line_total = quantity * candy.unit_price
        lines.append(CandyLine(
            index, candy.name, candy.category, candy.unit_price, quantity,
            line_total, quantity * candy.weight_grams,
        ))
        remaining -= line_total
    return tuple(lines), budget - remaining


def build_greeting_graph(
    sender_count: int, recipient_count: int, template_count: int
) -> tuple[GreetingEdge, ...]:
    _count(sender_count, "sender_count")
    _count(recipient_count, "recipient_count")
    _count(template_count, "template_count")
    if sender_count * recipient_count > MAX_EDGES:
        raise ValueError(f"greeting graph exceeds {MAX_EDGES} edges")
    return tuple(
        GreetingEdge(sender, recipient, (sender + recipient) % template_count)
        for sender in range(sender_count)
        for recipient in range(recipient_count)
    )


def plan_gift(
    budget: int,
    recipients: int,
    catalog: Sequence[Candy],
    templates: Sequence[str],
    *,
    weights: Sequence[int] | None = None,
    senders: int = 1,
) -> GiftPlan:
    _budget(budget)
    _count(recipients, "recipients")
    _count(senders, "senders")
    if not isinstance(templates, (list, tuple)) or not 1 <= len(templates) <= MAX_ITEMS:
        raise ValueError(f"templates must contain 1 to {MAX_ITEMS} entries")
    if any(not isinstance(text, str) or not text.strip() for text in templates):
        raise ValueError("greeting templates must be non-empty strings")
    allocations = allocate_equal(budget, recipients) if weights is None else allocate_weighted(budget, weights)
    if len(allocations) != recipients:
        raise ValueError("weights must contain exactly one entry per recipient")

    available = list(catalog)
    baskets: list[tuple[CandyLine, ...]] = []
    spent = 0
    for share in allocations:
        basket, basket_spent = build_candy_basket(share, available)
        baskets.append(basket)
        spent += basket_spent
        for line in basket:
            current = available[line.catalog_index]
            available[line.catalog_index] = Candy(
                current.name, current.category, current.unit_price,
                current.stock - line.quantity, current.preference, current.weight_grams,
            )
    plan = GiftPlan(
        budget=budget,
        allocations=tuple(allocations),
        baskets=tuple(baskets),
        spent=spent,
        remaining=budget - spent,
        greeting_edges=build_greeting_graph(senders, recipients, len(templates)),
    )
    if not plan.verify():
        raise AssertionError("gift plan failed its budget-conservation invariant")
    return plan


def _catalog() -> tuple[Candy, ...]:
    return (
        Candy("Шоколадное пралине", "шоколад", 18, 30, 5, 14),
        Candy("Ореховый трюфель", "трюфель", 24, 20, 5, 16),
        Candy("Вафельный брусок", "вафля", 12, 25, 3, 18),
        Candy("Фруктовая карамель", "карамель", 8, 40, 2, 10),
        Candy("Ягодный мармелад", "желе", 10, 30, 4, 12),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create a read-only integer gift allocation and greeting report."
    )
    parser.add_argument("--budget", type=int, default=500, help="integer currency units")
    parser.add_argument("--recipients", type=int, default=5)
    parser.add_argument("--senders", type=int, default=1)
    args = parser.parse_args(argv)
    report = plan_gift(
        args.budget,
        args.recipients,
        _catalog(),
        ("Счастья и радости!", "Здоровья и сил!", "Пусть сбываются мечты!"),
        senders=args.senders,
    )
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
