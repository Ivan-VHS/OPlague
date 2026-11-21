from __future__ import annotations

import unittest

from oplague.gift_planner import (
    Candy, allocate_equal, allocate_weighted, build_candy_basket,
    build_greeting_graph, combination_count, percent_of, plan_gift,
)


class DiscreteGiftPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = (
            Candy("Praline", "chocolate", 18, 30, 5, 14),
            Candy("Truffle", "truffle", 24, 20, 5, 16),
            Candy("Wafer", "wafer", 12, 25, 3, 18),
        )

    def test_equal_and_weighted_allocation_conserve_budget(self):
        self.assertEqual(allocate_equal(500, 5), (100, 100, 100, 100, 100))
        self.assertEqual(allocate_equal(10, 3), (4, 3, 3))
        self.assertEqual(allocate_weighted(500, (2, 1, 1)), (250, 125, 125))
        self.assertEqual(allocate_weighted(10, (1, 1, 1)), (4, 3, 3))

    def test_percentage_and_combination_arithmetic(self):
        self.assertEqual(percent_of(500, 25), 125)
        self.assertEqual(percent_of(500, 1), 5)
        self.assertEqual(combination_count(5, 2), 10)
        self.assertEqual(combination_count(5, 3), 10)
        self.assertEqual(combination_count(5, 0), 1)

    def test_candy_basket_is_stock_and_budget_bounded(self):
        lines, spent = build_candy_basket(100, self.catalog)
        self.assertEqual(spent, sum(line.line_total for line in lines))
        self.assertLessEqual(spent, 100)
        self.assertTrue(all(line.quantity <= self.catalog[line.catalog_index].stock for line in lines))

    def test_complete_greeting_graph_and_rotation(self):
        edges = build_greeting_graph(2, 5, 3)
        self.assertEqual(len(edges), 10)
        self.assertEqual(edges[-1].template_index, 0)

    def test_composite_report_keeps_budget_invariant_and_consumes_stock(self):
        plan = plan_gift(
            500, 5, self.catalog, ("greeting a", "greeting b", "greeting c"), senders=2
        )
        self.assertTrue(plan.verify())
        self.assertEqual(sum(plan.allocations), 500)
        self.assertEqual(plan.spent + plan.remaining, 500)
        self.assertEqual(len(plan.greeting_edges), 10)
        self.assertEqual(len(plan.baskets), 5)

    def test_rejects_invalid_and_oversized_inputs(self):
        calls = (
            lambda: allocate_equal(500, 0),
            lambda: allocate_weighted(500, (0, 0)),
            lambda: percent_of(500, 101),
            lambda: combination_count(5, 6),
            lambda: build_candy_basket(100, (Candy("bad", "candy", 0, 1),)),
            lambda: build_greeting_graph(1, 1, 0),
            lambda: plan_gift(500, 2, self.catalog, ("hello",), weights=(1,)),
        )
        for call in calls:
            with self.subTest(call=call):
                with self.assertRaises((TypeError, ValueError)):
                    call()


if __name__ == "__main__":
    unittest.main()
