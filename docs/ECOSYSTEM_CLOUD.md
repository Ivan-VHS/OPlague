# Ecosystem Cloud Adapter — OPlague

**Adapter:** `oplague` · **Shared contract:** `ivan-vhs.ecosystem-cloud.v1` · **Status:** contract-only

OPlague remains a read-only, evidence-oriented device and driver inspection workbench. Cloud storage is not a driver distribution channel and does not alter any device.

## Eligible data

Only sanitized report metadata, SHA-256 references, normalized compatibility summaries and review notes explicitly selected by the user may be published. The UI must present a preview and redaction summary before upload.

## Prohibited data and operations

Never upload driver binaries, INF payloads, raw device identifiers, serial numbers, raw USB descriptors, private signing material, secrets or unredacted local paths. A checksum is an integrity reference, not proof of authorship or safety. Cloud publication must never trigger driver installation, payload extraction or execution.

## Runtime rules

- Device inspection and archive/package analysis remain local and read-only.
- No network call occurs during enumeration, inspection or report generation.
- Publication is explicit, authenticated and tenant-scoped.
- A cloud outage must not affect offline inspection or saved local reports.
- Retry is bounded and idempotent; report history remains locally authoritative.

## Implementation boundary

This PR adds a contract manifest, documentation and regression test only. It does not add a Supabase SDK, upload worker, driver catalog, installer, firmware path or remote execution capability. Any later transport must preserve OPlague's read-only evidence boundary.
