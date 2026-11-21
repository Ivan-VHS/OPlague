from __future__ import annotations

import unittest

from tools.compute_ops import (
    accumulate, aggregate, amplify, cartesianize, combine, compute, compound,
    convolve, couple, cross_multiply, expand, exponentiate, factor, fuse,
    multiply, pair, product, scale,
)


class ComputeOperationsTests(unittest.TestCase):
    def test_scalar_vector_and_aggregate_products(self):
        self.assertEqual(multiply(6, 7), 42)
        self.assertEqual(product([2, 3, 4]), 24)
        self.assertEqual(scale([1, 2, 3], 2), [2, 4, 6])
        self.assertEqual(amplify(2.5, 4), 10.0)
        self.assertEqual(compound([1, 2], [3, 4]), [3, 8])

    def test_calculate_and_exponentiate(self):
        self.assertEqual(compute(7, 5, "add"), 12)
        self.assertEqual(compute(7, 5), 35)
        self.assertEqual(exponentiate(2, 8), 256.0)

    def test_sequence_and_matrix_operations(self):
        self.assertEqual(expand([1, 2], 2), [1, 2, 1, 2])
        self.assertEqual(accumulate([1, 2, 3]), [1, 3, 6])
        self.assertEqual(cross_multiply([1, 2], [3, 4]), [[3, 4], [6, 8]])
        self.assertEqual(cartesianize(["a", "b"], [1, 2]), [
            ["a", 1], ["a", 2], ["b", 1], ["b", 2]
        ])

    def test_factor_combine_fuse_pair_and_couple(self):
        self.assertEqual(factor(360), [2, 2, 2, 3, 3, 5])
        self.assertEqual(combine([1, 2], [3, 4]), [4, 6])
        self.assertEqual(fuse([1, 2], [3]), [1, 2, 3])
        self.assertEqual(pair("gpu", "driver"), ["gpu", "driver"])
        self.assertEqual(couple(["cpu", "gpu"], [1, 2]), [["cpu", 1], ["gpu", 2]])

    def test_aggregate_and_convolution(self):
        self.assertEqual(aggregate([1, 2, 3])["mean"], 2)
        self.assertEqual(aggregate([1, 2, 3])["product"], 6)
        self.assertEqual(convolve([1, 2, 3], [1, 1]), [1.0, 3.0, 5.0, 3.0])

    def test_invalid_inputs_are_rejected(self):
        calls = (
            lambda: multiply(True, 2),
            lambda: factor(0),
            lambda: exponentiate(0, -1),
            lambda: compute(1, 0, "divide"),
            lambda: combine([1], [1, 2]),
            lambda: couple([1], [1, 2]),
            lambda: convolve([], [1]),
            lambda: aggregate([]),
        )
        for call in calls:
            with self.assertRaises((TypeError, ValueError, OverflowError)):
                call()


if __name__ == "__main__":
    unittest.main()
