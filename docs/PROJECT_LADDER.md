# Project Evolution Ladder — OPlague

**Current rung:** 04 — **Ascension**  
**Assessment:** Provisional documentation review · 25 November 2026  
**Next rung:** 05 — **Vanguard**

This is a project-level maturity snapshot under the [canonical Ivan-VHS Project Evolution Ladder](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/PROJECT_EVOLUTION_LADDER.md). It does not replace capability statuses, release versioning or domain-specific stage names. SemVer remains unchanged.

## Evidence considered

- [`docs/FEATURES.md`](https://github.com/Ivan-VHS/OPlague/blob/main/docs/FEATURES.md) — The feature matrix documents read-only inventory, bounded INF/ZIP inspection, Authenticode metadata, compatibility evidence, UDRV validation and local reports.
- [`docs/ARCHITECTURE.md`](https://github.com/Ivan-VHS/OPlague/blob/main/docs/ARCHITECTURE.md) — The workflow is described as local input, bounded parser, evidence record, dry-run report and explicit export.

The initial rung is **provisional**: it was assigned from documented implementation boundaries. No source-level deep audit, test run or CI rerun was performed as part of ladder adoption. It is not a new certification and must not upgrade individual capability statuses.

## Known limits

- Package inspection does not certify drivers or install, load or mutate device state.
- No test or CI workflow was re-run during ladder adoption.

## Next promotion gate — 05 Vanguard

- Exercise the end-to-end inspection/report workflow in the declared Windows CI target.
- Add adversarial and fuzz coverage for untrusted PE, INF, ZIP and UDRV inputs.
- Keep read-only guarantees explicit and regression-tested across integrations.

## Machine-readable record

The [`.github/project-ladder.v1.json`](https://github.com/Ivan-VHS/OPlague/blob/main/.github/project-ladder.v1.json) file is the repository-owned record. Update it in the same PR as a material change to project scope, runtime, integration boundaries or acceptance evidence. Promote only when the full cumulative gate is supported by source and reproducible verification.
