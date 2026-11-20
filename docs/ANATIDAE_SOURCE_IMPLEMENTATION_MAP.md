# Anatidae Source-Document Implementation Map — OPlague

**Feature name:** Flock Batch Gate (FBG)

**Scope:** bounded, ordered, read-only INF/ZIP batch preflight and driver evidence workbench.

The uploaded AETHER-ANAS / Anatidae document is applied to OPlague through security boundaries, bounded dataflow, human-first inspection UX, deterministic evidence and explicit capability limits. Compiler-specific requirements are mapped to their sibling repository Reaper; driver installation and other privileged system mutations remain outside this product's current safety boundary.

## 1. New Flock Batch Gate

Module: `tools/inspection_batch.py`; UI integration: `oplage_app.py`; tests: `tests/test_inspection_batch.py`.

- Preflight the entire selection before inspecting any item.
- Limit a batch to 64 packages by default.
- Enforce the existing 512 MiB per-file inspection ceiling and an 8 GiB aggregate source-byte budget.
- Reject missing paths, symlink paths, non-files and unsupported extensions before processing.
- Inspect synchronously, in supplied order, with no unbounded worker pool or result queue.
- Preserve the existing inspector as the only package parser; the batch adapter does not extract or execute payloads.

Synchronous one-at-a-time processing is deliberate backpressure: the next package is not opened until the current inspection returns. This is not a claim of parallel driver processing, distributed execution or installation.

## 2. Ten renunciations mapped to a driver workbench

| Source doctrine | OPlague realization | Status / boundary |
|---|---|---|
| Three-medium existence | local Windows PnP capture, portable offline package inspection and offline snapshot comparison are separated by explicit adapters. | Partial; no GPU/cloud driver execution. |
| Hydrodynamic calm | desktop status, structured reports, batch workflow and evidence views hide routine mechanics but preserve detail. | Existing UI contract; diagnostics remain visible. |
| Ontological duck typing | typed Python structures, JSON schemas and normalized device/package models define observable contracts. | Partial; no compiler-level structural type system. |
| Feather-oil / explicit effects | inventory is read-only, snapshot export is explicit, native ABI loading is opt-in and future privileged actions have separate gates. | Existing hard boundary. |
| Flock / collective aerodynamics | FBG preflights a bounded set, retains order and applies serial backpressure. | Implemented; intentionally not parallelized. |
| Rounded visual ergonomics | Anatidae design tokens, keyboard/focus, responsive reflow and reduced-motion rules. | Existing UI/design contract. |
| Semantic hypergraph | device-to-package compatibility graph and evidence ledger model explicit nodes/edges/observations. | Existing domain graph, not a general programming-language graph. |
| Content-addressed identity | package SHA-256, source digests and deterministic bundle fingerprints support byte-level provenance. | Existing; hash identity is not publisher authenticity. |
| Habitats / FBIP | bounded streaming reads, limits on archive entries/bytes/paths and sequential batch inspection. | Partial; no general region allocator/FBIP. |
| Immune inputs / cost transparency | hostile archive/path/JSON validation, HMAC pseudonyms, exact evidence grouping and explicit memory/byte caps. | Implemented in specific input paths; not a universal taint type. |

## 3. Twelve Creator commandments — OPlague acceptance rules

1. **Uniqueness:** remain the driver evidence and package audit workbench; compiler semantics stay with Reaper and generic processor kernels with Pytyliki.
2. **Zero ambiguity:** distinguish `verified`, `unknown`, `disputed` and `candidate`; never infer safety from an exact-ID match.
3. **Orthogonality:** discovery, inspection, evidence reconciliation, compatibility dry-run and export are separate stages.
4. **Human-first diagnostics:** identify the package, field, path or evidence source that failed.
5. **Fast feedback:** keep preflight bounded; measure UI latency rather than promise 16 ms for all hosts.
6. **Self-hosting:** not a driver-workbench requirement.
7. **Seamless bridge:** Pytyliki ABI calls are opt-in and use an explicit trusted path.
8. **Cognitive scaling:** make single-package inspection simple and expose batch/evidence tools progressively.
9. **Computational ecology:** bound item count, byte count, archive expansion and concurrent work; current batch runner is sequential.
10. **Stable core:** version UDRV, snapshots and report schemas before changing fields.
11. **Open tooling:** retain CLI inspectors, JSON reports, schemas and deterministic fingerprints.
12. **Joy of creation:** calm UI and purposeful motion never obscure warnings or user intent.

## 4. Sixty-six engineering laws in five driver-domain clusters

