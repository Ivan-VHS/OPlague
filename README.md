# OPlague — Driver Workbench

<p align="center">
  <a href="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml"><img alt="Windows desktop build" src="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml/badge.svg"></a>
  <img alt="runtime" src="https://img.shields.io/badge/runtime-Python%203.10%2B-0039A6?style=flat-square">
  <img alt="desktop" src="https://img.shields.io/badge/desktop-Windows-0A1E46?style=flat-square">
  <img alt="license" src="https://img.shields.io/badge/license-Apache--2.0-D52B1E?style=flat-square">
</p>

**OPlague is a Windows-first, read-only workbench for hardware inventory and driver-package diagnostics.** It inspects evidence and prepares reports; it does not install, remove, enable, disable, sign or roll back drivers.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Workbench

| Module | Purpose |
|---|---|
| Device inventory | Reads Windows Plug and Play metadata: device name, status, manufacturer and hardware ID. |
| INF / ZIP inspection | Reads selected INF metadata, computes SHA-256, inspects archive paths and resource limits, and records hardware-ID and target-architecture evidence. Package payloads are not extracted or executed. |
| Batch reports | Combines ordered inspection results with aggregate counts and a deterministic bundle fingerprint. |
| UDRV inspection | Validates a versioned manifest, declared payload inventory, sizes, hashes, paths and resource bounds. It does not install, load or execute payloads. |
| DRIVE-LENS evidence ledger | Keeps source-digest provenance, exact attribute/time-window grouping and explicit conflict retention. It does not produce an automatic driver verdict. |
| Compatibility dry-run | Links devices and INF Models entries only through exact normalized hardware-ID matches. Candidate edges are evidence for review, not rankings or compatibility certification. |
| Metric Lab | Compares normalized profiles using weighted distances, cosine similarity, orthogonality and repeated-run variance. |
| Device federation | Exports bounded JSON snapshots and compares saved snapshots offline. Export requires explicit operator confirmation. |
| Native cross-check | Optional Pytyliki C ABI v1 verification requires an explicitly supplied trusted library path. |
| QCS and systems catalogues | Validates domain syntax and reports PATH-discovered toolchain capabilities; it does not compile or execute hardware descriptions. |

## Desktop design: Duck Sovereign Canon

The Tk workbench uses a top-down workflow: device inventory, package evidence, compatibility dry-run, comparison and explicit export. White surfaces and deep blue carry information; red is reserved for signal and priority. Local serif headings, readable local sans-serif controls, compact rectangular panels, keyboard focus and reduced-motion behavior form the shared visual contract.

Read [the complete design doctrine](docs/DUCK_SOVEREIGN_CANON.md), [desktop design system](docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md) and [UI/UX architecture](docs/UI_UX_ARCHITECTURE.md). The design specification distinguishes illustrative layouts from screenshots of a running application.

## Run on Windows

Requirements: Windows x64 and Python 3.10+.

~~~sh
git clone https://github.com/Ivan-VHS/OPlague.git
cd OPlague
python oplague_app.py
python -m unittest discover -s tests -v
~~~

The desktop workflow builds OPlague.exe and publishes the archive as a workflow artifact. A v* tag publishes a GitHub Release.

## Read-only command-line tools

~~~sh
python tools/udrv_inspector.py path/to/package.udrv --json
python -m tools.federation snapshot --output device-snapshot.json
python -m tools.federation compare --reference baseline.json --candidate current.json
python -m tools.qcs dialects
python -m tools.qcs validate path/to/example.qcs
python tools/systems_languages.py --profile oplague
~~~

## Security, privacy and limits

- Imported packages are untrusted input. Path traversal, archive entry counts, expanded size, compression ratio and INF size are bounded.
- ZIP contents are inspected as metadata; driver payloads are not extracted or executed.
- Device identifiers are HMAC-pseudonymized for snapshots by default. Pseudonyms may remain linkable and are not equivalent to anonymization.
- Optional cross-snapshot matching requires an operator-managed protected key.
- Export is a separate, explicit operation; local inspection does not imply permission to share data.
- Package hashes establish byte-level integrity, not publisher identity, safety or compatibility.
- No driver installation/removal/enable/disable/signing/rollback, firmware changes or claimed live DPC/ISR diagnosis are provided.

## Documentation

- [DRIVE-LENS evidence ledger](docs/DRIVE_LENS_EVIDENCE_LEDGER.md)
- [UDRV format v1](docs/UDRV_FORMAT_V1.md)
- [Device compatibility graph](docs/DEVICE_COMPATIBILITY_GRAPH.md)
- [Governance and consent](docs/HUMAN_FIRST_GOVERNANCE.md)
- [Unified engineering standard](docs/UNIFIED_ENGINEERING_STANDARD.md)
- [Quality and commercial readiness](docs/QUALITY_COMMERCIAL_STANDARD.md)
- [Four-project federation](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md)

## License

[Apache License 2.0](LICENSE)