# Universal Division & Decomposition Engine

**Status: architecture contract for OPlague; native implementation is not yet present.**

OPlague is being designed as a native desktop driver-management application. This
specification defines a portable contract for dividing, partitioning, comparing,
and recombining driver-package data without implying that a driver can safely be
split into independently installable pieces.

## Functional domains

1. **Arithmetic:** integer and rational division, quotient/remainder, modulo,
   exactness checks, ratios, and factorization metadata.
2. **Package decomposition:** partition manifests, file inventories, metadata,
   dependency edges, and validation evidence into bounded review units.
3. **Resource distribution:** allocate scan, hashing, indexing, and validation
   work by explicit weights and available capacity.
4. **Dependency-aware grouping:** keep inseparable package dependencies in one
   group; never split signed payloads or catalog relationships merely to balance
   file counts.
5. **Reconstruction:** recombine ordered manifests and verify content hashes,
   package identity, dependency closure, and original inventory equivalence.
6. **Planning and optimization:** compare candidate plans by measured elapsed
   time, memory, I/O, and validation outcomes; label estimates separately.
7. **Audit and rollback:** persist plan inputs, algorithm version, evidence,
   rejected candidates, and a reversible operation log.

## Safety invariants

- Inspection and planning are read-only by default.
- Partitioning a driver package is a data-management operation, not a claim that
  the resulting fragments are installable drivers.
- Driver payload bytes, signatures, catalog files, INF relationships, and
  dependency closure must remain intact.
- No package is installed, removed, modified, or elevated by the planner.
- Imported manifests and metadata are untrusted input and require schema,
  size, path-traversal, and hash validation.
- A plan must conserve the complete input inventory and be reproducible.
- Any later privileged action remains a separate, explicit, reviewable workflow.

## Plan lifecycle

`DISCOVER -> VALIDATE -> MODEL_DEPENDENCIES -> PROPOSE -> SIMULATE -> VERIFY ->
REVIEW -> APPLY`

The first seven stages are non-mutating. `APPLY` is reserved for a separately
authorized operation with a rollback strategy. Automatic improvement may
generate and compare proposals, but it cannot grant itself installation
privileges or bypass signature and operating-system policy.

## Allocation rules

- Equal allocation uses quotient and remainder; earlier groups receive the
  indivisible remainder in a stable order.
- Weighted allocation uses a deterministic largest-remainder method.
- Dependency-aware allocation treats strongly connected dependency groups as
  indivisible units.
- Every allocation must conserve the total item/byte/work count.
- Recombination must reproduce the original ordered inventory and all recorded
  hashes.

## Acceptance criteria for the native implementation

- Unit tests cover positive/negative Euclidean division, zero divisors,
  overflow boundaries, exact fractions, and remainder conservation.
- Partition tests cover empty inventories, one-item groups, oversized groups,
  dependency cycles, and deterministic tie-breaking.
- Property tests verify conservation and lossless reconstruction.
- Malformed or oversized manifests fail closed with actionable diagnostics.
- Benchmarks compare the same input and hardware profile; no speedup is claimed
  from heuristic scores alone.
