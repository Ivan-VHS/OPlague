# Discrete Gift Allocation and Greeting Report

OPlague exposes a self-contained, read-only planner for integer-budget scenarios. It demonstrates resource allocation, stock-aware item selection, combinatorial counts and deterministic sender/recipient routing without performing purchases or modifying the host.

## API

```python
from oplague import Candy, plan_gift

catalog = (
    Candy("Praline", "chocolate", unit_price=18, stock=30, preference=5),
    Candy("Fruit caramel", "caramel", unit_price=8, stock=40, preference=2),
)
report = plan_gift(
    500, 5, catalog,
    ("Happy day!", "Best wishes!", "Congratulations!"),
)
assert report.verify()
```

The API provides:

- Equal allocation with deterministic remainder assignment.
- Largest-remainder weighted allocation with stable tie-breaking.
- Integer percentage calculations and exact bounded combinations.
- Candy selection bounded by item stock and each recipient's budget share.
- A complete directed sender/recipient graph with deterministic greeting-template rotation.
- A composite report whose verification checks the budget conservation invariant.

## Run

```sh
python -m oplague.gift_planner --budget 500 --recipients 5 --senders 1
python -m unittest tests.test_gift_planner -v
```

All monetary values are integer units; use whole UAH or kopiykas consistently. The candy selection order is an explainable preference/price greedy heuristic, not an optimal knapsack guarantee.

## Read-only boundary

This module reads only the catalog passed to it and returns an in-memory report. It makes no network requests, opens no shop account, executes no driver operation and writes no device or operating-system state.
