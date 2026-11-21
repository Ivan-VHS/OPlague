# OPlague — Driver Workbench

<p align="center">
  <a href="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml"><img alt="Windows desktop build" src="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml/badge.svg"></a>
  <img alt="Python 3.10+" src="https://img.shields.io/badge/runtime-Python%203.10%2B-2563EB?style=flat-square">
  <img alt="Windows" src="https://img.shields.io/badge/desktop-Windows-DC2626?style=flat-square">
  <img alt="Apache 2.0" src="https://img.shields.io/badge/license-Apache--2.0-334155?style=flat-square">
</p>

**OPlague is a Windows-first, read-only workbench for hardware inventory and driver-package diagnostics.** It does not install or modify drivers.

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

## Desktop interface preview

<p align="center"><img src="assets/oplague-workbench-preview.svg" alt="Illustrative OPlague desktop interface preview" width="100%"></p>
<sub>Illustrative reconstruction based on the checked-in Tkinter layout, not a screenshot captured from a running Windows application.</sub>

## Workbenches and tools

- **Device inventory:** read-only Windows Plug and Play discovery with device name, status, manufacturer and hardware ID.
- **INF / ZIP inspector:** extract selected INF metadata, calculate SHA-256, inspect archive paths and resource limits, and report exact hardware-ID and target-architecture evidence. Package content is not extracted or executed.
- **Batch reports:** compose ordered inspection results with aggregate counts and a deterministic bundle fingerprint.
- **UDRV inspector:** validate a versioned manifest, payload inventory, declared sizes, hashes and path/resource bounds. It does not install, load or execute payloads.
- **DRIVE-LENS evidence ledger:** HMAC-pseudonymized device references, source-digest provenance, exact attribute/time-window grouping and explicit conflict retention across inspected PnP/INF/UDRV/catalog metadata. No automatic driver verdict ([design](docs/DRIVE_LENS_EVIDENCE_LEDGER.md)).
- **Compatibility dry-run:** connect devices and INF Models entries only through exact normalized hardware-ID matches. Candidate edges are not driver rankings or compatibility verdicts.
- **Metric Lab:** compare normalized profiles using weighted distances, cosine similarity, orthogonality and repeated-run variance.
- **Device federation:** export bounded versioned JSON snapshots and compare saved snapshots offline. Export requires explicit operator confirmation; raw PnP IDs are HMAC-pseudonymized with ephemeral keys by default or an optional protected key for deliberate cross-snapshot matching.
- **Native cross-check:** optional Pytyliki C ABI v1 metric verification when the caller supplies an explicit trusted library path.
- **QCS validator:** one compact grammar with 66 named hardware-domain profiles; validates contour metadata and handoff markers. It is not a compiler or hardware verifier.
- **Systems catalogue:** 66 language/toolchain capability entries with PATH-only discovery.

## Run the desktop app

Requirements: Windows x64 and Python 3.10+.

```bash
git clone https://github.com/Ivan-VHS/OPlague.git
cd OPlague
python oplague_app.py
python -m unittest discover -s tests -v
```

The Windows workflow builds `OPlague.exe` and uploads `OPlague-windows-x64.zip`. A `v*` tag publishes the archive as a GitHub Release.

## Useful read-only tools

```bash
python tools/udrv_inspector.py path/to/package.udrv --json
python -m tools.federation snapshot --output device-snapshot.json
python -m tools/federation compare --reference baseline.json --candidate current.json
python -m tools.qcs dialects
python -m tools.qcs validate path/to/example.qcs
python tools/systems_languages.py --profile oplague
```

## Project evolution and safety boundary

Mainline includes PnP inventory, bounded INF/ZIP inspection, architecture analysis, exact-ID dry-run planning, UDRV integrity checks, reports, metrics, device snapshots, Pytyliki interop and QCS validation.

