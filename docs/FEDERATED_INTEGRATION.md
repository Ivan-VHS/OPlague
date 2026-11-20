# Federated integration: OPlague, Pytyliki and Reaper

OPlague owns Windows device inventory and driver-package inspection. Its
federation interface is read-only: it captures currently present PnP devices
through a fixed PowerShell Get-PnpDevice query, normalizes the results, and
emits a versioned JSON snapshot for downstream consumers.

## Device snapshot v1

Contract schema: [oplage.device-snapshot.v1.schema.json](../schemas/oplage.device-snapshot.v1.schema.json)

- Schema identifier: oplage.device-snapshot.v1
- Device identity: stable SHA-256 pseudonymous fingerprint of the PnP InstanceId; the raw InstanceId is omitted. This is not anonymization: snapshots remain linkable, and low-entropy identifiers may be guessable.
- Metric values: finite numbers normalized to [0, 1], higher means healthier.
- A zero package-integrity metric is paired with an audit-coverage metric, so
  no package scan is not silently reported as a pass.
- Snapshot fingerprint: SHA-256 over canonical JSON before the fingerprint field. It detects accidental drift but is not a vendor signature or authenticity proof.

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

Reaper uses read_json() to load the file, oplage_metrics() to validate/extract
the metric profile, and oplage_compare() to create a report. Reaper can pass an
explicit trusted Pytyliki shared-library path to the comparison built-in to
calculate the Euclidean distance through Pytyliki ABI v1.

## Security and limitations

- PowerShell receives a fixed command string; no user-supplied text is inserted.
- Inventory is bounded to 10,000 devices and 16 MiB of JSON.
- PnP instance IDs are hashed before export to avoid serial-bearing identifiers.
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

- **Shared 3 × 3 map:** [Project federation matrix](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md).
- **Reaper:** [repository](https://github.com/Ivan-VHS/Reaper), [federation contract](https://github.com/Ivan-VHS/Reaper/blob/main/docs/FEDERATED_INTEGRATION.md), [snapshot consumer](https://github.com/Ivan-VHS/Reaper/blob/main/reaper/federation.py), [project manifest](https://github.com/Ivan-VHS/Reaper/blob/main/project-contract.json).
- **Pytyliki:** [repository](https://github.com/Ivan-VHS/Pytyliki), [federation contract](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/FEDERATED_INTEGRATION.md), [public ABI header](https://github.com/Ivan-VHS/Pytyliki/blob/main/src/interop.h), [project manifest](https://github.com/Ivan-VHS/Pytyliki/blob/main/project-contract.json).
- **OPlague evidence:** [device snapshot producer](../tools/federation.py), [Pytyliki adapter](../tools/pytyliki_ffi.py), [inspection composer](../tools/report_composer.py), [project manifest](../project-contract.json).
