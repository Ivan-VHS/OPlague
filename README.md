<p align="center">[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)</p>

<h1 align="center"><strong>🛡️ OPlague — Device, Driver & Gaming Workbench</strong></h1>

[![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![Docs checks](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/docs.yml?branch=main&label=Docs%20checks)](https://github.com/Ivan-VHS/OPlague/actions/workflows/docs.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague)](LICENSE)

> **Inspect devices and packages. Preserve the machine. Publish evidence, never driver actions.**

**State:** Development · Windows-first inspection tools · **Version:** Version not declared in project contract · **License:** [Apache-2.0](LICENSE) · **README standard:** Psychoporter 666 v1.0 · **Last reviewed:** 2026-11-25 · UTC · **Source:** [Ivan-VHS/OPlague](https://github.com/Ivan-VHS/OPlague)

<p align="center"><img src="assets/oplague-workbench-preview.svg" alt="OPlague — Device, Driver & Gaming Workbench — project overview" width="100%"></p>
<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="OPlague — Device, Driver & Gaming Workbench — application screenshot" width="100%"></a></p>

## Quick navigation

[🚀 Demo: workbench screenshot](assets/screenshots/oplague-workbench.png) · [Documentation](docs/README.md) · [Source repository](https://github.com/Ivan-VHS/OPlague) · [Issues](https://github.com/Ivan-VHS/OPlague/issues)

## Mission & scope

A local workbench for read-only device discovery, bounded INF/ZIP/UDRV package inspection, compatibility evidence and gaming telemetry. Live Windows Plug-and-Play discovery is Windows-only; saved-file and report analysis is portable. The application does not install, enable, unload or modify drivers.

## Capabilities

- Windows Plug-and-Play inventory with read-only queries.
- Bounded INF/ZIP inspection, PE and Authenticode metadata, SHA-256 and SPDX inventory.
- UDRV v1 manifest, file-size, hash and path validation; payloads are not installed or executed.
- Exact normalized hardware-ID candidate edges; candidates are not compatibility certification.
- Local gaming/frametime analysis and NVIDIA nvidia-smi read-only telemetry export when available.
- Versioned JSON device snapshots and optional trusted Pytyliki C ABI cross-checks.

## Architecture & data flow

~~~mermaid
flowchart TB
  U["User-selected device or file"] --> I["Bounded inspector"]
  I --> N["Normalize IDs / metadata / hashes"]
  N --> E["Evidence and candidate graph"]
  E --> R["Local report / JSON snapshot"]
  G["nvidia-smi — read only"] --> T["GPU telemetry snapshot"]
  T --> R
  R -.-> X["No driver install, load or certification"]
~~~

Source code, schemas, build files, tests and CI are the evidence for implemented behavior. Roadmap entries and catalogue records describe plans or inventories, not shipped functionality.

## Requirements

Python 3.10–3.12 for the current desktop and validation tools. Windows is required for live Plug-and-Play inventory; offline file inspection and report analysis do not require live device access. Tk-based desktop UI availability depends on the local Python installation.

## Build

~~~sh
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python oplague_app.py
~~~


## First checks

~~~sh
python -m unittest discover -s tests -v
python tools/udrv_inspector.py path/to/package.udrv --json
~~~

Run the desktop entry point after reviewing the tests and inspector output. The package inspector does not extract or execute payloads.

## Run

The current desktop entry point is oplague_app.py. The package inspector accepts a user-selected local file; it does not execute package payloads.

## Interfaces

| Surface | Contract / entry point | Boundary |
|---|---|---|
| Device snapshot | `oplage.device-snapshot.v1` | Versioned JSON; pseudonymous device fingerprint. |
| GPU telemetry | `oplage.gpu-telemetry.v1` | Read-only NVIDIA sensor export; unavailable values remain unknown. |
| UDRV inspector | `tools/udrv_inspector.py` | Manifest, size, hash and path checks; no install/load. |
| Native metrics | `Optional pytyliki.c-abi.v1` | Only through an explicitly selected trusted library. |

REST/GraphQL, WebSocket, OAuth, cloud deployment and cookie mechanisms are not advertised without a versioned implementation and tests.

## Security & trust boundaries

Imported files and packages are untrusted input. Archive entry counts, paths, sizes and compression are bounded; payloads are not extracted or executed. Hardware-ID matches are candidate evidence, not signing, safety or operating-system support verdicts. Device discovery is read-only; no driver, firmware or device state is changed.

Security reporting: [SECURITY.md](SECURITY.md). Do not publish secrets, device identifiers or private logs in public issues.

## Verification

~~~sh
python -m unittest discover -s tests -v
~~~

The checked-in CTest/unittest targets and workflows define the test scope. No coverage percentage, fuzz result or load-test report is claimed without a published artifact.

## Performance evidence

Gaming and GPU metrics are local observations, not universal benchmarks. NVIDIA telemetry is read-only and source-attributed; missing measurements remain unknown. No fixed latency or memory footprint is claimed.

## Compatibility

Live Windows Plug-and-Play inventory is Windows-only. Offline package, hash, schema and report inspection are portable subject to the installed Python environment and optional platform-specific evidence sources.

## Documentation & ecosystem

- [Features and limits](docs/FEATURES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Authenticode inspection](docs/AUTHENTICODE.md)
- [UDRV v1 format](docs/UDRV_FORMAT_V1.md)
- [GPU telemetry bridge](docs/GPU_TELEMETRY_BRIDGE_V1.md)
- [Gaming workbench](docs/GAMING_PERFORMANCE_WORKBENCH.md)
- [Documentation index](docs/README.md)

Feature boundaries, the UDRV schema, Authenticode inspection and the read-only GPU telemetry bridge are the primary technical references.

Cross-project integrations use documented versioned interfaces and explicit adapters. An optional adapter does not grant another project runtime or hardware privileges.

## Contributing

Read CONTRIBUTING.md before changing code or contracts. Keep changes reviewable, add deterministic tests and use Conventional Commits where required by the repository guide.

## License & legal

Distributed under [Apache-2.0](LICENSE). The software is provided “AS IS” under the license terms. Third-party project names and trademarks remain with their respective owners.

This repository documents local software interfaces. Hosted-service terms, cookie consent, OAuth and CORS are not applicable to the runtime surfaces described above unless a separate hosted component is introduced and documented.

---

<p align="center"><sub>Psychoporter 666 README Standard v1.0 · Ivan-VHS · 2026-11-25 · UTC</sub></p>