**Not implemented:** driver installation/removal, enable/disable, signing, rollback, firmware changes or live DPC/ISR diagnostics. Package integrity does not establish vendor authenticity, driver safety or compatibility. Imported files are untrusted input; inspect reports before making manual decisions. The QCS body is retained as text and is never compiled or executed.

## Documentation and downloads

[DRIVE-LENS evidence ledger](docs/DRIVE_LENS_EVIDENCE_LEDGER.md)

[Human-first governance](docs/HUMAN_FIRST_GOVERNANCE.md) · [Anatidae desktop design system](docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md) · [UI/UX system](docs/UI_UX_SYSTEM.md) · [Atomic UI settings persistence](docs/ATOMIC_SETTINGS_PERSISTENCE.md) · [UDRV format](docs/UDRV_FORMAT_V1.md) · [Device compatibility graph](docs/DEVICE_COMPATIBILITY_GRAPH.md) · [Federation contract](docs/FEDERATED_INTEGRATION.md) · [QCS syntax](docs/QUANTUM_CONTOUR_SYNTAX.md) · [Unified engineering standard](docs/UNIFIED_ENGINEERING_STANDARD.md)


[Governance and consent](docs/HUMAN_FIRST_GOVERNANCE.md) · [Anatidae desktop design system](docs/ANATIDAE_DESKTOP_DESIGN_SYSTEM.md) · [UI/UX architecture](docs/UI_UX_ARCHITECTURE.md) · [12 animation principles](docs/DISNEY_MOTION_SYSTEM.md) · [Project contract](docs/UNIFIED_PROJECT_CONTRACT.md)
[Windows releases](https://github.com/Ivan-VHS/OPlague/releases) · [Desktop build](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)

**Federation:** [Reaper](https://github.com/Ivan-VHS/Reaper) · [Pytyliki](https://github.com/Ivan-VHS/Pytyliki) · [3×3 matrix](https://github.com/Ivan-VHS/Reaper/blob/main/docs/PROJECT_FEDERATION_MATRIX.md).

## Anatidae doctrine and safety contract

- **Operator intent first:** inventory and inspection are read-only; snapshot export requires explicit operator confirmation. Native interop is opt-in and requires an explicitly supplied trusted library path.
- **Treat packages as hostile input:** enforce path and resource bounds; inspect metadata without extracting or executing payloads.
- **Evidence, not guesswork:** compatibility dry-run links only exact normalized hardware IDs. A candidate edge is evidence for review, not a driver recommendation or compatibility verdict.
- **Privacy by minimization:** PnP identifiers are HMAC-pseudonymized with ephemeral keys by default; an optional protected key supports deliberate cross-snapshot matching. Pseudonyms remain potentially linkable and are not anonymization.
- **Safe non-goals:** no driver install/remove/enable/disable/sign/rollback, firmware changes or claimed live DPC/ISR diagnosis.
- **Accessible desktop behavior:** clear status and error language, keyboard/focus visibility, localization and reduced-motion support. Motion must never hide warnings or consequences.

Package hashes establish byte-level integrity only; they do not establish publisher identity, driver safety or compatibility.

## Documentation governance

[Documentation control](docs/DOCUMENTATION_CONTROL.md) defines the normative rules for public claims, evidence, privacy and integrations.

## License

[Apache License 2.0](LICENSE)

UI motion: [12 animation principles](docs/DISNEY_MOTION_SYSTEM.md).


## Quality and commercial readiness

OPlague now carries an evidence-linked 20 × 3 matrix for product quality, operational execution and commercial governance. Run **python tools/quality_commercial.py** or add **--format json**. The report does not imply driver compatibility, market demand, revenue or profitability. See [the quality-commercial standard](docs/QUALITY_COMMERCIAL_STANDARD.md).


The readiness report also prints a prioritized commercial action plan. Open items stay explicit: license review, support ownership, release delivery, user validation, cost measurement and any future pricing decision. No revenue, profit or market-fit claim is inferred.
