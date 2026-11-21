# Federated integration: OPlague, Pytyliki and Reaper

OPlague owns Windows device inventory and driver-package inspection. Its
federation interface is read-only: it captures currently present PnP devices
through a fixed PowerShell Get-PnpDevice query, normalizes the results, and
emits a versioned JSON snapshot for downstream consumers.

## Device snapshot v1

Contract schema: [oplage.device-snapshot.v1.schema.json](../schemas/oplage.device-snapshot.v1.schema.json)

- Schema identifier: oplage.device-snapshot.v1
- Device identity: HMAC-SHA-256 pseudonym of the PnP InstanceId with domain separation; the raw InstanceId is omitted. Each default snapshot uses an ephemeral key, preventing cross-export correlation by default. A caller-managed protected key deliberately enables pseudonymous matching across snapshots. This is pseudonymization, not anonymization.
- Metric values: finite numbers normalized to [0, 1], higher means healthier.
- A zero package-integrity metric is paired with an audit-coverage metric, so
  no package scan is not silently reported as a pass.
- Snapshot fingerprint: SHA-256 over canonical JSON before the fingerprint field. Consumers recompute it and reject content mismatches. It detects content drift but is not a vendor signature or authenticity proof.

Profile dimensions are device_ok_ratio, device_problem_free_ratio,
device_class_coverage_ratio, device_identity_coverage_ratio,
package_integrity_ratio and package_audit_coverage_ratio.

## Commands

Capture present devices and optionally inspect UDRV package directories/ZIPs:

```powershell
python -m tools.federation snapshot --output device-snapshot.json
python -m tools.federation snapshot --package C:\\packages\\sample.udrv --output device-snapshot.json
```

Compare saved snapshots:

```powershell
python -m tools.federation compare --reference baseline.json --candidate current.json --output comparison.json
```

Snapshot requires Windows and the PnpDevice PowerShell module. Comparison
works cross-platform on saved JSON. Both commands only read inventory/files
and write the requested output. They never install, remove, enable, disable or
otherwise modify a device or driver.

## Consumer contract

Reaper uses read_json() to load the file, then validates the complete v1
envelope, device/package record shapes, summary counters, normalized metrics
and recomputed canonical SHA-256 fingerprint before extracting the metric
profile. The local schema copy is checked in at
[Reaper/schemas/oplage.device-snapshot.v1.schema.json](https://github.com/Ivan-VHS/Reaper/blob/main/schemas/oplage.device-snapshot.v1.schema.json).
oplage_compare() emits a read-only report and rejects dimension drift. Reaper
can pass an explicit trusted Pytyliki shared-library path to cross-check the
Euclidean distance through ABI v1.

## Security and limitations

- PowerShell receives a fixed command string; no user-supplied text is inserted.
- Inventory is bounded to 10,000 devices and 16 MiB of JSON.
- Raw PnP instance IDs are never exported. HMAC pseudonyms use ephemeral keys by default; reuse of a protected caller-managed key enables deliberate linkability.
- Optional package paths use the existing read-only UDRV inspector. This is not
  a general INF/catalog signature verifier.
- A snapshot is telemetry, not proof of driver trust or compatibility.
- Driver changes remain outside this integration and require separately
  reviewed dry-run and explicit confirmation.

## Optional direct Pytyliki cross-check

Device Metric Lab can cross-check its profile distance through Pytyliki ABI v1
without making the native library mandatory:

```powershell
python -m tools.federation compare --reference baseline.json --candidate current.json --pytyliki-library C:\\trusted\\Pytyliki\\build\\Release\\pytyliki_ffi.dll
```

The comparison keeps the OPlague metric-analysis result and adds a
native_cross_check object containing the Pytyliki distance, Python distance,
absolute error and a numerical tolerance result. The DLL/SO path must be
absolute and point to a trusted build; loading it executes native code. No
library is loaded unless this flag is provided.


## Cross-repository references

- **Shared 4 × 4 map:** [Project federation matrix](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md).
- **Reaper:** [repository](https://github.com/Ivan-VHS/Reaper), [federation contract](https://github.com/Ivan-VHS/Reaper/blob/main/docs/FEDERATED_INTEGRATION.md), [snapshot consumer](https://github.com/Ivan-VHS/Reaper/blob/main/reaper/federation.py), [project manifest](https://github.com/Ivan-VHS/Reaper/blob/main/project-contract.json).
- **Pytyliki:** [repository](https://github.com/Ivan-VHS/Pytyliki), [federation contract](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/FEDERATED_INTEGRATION.md), [public ABI header](https://github.com/Ivan-VHS/Pytyliki/blob/main/src/interop.h), [project manifest](https://github.com/Ivan-VHS/Pytyliki/blob/main/project-contract.json).
- **OPlague evidence:** [device snapshot producer](../tools/federation.py), [Pytyliki adapter](../tools/pytyliki_ffi.py), [inspection composer](../tools/report_composer.py), [project manifest](../project-contract.json).


## Reaper report consumer

OPlague validates Reaper's `reaper.oplage-comparison.v1` output through `tools.reaper_report`. The importer checks schema, read-only mode, finite normalized dimensions, component deltas, Python/native metric consistency and canonical report SHA-256. It returns an `oplage.reaper-report-audit.v1` summary. It never executes a report, loads the optional native library named in report metadata, or changes a device.

```powershell
python -m tools.reaper_report comparison.json --json
```

## OCTA-8 horizontal mesh

The shared [four-project OCTA-8 topology](OCTA_PYRAMID_FEDERATION.md) defines twelve directed peer links, four local self-loops and eight protocol facets. Reaper↔OPlague exchanges bounded read-only snapshots and comparison reports; Reaper↔Pytyliki and OPlague↔Pytyliki use synchronous request/response via explicit Pytyliki ABI v1 calls. VentuSample exports pack v1 manifests for Reaper's read-only metric audit. OPlague↔VentuSample is explicitly not applicable: device/driver diagnostics are not part of audio generation. The apex is metadata-only, not an executable gateway.
