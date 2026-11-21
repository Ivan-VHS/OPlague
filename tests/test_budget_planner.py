from __future__ import annotations

import unittest

from budget_planner import BudgetError, calculate_budget


class OPlagueBudgetTests(unittest.TestCase):
    def test_weekly_plan_equals_500(self):
        result = calculate_budget()
        self.assertEqual(result["planned_uah"], 500)
        self.assertEqual(result["remaining_uah"], 0)
        self.assertTrue(result["within_budget"])

    def test_over_budget_is_reported_without_clamping(self):
        result = calculate_budget(500, overrides={"food": 350, "transport": 200})
        self.assertEqual(result["planned_uah"], 650)
        self.assertEqual(result["over_budget_uah"], 150)
        self.assertFalse(result["within_budget"])

    def test_coffee_scenario_uses_460_and_keeps_40_reserve(self):
        result = calculate_budget(scenario="coffee")
        by_id = {row["id"]: row["amount_uah"] for row in result["allocations"]}
        self.assertEqual(by_id["leisure"], 460)
        self.assertEqual(by_id["reserve"], 40)

    def test_invalid_inputs_are_rejected(self):
        for amount in (-1, True, 1_000_001):
            with self.subTest(amount=amount), self.assertRaises(BudgetError):
                calculate_budget(amount)
        with self.assertRaises(BudgetError):
            calculate_budget(overrides={"unknown": 1})
        with self.assertRaises(BudgetError):
            calculate_budget(overrides={"food": -1})

    def test_user_supplied_price_ranges_are_preserved(self):
        result = calculate_budget()
        item = next(x for x in result["reference_prices"] if x["item"] == "Гречка")
        self.assertEqual((item["min_uah"], item["max_uah"]), (75, 88))
        self.assertIn("не являются", result["price_basis"])


if __name__ == "__main__":
    unittest.main()
