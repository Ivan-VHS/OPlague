# Automatic compute operations

OPlague now provides a bounded numerical toolkit in `tools/compute_ops.py`.
It is intended for local diagnostics, metric aggregation and device/driver
analysis; it does not install, remove, stage, load or modify drivers.

The API covers checked multiplication and exponentiation, scaling and
element-wise composition, bounded expansion and accumulation, outer and
Cartesian products, prime factorization, pair/couple operations, summary
statistics, and one-dimensional linear convolution.

All inputs are checked for type and finite numeric values. Sequence products
and Cartesian expansions are capped at 100,000 items; integer growth is capped
at 4,096 bits; prime factorization accepts values from 1 through 10^12.
These utilities do not turn a compatibility candidate into an installation
recommendation or a safety verdict.
