# Orthogonal Metric Diagnostics

OPlague uses the Pythagorean family as a numerical comparison layer for hardware and benchmark profiles. The implemented Device Metric Lab compares **user-supplied, normalized observations**; it does not probe undocumented counters, install drivers, alter device state or claim hardware compatibility.

## Device Metric Lab

Each profile is a JSON object with the same metric keys and values normalized to [0, 1], where higher means better. Convert inverse metrics such as latency or error rate before comparison (for example, map a bounded lower-is-better measure to a higher-is-better score). Do not mix units or scales.

The analyzer reports:

- n-dimensional Euclidean distance between profile vectors;
- a weighted quadratic form and weighted distance, with non-negative per-metric weights;
- dot product, cosine similarity, angle and a normalized orthogonality flag;
- squared-vector energies and per-dimension contributions;
- sample mean and sample variance for repeated local measurements;
- composition of variance components only when their pairwise covariance is zero.

Example profiles:

    {
      "cpu_score": 0.82,
      "memory_score": 0.71,
      "thermal_headroom": 0.68
    }

Use the Metric Lab tab in OPlague to compare reference and candidate profiles. The UI accepts JSON only and does not execute the supplied text.

## Mathematical guardrails

Euclidean distance and quadratic forms are appropriate for same-dimension normalized profiles. A positive diagonal weight matrix expresses the relative importance assigned by the operator; it is not learned from the machine. Cosine similarity measures profile direction rather than absolute performance. Near-orthogonality is a numerical relationship, not proof that two physical measurements are statistically independent.

Repeated-run sample variance measures observed spread. Adding separate variances is valid only when covariance terms are zero; independence is sufficient, but not required. Parseval energy is exposed for coefficient arrays only when callers use an orthonormal basis.

The de Gua face-area theorem, spherical/hyperbolic right-triangle identities, reciprocal-altitude identity and Minkowski spacetime interval are retained in the wider mathematical reference but are not treated as driver trust or compatibility scores. Their geometric assumptions do not describe Windows Plug and Play state or INF package validity.

## Safety

- No package contents are executed by this metric layer.
- All dimensions and values are bounded and checked for type, finiteness and range.
- Missing profile dimensions are rejected rather than silently imputed.
- Outputs are analysis summaries, not vendor certification, driver signatures or compatibility verdicts.
