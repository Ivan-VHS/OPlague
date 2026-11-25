# DRIVE-LENS — Driver Evidence & Integrity Ledger

**Status:** implemented as a bounded Python module (`tools.driver_evidence`). DRIVE-LENS reconciles already-inspected metadata; it is not a driver recommender, installer, signature verifier or compatibility verdict engine.

## Data flow

The caller supplies observations from the existing read-only OPlague tools:

- PnP inventory fields;
- selected INF metadata;
- UDRV manifest/integrity reports;
- catalog metadata;
- an explicitly labelled operator annotation.

Each observation is bound to the digest of the exact source artifact and a relative metadata locator. A source digest identifies bytes; it does not authenticate a publisher.

## Privacy contract

- The raw PnP `InstanceId` is accepted only as input to HMAC-SHA-256 and is never copied into the output.
- Hardware-ID, serial and other `*_id` attribute values are independently HMAC-pseudonymized with attribute-domain separation.
- A caller-managed key of at least 32 bytes is mandatory. Keep it outside the exported ledger.
- Pseudonyms are linkable by design when the same key is reused; they are not anonymization.
- Locators are restricted to relative metadata paths / selectors, not absolute host file paths.

## Reconciliation rules

Records group only on exact pseudonymous subject, exact attribute and exact declared time window. No fuzzy matching or inferred hardware compatibility is performed.

Group states:

- `single_source`: one distinct source artifact digest;
- `multi_source_consistent`: multiple source artifact digests carry the same normalized value;
- `conflicted`: the same exact group contains different values.

`multi_source_consistent` does not mean independent verification. Two artifacts may share an upstream origin. Conflicts preserve all evidence IDs and remain unresolved; the module never chooses a preferred value.

## API

```python
from tools.driver_evidence import build_driver_evidence_ledger

ledger = build_driver_evidence_ledger(
    observations,
    identity_key=protected_key,  # bytes, at least 32 bytes
    generated_at_utc="2026-11-20T12:00:00Z",
)
```

Each observation has `instance_id`, `attribute`, scalar `value`, `source_kind`, `source_sha256`, `locator` and `captured_at_utc`. Optionally provide both `period_start_utc` and `period_end_utc`. Attribute names use normalized lowercase identifiers. ID-valued fields are pseudonymized before storage.

The returned JSON is deterministic for identical inputs and key. Its SHA-256 is a content fingerprint, not a vendor signature. Build the ledger in memory first; writing or sharing a device-derived export remains an operator-controlled action.

## Safety limits

DRIVE-LENS only compares metadata. It does not extract package payloads, execute binaries, modify drivers, bind a driver to a device or convert a hash match into trust. Existing exact Hardware ID dry-run and package validation remain separate evidence sources.
