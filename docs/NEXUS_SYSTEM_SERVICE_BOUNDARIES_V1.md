# OPlague — NEXUS System-Service Boundaries v1

**Owner:** OPlague  
**NEXUS role:** read-only device, package, signature and GPU evidence provider  
**Status:** additive federation contract

OPlague remains an independent device/driver inspection and gaming-performance workbench. Its default operations are read-only. This profile does not turn OPlague into a DuckOS kernel driver manager, endpoint enforcement engine or network firewall.

## Service relationships

| DuckOS service / app | Permitted OPlague evidence | Boundary |
|---|---|---|
| KERNEL_SENTINEL | Device/package inventory, hashes, Authenticode metadata and available signature-verification results | Not a protected kernel measurement stream, malware verdict or process-memory scanner |
| SecurityModule / TrustVault | Signature, publisher, SBOM, digest and provenance evidence for operator review | A hash is not a signature; a valid signature is not proof that a package is safe or compatible |
| MEMORY_FORGE | GPU memory/telemetry values only when a supported provider supplies them | No direct VRAM mapping, allocator control or unsupported-value estimation |
| VECTOR_GATEWAY | No direct network enforcement dependency; may consume device inventory for diagnostics | Device evidence does not prove firewall state, VPN protection or DDoS mitigation |
| VectorScope / ThermalPilot | Supported GPU, thermal, power and frametime observations with source and capture metadata | Unknown, stale, permission-denied and unsupported values remain explicit |

## Evidence contract

1. Reuse `oplage.device-snapshot.v1`, `oplage.gpu-telemetry.v1`, existing package inspection records and report envelopes.
2. Validate schema version, payload bounds, source mode, capture time and digest before a consumer accepts the record.
3. Preserve provider identity, hardware/software context, units and validity for every metric.
4. Distinguish file hash, Authenticode signature, publisher identity, trust-root validation, package compatibility and security assessment.
5. Treat a missing sensor or unsupported provider as unavailable, never as a fabricated Intel/AMD reading.
6. Do not extract or execute untrusted packages as part of evidence collection.
7. Do not install, unload, enable or mutate drivers or firmware through NEXUS.

## Future privileged operations

Any later driver or device mutation requires a separate authenticated native DuckOS API, least-privilege capability, explicit operator consent, pre-change snapshot, validation and rollback. It is outside this profile.

## Acceptance

- Fixtures cover valid, malformed, oversized, stale, unknown-provider and digest-mismatch reports.
- Every consumer preserves evidence provenance and displays unsupported states.
- No evidence report is promoted to a certification, malware verdict or enforcement decision without a separate reviewed mechanism.

This profile connects OPlague as an evidence source only. It does not implement KERNEL_SENTINEL, SecurityModule or VECTOR_GATEWAY.
