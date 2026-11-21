# Unified Engineering Standard

**Profile:** Windows-first hardware inventory, driver-package inspection and portable audit tooling.

This standard turns the shared quality vocabulary into rules that can be implemented, tested and reviewed. It distinguishes implemented read-only capabilities from roadmap features and keeps privileged operations outside the inspection path.

## Product boundary

OPlague owns Windows Plug and Play inventory, driver-package inspection, UDRV integrity contracts, device-to-package evidence graphs, device snapshots and recovery/deployment preparation. Pytyliki owns reusable processor/numerical primitives. Reaper owns programming-language semantics and higher-level orchestration.

## Twenty quality groups, expressed as engineering rules

| Quality vocabulary | Enforceable meaning |
|---|---|
| Unified · Consolidated · Centralized | Use one normalized device model, one package-inspection pipeline and canonical report composition instead of parallel implementations. |
| Unique · Distinctive · Original | Keep the driver-management and hardware-audit domain distinct from processor benchmarking and language-runtime responsibilities. |
| Universal · Cross-platform · Compatible | Keep parsing, hashing, schema validation and offline report comparison portable; isolate live PnP capture behind a Windows adapter. |
| Standardized · Normalized · Systematized | Version snapshots, manifests and reports; normalize hardware identifiers and validate exact field types, sizes and permitted values. |
| Versatile · Multifunctional · Multipurpose | Support single-package inspection, ordered batch inspection, offline snapshot comparison and desktop workflows through shared core functions. |
| Integrated · Interoperable · Interconnected | Exchange only versioned JSON and optional explicit ABI calls; preserve compatibility when sibling projects are absent. |
| Harmonized · Synchronized · Aligned | Keep schema files, serializers, validators, CLI output, documentation and tests aligned before changing a public contract. |
| Adaptive · Flexible · Modular | Separate inventory providers, package readers, validators, compatibility evidence, report composition and UI orchestration. |
| Extensible · Scalable · Bounded | Enforce ceilings for devices, JSON, archive entries, expanded bytes, paths and payload sizes before processing untrusted input. |
| Comprehensive · Holistic · Multidisciplinary | Evaluate identity, architecture, package integrity, compatibility evidence, metrics and recovery separately; never collapse them into one unsupported verdict. |
| Exceptional · Unparalleled · Evidence-led | Report unknown or missing evidence explicitly; a candidate edge is not a driver-rank, signature or installability verdict. |
| Singular · Coherent · Consistent | Use consistent report statuses, error handling, normalized identifiers and deterministic serialization across inspection modes. |
| Exclusive · Explicit · Opt-in | Keep live system access, native library loading and future privileged actions behind explicit user-controlled entry points. |
| Coordinated · Combined · Composable | Compose per-file inspection results into bounded bundles without changing original packages or executing their content. |
| Cross-language · Stable · Interoperable | Preserve `oplage.device-snapshot.v1` and `oplage.inspection-bundle.v1` as versioned contracts; evolve through new schema versions. |
| All-purpose · Generalized · Hybrid | Generalize offline audit and report tooling while keeping Windows-only device acquisition clearly labeled. |
| Remarkable · Auditable · Reproducible | Include hashes, schema versions, normalized results and testable assumptions; a hash is not vendor authenticity. |
| Rare · One-of-a-kind · Purposeful | Prefer exact hardware-ID evidence over fuzzy name or prefix matching; avoid duplicate compatibility heuristics. |
| Unmatched · Unrivaled · Reliable | Fail closed on duplicate paths, traversal, symlinks, malformed manifests, duplicate JSON keys, non-finite numbers and resource-limit violations. |
| Integrated · Maintainable · Independent | Keep optional Pytyliki/Reaper bridges isolated and independently testable; OPlague must remain useful without either. |

## Existing integration contracts

- **Device snapshots:** `oplage.device-snapshot.v1` carries normalized inventory, privacy-conscious identity fingerprints and explicit read-only provenance.
- **Report composition:** ordered inspection bundles are deterministic summaries; their fingerprint is not a vendor signature or compatibility verdict.
- **Pytyliki:** a native metric cross-check is optional and requires an explicit absolute path to a trusted ABI v1 library.
- **Reaper:** can consume the versioned device snapshot; this does not grant driver-management permissions or change the snapshot's evidence limits.

## Required review gates for new capabilities

1. Treat device metadata, INF files, archives, manifests and binaries as untrusted input.
2. Bound input bytes, item counts, decompression, path lengths and computational work before allocation or extraction.
3. Reject traversal, symlink escapes, duplicate entries, duplicate JSON keys and non-finite numeric values.
4. Keep inspection read-only: do not extract, install, load or execute imported driver payloads.
5. Separate exact evidence from heuristics; use explicit `unknown` when evidence is insufficient.
6. Require explicit review, elevation, platform checks and a reversible plan before any future system-changing workflow is designed.
7. Update JSON Schema, validators, fixtures, tests, CLI/GUI labels and documentation together for every public contract change.

## Non-goals and truth rules

The UDRV format is a package contract, not a universal driver-compatibility guarantee. A SHA-256 digest proves byte identity, not publisher authenticity. A matched hardware ID is a candidate, not proof that a driver is trusted, correctly ranked or installable. Driver installation, removal, signing and rollback remain unimplemented unless separately delivered and verified.

## Related contracts

- [Federated integration](FEDERATED_INTEGRATION.md)
- [UDRV format v1](UDRV_FORMAT_V1.md)
- [Device compatibility graph](DEVICE_COMPATIBILITY_GRAPH.md)
- [Driver target architecture analysis](DRIVER_TARGET_ARCHITECTURE.md)