- **1–14 — resources and state:** memory/byte ceilings, deny-by-default permissions, privacy minimization, no hidden state mutation, explicit evidence provenance. Anchors: UDRV inspector, policy/consent docs, DRIVE-LENS evidence ledger.
- **15–26 — flow and execution:** immutable inspection, one-way read paths, symmetric file closing, bounded archive reads and explicit integration friction. Anchors: INF/ZIP inspector, report composer, FBG.
- **27–40 — types and logic:** strict schema fields, finite numeric values, exact identifiers, validated hashes, no ambiguous matching and explicit unknowns. Anchors: device-snapshot schema, UDRV manifest rules, metrics and device graph.
- **41–50 — evolution and ecology:** versioned package/snapshot formats, evidence conflicts preserved rather than erased, module boundaries, prevention-first checks and humane diagnostics. Anchors: schemas, tests, UI docs, governance.
- **51–66 — systems engineering:** bounded throughput, partial failure reporting, optional sibling-project contracts, deterministic report fingerprints, debuggable abstractions and test-led claims. Anchors: federation, FBG, Pytyliki interop, QCS and CI.

## 5. Twelve special law/formula models

The source's Trauman, Baus–Bayes, Gause, Strauss, Bergmann, Dilman, Tilman, Spillman, Besse, Hess, Messe and Little–Tillman–Yoshia models inform practical trade-offs: track resource costs; preserve uncertainty; avoid duplicate heuristics; evolve formats compatibly; keep APIs small; reject accumulating errors; optimize the actual bottleneck; limit low-value features; balance data granularity; keep deterministic transformations; isolate dependencies; and bound queues. The FBG's count/byte budgets and serial consumption are the queueing/backpressure application, not a scientific claim about driver safety.

## 6. Six hundred sixty-six rules — complete range-to-domain traceability

| Source range | Source theme | OPlague mapping |
|---|---|---|
| 1–111 | Three-medium existence and computation ontology | local PnP adapter, portable offline package inspection and federated offline comparison; remote execution is not in product scope. |
| 112–222 | Calm surface and transparent internals | status-aware desktop workbench, reports, digest/provenance views, explicit limits and deterministic batch order. |
| 223–333 | Behavioral typing and strong type discipline | strict JSON Schema, normalized hardware IDs, validated UDRV fields and explicit compatibility graph contracts. |
| 334–444 | Effects and immune barrier | symlink/traversal/duplicate-key/size checks, HMAC pseudonyms, opt-in native bridge and read-only inspection. |
| 445–555 | Flock concurrency and backpressure | FBG sequential bounded pipeline; no unbounded queue or concurrent archive expansion. |
| 556–666 | Human ergonomics, freedom and creator code | tri-color UI, accessible text statuses, reduced motion, CLI tooling, versioned open schemas and clear non-goals. |

The six source ranges are used as a coverage index, not as 666 claims of implemented driver operations. Language-specific capabilities (compiler, AST, arbitrary algebraic effects, general semantic graph execution, self-hosting) are owned by Reaper. Generic CPU/metric kernels belong to Pytyliki.

## 7. Strong/weak types and the 150 maxim compendium

The document's strong-type discussion becomes strict boundary validation: raw package/device metadata is not accepted as a trusted driver verdict. Domain IDs, package digests, timestamps, architecture labels and bounded numeric metrics are checked before they enter normalized records. The Chinese maxim compendium contributes review heuristics—verify source evidence, preserve multiple viewpoints, prevent cascades, keep authority clear, and prioritize prevention—but never replaces exact package bytes, schema checks or Windows platform evidence.

## 8. Tri-Color Duck UI

Use the shared 65/25/10 palette: porcelain white (`#FFFFFF`, `#F4F7FB`), cobalt/azure (`#0052CC`, `#0A1F44`) and signal red (`#E62E2D`, `#FF4D4F`). A warning must have text and an icon/state label; color alone is insufficient. Reduced-motion settings are respected, and motion never hides evidence conflicts or destructive consequences.

## 9. Safety invariants and acceptance tests

- Batch preflight must finish before the first package inspector invocation.
- Default maximum is 64 selected packages, 512 MiB per package and 8 GiB aggregate source bytes.
- All package results remain in selection order; only one inspector call is active at a time.
- Symlinks, missing files and unsupported formats fail closed.
- INF/ZIP content remains unextracted and unexecuted; no driver is installed, removed, loaded, signed, rolled back or modified.
- Exact hardware-ID edges remain candidates, not safety/compatibility verdicts.
- SHA-256 proves byte identity only, not publisher authenticity or trustworthiness.
- CI and unit tests—not prose—define what is actually implemented.

## 10. Implementation anchors

New: `tools/inspection_batch.py`, `tests/test_inspection_batch.py`.

Updated: `oplage_app.py` (batch UI uses the bounded adapter).

Existing: `tools/udrv_inspector.py`, `tools/driver_evidence.py`, `tools/device_graph.py`, `tools/report_composer.py`, `schemas/oplage.device-snapshot.v1.schema.json`, `docs/DRIVE_LENS_EVIDENCE_LEDGER.md`, `docs/UDRV_FORMAT_V1.md`, `docs/UNIFIED_ENGINEERING_STANDARD.md`, `docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md`.
