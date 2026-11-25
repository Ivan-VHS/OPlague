# OPlague — NEXUS Device Evidence Profile v1

**Owner:** OPlague  
**Status:** additive integration profile  
**Compatibility:** OPlague remains an independent device, driver and gaming workbench.

## Product role

OPlague owns Windows device/driver inspection, bounded package analysis, Authenticode and hash evidence, compatibility candidates, gaming telemetry and read-only GPU snapshots. It is an evidence provider; it is not the DuckOS kernel driver manager and NEXUS does not authorize automatic driver installation.

## Existing evidence interfaces

| Existing interface | Data ownership | Consumer rule |
|---|---|---|
| `oplage.device-snapshot.v1` | Device inventory and pseudonymous fingerprints | Validate schema, source mode, bounds and digest |
| `oplage.gpu-telemetry.v1` | Read-only provider telemetry | Unsupported values remain null; record provider and capture time |
| UDRV inspection reports | Manifest, payload hashes, path and size evidence | Inspect only; never extract or execute untrusted payloads |
| Authenticode/SBOM reports | Signature, identity, hashes and package inventory | Distinguish hash, signature, publisher trust and compatibility |
| Gaming/frametime reports | Workload and performance measurements | Preserve hardware, provider, run conditions and sample windows |

## NEXUS consumers

- **VectorScope** presents device and GPU evidence with freshness and validity labels.
- **TrustVault** provides a review surface for signature, hash, SBOM and provenance evidence. It must not turn a SHA-256 digest into a trust verdict.
- **ThermalPilot** may display temperature and power values from supported providers, but remains advisory.
- **Nexus Hub** shows peer status and schema compatibility; it does not ask OPlague to install or load a driver.

## Explicit non-goals

- No direct VRAM mapping or GPU-driver bypass.
- No automatic driver replacement, firmware flashing, package execution or device mutation.
- No invented AMD/Intel sensor values when the provider is unavailable.
- No hidden clock, voltage, fan or power-limit control.
- No use of benchmark or compatibility reports as proof of certification.

A future mutation workflow must have its own authenticated native API, least-privilege capability, explicit user consent, pre-change snapshot, validation and rollback. It is not part of this profile.

## Acceptance

Every exported value has a provider and validity state. Invalid schemas, digest mismatch, unsupported provider, stale input and missing peer produce explicit errors or unavailable states. Inspection remains read-only and does not execute imported content.
