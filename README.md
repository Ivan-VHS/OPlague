
<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-banner-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-banner-light.svg"><img src="assets/readme/hero-banner-light.svg" alt="OPlague device, driver and gaming workbench" width="880"></picture></p>
<h1 align="center">OPlague — Device, Driver and Gaming Performance Workbench</h1>
<p align="center"><strong>A local Windows workstation for bounded device/driver inspection, evidence reports and reversible gaming-session tuning.</strong></p>
<p align="center"><a href="https://github.com/Ivan-VHS/OPlague/actions/workflows/completeness-check.yml"><img alt="Quality checks" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/completeness-check.yml?branch=main&style=flat-square&label=Quality"></a> <a href="https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml"><img alt="Windows build" src="https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&style=flat-square&label=Windows%20build"></a> <a href="LICENSE"><img alt="Apache-2.0" src="https://img.shields.io/github/license/Ivan-VHS/OPlague?style=flat-square"></a></p>

[Quick start](#quick-start) · [Revival](#documentation-revival) · [Visuals](#visual-overview) · [Architecture](#architecture) · [Docs](docs/README.md)

> **Safety boundary:** driver and package inspection is read-only: payloads are not extracted, executed, installed or loaded. Exact hardware-ID matches are candidates, not compatibility certification. A separate gaming session may temporarily select a built-in Windows power plan after saving a snapshot; restoration is guarded against overwriting later external changes.

## Quick start

**Requirements:** Python 3 and a Windows environment for live Plug and Play inventory. Saved reports and package metadata can be reviewed offline. Tkinter is required for the desktop UI.

~~~sh
git clone https://github.com/Ivan-VHS/OPlague.git
cd OPlague
python oplague_app.py
~~~

Run tests and visual-contract checks:

~~~sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python -m unittest discover -s tests -v
~~~

Useful CLI checks:

~~~sh
python -m oplague --verify
python -m oplague --catalog
python -m oplague --search "ballistic"
python -m oplague --profile 5
python -m oplague --rank reach
~~~

## Documentation revival

| Before | Revival documentation |
|---|---|
| Static overview without clear asset roles | Theme-aware hero and labelled real capture/architecture visual |
| Driver analysis and gaming controls read as one permission boundary | Read-only inspection separated from the explicit reversible power-plan session |
| Capability claims summarized without consistent maturity labels | Feature matrix with source, input and safety boundaries |
| Quick start mixed with operator detail | Verified launch, test and CLI commands near the top |
| Deep links scattered through the README | Topic hubs, documentation index and publication standard |

This is a documentation refresh, **not a software version or release announcement**. The source, tests, schemas and current CI workflows define actual behavior.

## Implemented scope

| Area | Current behavior | Boundary |
|---|---|---|
| Device inventory | Windows Plug and Play identity/status collection | Live inventory is Windows-only |
| INF / ZIP inspection | Bounded metadata parsing, path checks, hashes and architecture hints | No extraction or execution |
| Authenticode | Selected-file signature/signer/timestamp metadata | Not an install/load or safety verdict |
| Compatibility matching | Exact normalized hardware-ID candidate links | Candidate evidence only |
| UDRV v1 | Manifest, file-size and SHA-256 validation | No install or driver loading |
| Reports and snapshots | Versioned JSON, batch summaries and offline comparison | Local data; hashes identify bytes, not publisher trust |
| Gaming session | Snapshot, temporary built-in power-plan selection and guarded restore | Not GPU overclocking, driver mutation or firmware control |
| Metrics | Weighted distance and profile comparison | Advisory; not a certification score |

## Visual overview

<table><tr><td width="50%"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="Captured OPlague Windows device and driver workbench" width="100%"></a><p><sub><strong>Real application capture</strong> — Windows desktop, 1920×1080.</sub></p></td><td width="50%"><img src="assets/readme/workflow.svg" alt="OPlague local input, bounded parsing, evidence, candidate analysis and report workflow" width="100%"><p><sub><strong>Architecture illustration</strong> — evidence pipeline, not a UI screenshot.</sub></p></td></tr></table>

## Architecture

~~~mermaid
flowchart LR
  A[Windows PnP / local package] --> B[Bounded metadata parser]
  B --> C[Validated evidence record]
  C --> D[Candidate matching and review]
  D --> E[Dry-run report]
  E --> F[Explicit JSON export]
  G[Saved device snapshot] --> D
  H[Gaming session] --> I[Power-plan snapshot]
  I --> J[Temporary built-in plan]
  J --> K[Guarded restore]
~~~

Inspection and gaming-session flows are separate. The driver pipeline does not install, load, extract or execute package content.

## Configuration and access

There is no hosted service, API token, account, root .env or test login. The live device inventory path uses local Windows PowerShell/CIM. If that provider is unavailable, the application reports the inventory error; it does not invent or substitute a device list.

The desktop controls expose the documented Duck palette and motion preferences. System power-plan changes are limited to the separate, explicit gaming-session workflow.

## Repository map

| Path | Responsibility |
|---|---|
| oplague_app.py | Public desktop entry point |
| oplage_app.py | Desktop implementation and inspection logic |
| tools/ | CLI, report, metric and UDRV utilities |
| tests/ | Unit and regression tests with synthetic fixtures |
| schemas/ | Versioned reports and package contracts |
| docs/ | Architecture, safety, integration and operator references |
| assets/readme/ | Theme-aware hero and workflow illustration |
| assets/screenshots/ | Captured Windows application images |
| .github/workflows/ | CI, Windows packaging and quality gates |

## Verification and status

~~~sh
python -m unittest discover -s tests -v
python -m oplague --verify
python tools/udrv_inspector.py path/to/package.udrv --json
git diff --check
~~~

Current capabilities and limits are listed in [Features](docs/FEATURES.md), [Architecture](docs/ARCHITECTURE.md), the [device and driver hub](docs/clusters/device-driver-inspection.md) and the [information architecture map](docs/INFORMATION_ARCHITECTURE.md). Never treat a heuristic or match as a malware verdict or device certification.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing parsers, system integrations or safety controls. Publishing rules are in [README Visual Standard](docs/README_VISUAL_STANDARD.md); security policy is in [SECURITY.md](SECURITY.md).

## License

[Apache-2.0](LICENSE).
