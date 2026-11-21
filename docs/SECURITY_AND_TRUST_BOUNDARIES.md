# Security and trust boundaries — OPlague

## Scope and current operating model

OPlague is currently a **read-only Windows workbench** for device inventory, driver-package inspection and evidence-based comparison. It does not install, load, stage or modify drivers. Any future privileged workflow is out of scope until separately implemented, reviewed and explicitly approved by an operator.

## Assets and trust boundaries

| Boundary | Untrusted material | Required handling |
|---|---|---|
| Windows device inventory | host-reported IDs and status | read-only collection; preserve source and collection time |
| INF metadata | package text, paths, architecture declarations | parse as data; never execute INF directives |
| ZIP / UDRV package | archive paths, manifests and payloads | enforce entry, expanded-size and total-size limits; reject traversal and malformed entries |
| Hash inspection | file bytes and digest metadata | use cryptographic digest for byte identity only; do not infer publisher trust |
| Signature evidence | signature and certificate metadata | distinguish signature validity, publisher identity, revocation and compatibility |
| Compatibility graph | normalized hardware IDs | exact matches are candidate links, not install authorization |
| Reports / pseudonyms | device identifiers and derived evidence | minimize, redact and avoid raw identifiers in public logs |

## Non-negotiable safety rules

- No driver installation, loading, service creation, registry modification or system configuration write is performed by the current workbench.
- Never disable Windows driver-signature enforcement or silently elevate privileges.
- Package contents remain untrusted even when the archive opens or a SHA-256 digest matches.
- A digest proves byte identity, not source authenticity, publisher identity, compatibility or safety.
- INF parsing is metadata inspection, not execution of installation directives.
- Resource limits must be applied before extraction or large allocation; reject path traversal and decompression bombs.

## Future privileged workflows

If installation or rollback is ever introduced, it requires a separate design and review covering signed packages, explicit user consent, least privilege, Windows-native installation APIs, recovery/rollback, audit records and failure injection. The present read-only application must not be documented as having these capabilities.

## Failure behavior

Malformed packages, invalid paths, excessive entry counts, expanded-size overruns, signature uncertainty or missing evidence must yield a bounded error or an explicitly inconclusive report. Do not convert incomplete evidence into a positive compatibility or safety verdict.

## Verification evidence

For changes to package or device boundaries, add:
1. tests for malformed INF/ZIP/UDRV inputs;
2. archive traversal and decompression-limit tests;
3. hash and manifest consistency tests;
4. tests that prove inspection does not mutate system state;
5. privacy tests for identifiers, pseudonyms and report serialization;
6. fuzz tests for parsers and archive metadata where supported.

Run the AppGuard catalog checks:

```sh
python scripts/validate_beelzebul_appguard.py
python -m unittest discover -s tests -p "test_beelzebul_appguard.py" -v
```

These commands validate the catalog contract, not driver-signature verification or Windows installation safety.

## AppGuard status vocabulary

- **planned** — catalogued; no executable enforcement claim.
- **partial** — a named subset is implemented and evidenced.
- **implemented** — enforcement code and focused tests exist.
- **verified** — implementation, tests and review evidence are linked.

The current AppGuard PR adds a policy catalog and CI checks. It does not enable privileged driver operations or claim 666 active protections.

## Change and release checklist

- Document exact archive limits and accepted formats alongside schemas and parser tests.
- Distinguish digest integrity, signature authenticity and device compatibility.
- Preserve read-only guarantees in code, UI, tests and README.
- Treat all identifiers as sensitive operational data; log only what is necessary.
- Keep screenshots genuine and ensure they do not expose private device identifiers.
