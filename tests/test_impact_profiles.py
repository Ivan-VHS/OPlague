from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from oplague.impact import (DIMENSIONS, PROFILES, get_profile, rank_profiles,\n                            rank_profiles_by_total_native, search_profiles, load_profiles)


class ImpactProfileTests(unittest.TestCase):
    def test_registry_has_twenty_sequential_profiles(self):
        self.assertEqual(len(PROFILES), 20)
        self.assertEqual([item["id"] for item in PROFILES], list(range(1, 21)))

    def test_all_dimensions_are_ordinal_and_complete(self):
        for profile in PROFILES:
            self.assertEqual(set(profile["ranks"]), set(DIMENSIONS))
            self.assertTrue(all(1 <= value <= 5 for value in profile["ranks"].values()))

    def test_search_matches_each_lexical_component(self):
        self.assertEqual(search_profiles("баллистический")[0]["id"], 1)
        self.assertEqual(search_profiles("массивный")[0]["id"], 1)
        self.assertEqual(search_profiles("гиперзвуковой")[0]["id"], 5)

    def test_get_by_id_and_term(self):
        self.assertEqual(get_profile(20)["sound"], "Оглушительность")
        self.assertEqual(get_profile("Дальнобойный")["id"], 19)

    def test_unknown_and_ambiguous_queries_are_rejected(self):
        with self.assertRaises(KeyError):
            get_profile("not-a-profile")
        with self.assertRaises(ValueError):
            get_profile("гром")

    def test_ranking_is_descending_and_stable(self):
        ordered = rank_profiles("reach")
        ranks = [item["ranks"]["reach"] for item in ordered]
        self.assertEqual(ranks, sorted(ranks, reverse=True))
        self.assertEqual(ordered[0]["id"], 5)

    def test_native_total_ranking_delegates_to_reaper(self):
        from unittest.mock import patch

        def native_score(expression, library_path):
            self.assertEqual(library_path, "/trusted/reaper/libreaper_ffi.so")
            return sum(int(part.strip()) for part in expression.split("+"))

        with patch("tools.reaper_ffi.evaluate_i64", side_effect=native_score) as evaluator:
            ranked = rank_profiles_by_total_native("/trusted/reaper/libreaper_ffi.so")
        self.assertEqual(len(ranked), 20)
        scores = [item["native_total_score"] for item in ranked]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(evaluator.call_count, 20)
        self.assertEqual(set(ranked[0]), set(PROFILES[0]) | {"native_total_score"})

    def test_native_total_ranking_rejects_malformed_profiles(self):
        from unittest.mock import patch

        invalid = {"id": 1, "ranks": {"acoustic": 2}}
        with patch("tools.reaper_ffi.evaluate_i64") as evaluator:
            with self.assertRaisesRegex(ValueError, "incomplete"):
                rank_profiles_by_total_native("/trusted/reaper/libreaper_ffi.so", [invalid])
        evaluator.assert_not_called()

    def test_invalid_dimension_is_rejected(self):
        with self.assertRaises(ValueError):
            rank_profiles("unknown")

    def test_registry_rejects_missing_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registry.json"
            path.write_text(json.dumps({"schema_version": 1, "profiles": [dict(PROFILES[0])]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_profiles(path)


if __name__ == "__main__":
    unittest.main()
