# Quality, Repeatability and Native Integration

## Quality
Device and driver findings must be evidence-backed, read-only by default, failure-contained and attributable to a concrete inspection run. Reports should distinguish observed facts, inferred compatibility and unavailable data.

## Repeatability
Repeated scans and report generation must define a stable input snapshot, bounded batch size, ordering, cancellation behavior and partial-failure reporting. Re-running a read-only inspection must not modify driver state. Exported artifacts must retain provenance and stable versioned contracts.

## Native integration
Use operating-system and device interfaces through narrow native boundaries. Keep UDRV, INF, device snapshots and inspection bundles versioned; avoid lossy translations between the native inventory and normalized reports. UI integration must preserve platform conventions and surface permission or capability limits clearly.

## OPlague application
Prioritize the read-only device inventory, compatibility graph, driver-evidence ledger, inspection batching, stable reports and native desktop boundary. Any future driver-changing operation must remain separately permissioned and must not be implied by inspection features.

## Acceptance and evidence
quality-repeatability-native.v1.json records implementation and verification evidence for every criterion. The validator checks the manifest shape, unique IDs and that referenced files exist. It is a policy-integrity check, not a replacement for unit tests, operating-system integration tests, security review or packaging checks.

Use implemented only when code and a maintained test or workflow support the requirement. Use planned for incomplete work. Use not_applicable only with a written reason.

Local checks: python tools/validate_quality_repeatability_native.py --self-test and python tools/validate_quality_repeatability_native.py --json.
