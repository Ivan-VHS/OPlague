# Inspection report composition architecture

## Purpose and product boundary

OPlague combines already-produced, read-only package inspection results into one deterministic inventory summary. Composition does not install, unpack, load, sign, repair or execute driver content. The 666-term concatenation taxonomy is used as an architecture crosswalk, not as a claim that OPlague contains a database, compiler, audio engine or distributed platform.

## Implemented feature

`tools/report_composer.py` provides `compose_inspection_reports(reports)`:

- Accepts reports already returned by OPlague's local INF/ZIP inspector.
- Preserves the user's input order and creates one versioned `oplage.inspection-bundle.v1` document.
- Aggregates package count, reported bytes, archive entry count, expanded bytes, INF count and catalog count.
- Validates report types, formats, SHA-256 strings, non-negative sizes, archive bounds, metadata fields and duplicate file digests.
- Computes a canonical SHA-256 digest over the ordered bundle summary.
- Enforces limits of 256 reports, 64 GiB total reported input size and per-archive bounds already used by the inspector.

The desktop package tab exposes **Batch inspect…** so users can select multiple INF/ZIP files and view the composed report. No archive is extracted as part of this workflow.

## Six-domain crosswalk

| Domain | OPlague mapping | Status |
|---|---|---|
| 1. Strings, parsing, serialization | Canonical JSON serialization of the report bundle | Implemented |
| 2. Streams and pipelines | Ordered aggregation of independent local inspection results | Implemented |
| 3. Databases and relational joins | Bundle totals provide a report-level summary; no persistent database or SQL joins are claimed | Partial |
| 4. Build and integration | Composer is imported by the desktop app and covered by unit tests | Implemented |
| 5. UI and multimedia composition | Desktop batch-selection and report presentation; no media compositor | Partial / otherwise not applicable |
| 6. Algebra and integrity semantics | Deterministic ordered composition and bundle SHA-256 fingerprint | Implemented |

## Digest meaning

The bundle digest is a reproducible fingerprint of the normalized report summary. It is not a digital signature, vendor authenticity proof, certificate-chain validation, driver compatibility verdict or guarantee that the source files remain unchanged after inspection. Individual package digests are copied from the inspector's local file-hash result.

## Safety contract

- Inspection remains local and read-only.
- Package files are not extracted, executed, loaded or installed.
- A duplicate digest is rejected instead of being silently double-counted.
- Size and collection limits are checked before report composition grows without bound.
- The bundle is an evidence summary; missing or unsupported fields are not invented.
