from __future__ import annotations

import unittest

from tools.metric_analysis import (
    analyze_device_profiles,
    aggregate_device_profiles,
    compare_profile_matrix,
    combine_uncorrelated_variances,
    parseval_energy,
    summarize_repeated_measurements,
)


class DeviceMetricAnalysisTests(unittest.TestCase):
    def test_compares_normalized_profiles(self) -> None:
        result = analyze_device_profiles(
            {"cpu": 0.8, "memory": 0.7, "thermal": 0.6},
            {"cpu": 0.9, "memory": 0.6, "thermal": 0.8},
            {"memory": 2.0},
        )
        self.assertEqual(result["schema"], "oplage.device-metric-comparison.v1")
        self.assertAlmostEqual(result["euclidean_distance"], (0.01 + 0.01 + 0.04) ** 0.5)
        self.assertAlmostEqual(result["quadratic_form"], 0.07)
        self.assertAlmostEqual(result["weighted_distance"], 0.07 ** 0.5)
        self.assertEqual(result["dimension_count"], 3)
        self.assertEqual(set(result["components"]), {"cpu", "memory", "thermal"})

    def test_orthogonality_is_scale_independent(self) -> None:
        result = analyze_device_profiles(
            {"axis_a": 1.0, "axis_b": 0.0},
            {"axis_a": 0.0, "axis_b": 1.0},
        )
        self.assertEqual(result["cosine_similarity"], 0.0)
        self.assertTrue(result["orthogonal"])

    def test_repeated_measurements_and_variance_composition(self) -> None:
        summary = summarize_repeated_measurements([10.0, 12.0, 14.0])
        self.assertEqual(summary["count"], 3)
        self.assertEqual(summary["mean"], 12.0)
        self.assertEqual(summary["sample_variance"], 4.0)
        self.assertEqual(combine_uncorrelated_variances([4.0, 9.0, 3.0]), 16.0)

    def test_parseval_energy(self) -> None:
        self.assertEqual(parseval_energy([1.0, 2.0, 2.0]), 9.0)


    def test_batch_profile_aggregation(self) -> None:
        result = aggregate_device_profiles([
            {"cpu": 0.8, "memory": 0.6},
            {"cpu": 0.6, "memory": 0.8},
        ])
        self.assertEqual(result["schema"], "oplage.device-metric-aggregate.v1")
        self.assertEqual(result["record_count"], 2)
        self.assertAlmostEqual(result["metrics"]["cpu"]["mean"], 0.7)
        self.assertAlmostEqual(result["metrics"]["cpu"]["product"], 0.48)
        self.assertAlmostEqual(result["metrics"]["memory"]["sample_variance"], 0.02)

    def test_cartesian_profile_comparison_matrix(self) -> None:
        result = compare_profile_matrix(
            [{"cpu": 0.8}, {"cpu": 0.5}],
            [{"cpu": 0.7}, {"cpu": 0.9}],
        )
        self.assertEqual(result["pair_count"], 4)
        self.assertEqual(
            [(item["reference_index"], item["candidate_index"]) for item in result["comparisons"]],
            [(0, 0), (0, 1), (1, 0), (1, 1)],
        )

    def test_rejects_mismatched_dimensions_and_bad_values(self) -> None:
        with self.assertRaisesRegex(ValueError, "dimensions differ"):
            analyze_device_profiles({"cpu": 0.5}, {"gpu": 0.5})
        with self.assertRaisesRegex(ValueError, "normalized"):
            analyze_device_profiles({"cpu": 2.0}, {"cpu": 0.5})
        with self.assertRaisesRegex(ValueError, "negative"):
            analyze_device_profiles({"cpu": 0.5}, {"cpu": 0.6}, {"cpu": -1.0})
        with self.assertRaisesRegex(ValueError, "negative"):
            combine_uncorrelated_variances([1.0, -0.1])


if __name__ == "__main__":
    unittest.main()
