<p align="center"><picture><source media="(prefers-color-scheme: dark)" srcset="assets/readme/hero-banner-dark.svg"><source media="(prefers-color-scheme: light)" srcset="assets/readme/hero-banner-light.svg"><img src="assets/readme/hero-banner-light.svg" alt="OPlague device, driver and gaming workbench" width="880"></picture></p>

# OPlague — Device, Driver and Gaming Performance Workbench

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![Quality](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/completeness-check.yml?branch=main&style=flat-square&label=Quality)](https://github.com/Ivan-VHS/OPlague/actions/workflows/completeness-check.yml) [![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&style=flat-square&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague?style=flat-square)](LICENSE)

> A local Windows-first workbench for bounded device and driver evidence, source-attributed telemetry, and an explicit reversible gaming-session power-plan workflow.

**Project record:** Development · no unified product version declared · Python 3.10+ · JSON Schema · partial Rust 2021 diagnostics consumer · Windows desktop and live inventory · Apache-2.0 · **Documentation reviewed:** 2026-11-27 UTC

## Purpose and scope

OPlague brings together two deliberately separate workflows:

1. **Device and package evidence.** Read-only Windows Plug-and-Play inventory, bounded INF/ZIP/UDRV inspection, normalized hardware-ID candidate matching, local reports and source-attributed GPU telemetry.
2. **Gaming-session planning.** An explicit Windows workflow that saves a local snapshot and may temporarily select a built-in Windows power plan. It can restore the previous plan only when the active plan is still the one OPlague applied.

Driver and package inspection does not install, remove, enable, unload, extract or execute drivers or payloads. The gaming-session workflow is a separate, user-confirmed system change: it does not modify drivers, registry settings, firmware, clocks, voltages, services or network configuration.

## Capabilities

- **Live device inventory:** current Windows Plug-and-Play records collected through a fixed read-only query. Live inventory is Windows-only.
- **Bounded package inspection:** INF metadata and ZIP structure checks with path, entry, size and compression limits.
- **UDRV v1 integrity inspection:** validates the manifest, declared payload inventory, file sizes, SHA-256 digests and resource/path constraints without extracting or executing payloads.
- **Evidence reports:** deterministic batch summaries, content digests and versioned JSON snapshots with pseudonymous device fingerprints.
- **Candidate compatibility graph:** exact normalized hardware-ID matches create candidate edges only. They do not rank, certify or prove a driver safe or compatible.
- **Metrics and telemetry:** normalized profile comparisons and optional NVIDIA sensor readings from `nvidia-smi`. Missing sensor values remain unknown; telemetry is read-only.
- **Gaming session:** after explicit confirmation, saves the current device/driver and power-plan snapshot and can temporarily select the built-in High Performance plan. Restoration is guarded: if the active plan changed outside the session, OPlague leaves that newer selection untouched.
- **Interop:** versioned device snapshots and Reaper reports; optional Pytyliki C ABI calls through a caller-selected trusted library.
- **Rust diagnostics bridge:** a bounded Rust 2021 consumer of the Pytyliki diagnostics ABI is partial; this is not a full Rust/Slint migration.

Offline package and report analysis is available on supported Python environments outside Windows when the workflow does not require live Plug-and-Play data.

## Quick start

Requirements: Python 3.10+; Windows for the desktop application, live Plug-and-Play inventory and power-plan control. NVIDIA telemetry additionally requires a supported local `nvidia-smi` provider.

Launch the Windows workbench:

~~~sh
python oplague_app.py
~~~

Run the tests and inspect a user-selected UDRV package:

~~~sh
python -m unittest discover -s tests -v
python tools/udrv_inspector.py path/to/package.udrv --json
~~~

The UDRV inspector validates metadata and file digests within fixed limits. It never extracts, installs, loads or executes package content.

## Data contracts

| Interface | Contract | Boundary |
|---|---|---|
| Device snapshot | `oplage.device-snapshot.v1` | Versioned JSON; pseudonymous fingerprint |
| GPU telemetry | `oplage.gpu-telemetry.v1` | Read-only provider metadata; unknown values stay unknown |
| Batch evidence | `oplage.inspection-bundle.v1` | Ordered report and deterministic digest |
| Driver package | UDRV v1 | Bounded manifest/integrity validation only |
| Reaper comparison | `reaper.oplage-comparison.v1` | Offline report validation; no device mutation |
| Pytyliki metrics | `pytyliki.c-abi.v1` | Optional native call through an explicitly trusted library |
| Gaming session | `oplague.gaming.v1` | Local snapshot and guarded Windows power-plan transition |

SHA-256 detects byte changes relative to a recorded digest; it is not a digital signature, publisher authentication or proof of safety. Authenticode metadata is evidence about supported files, not device-compatibility certification.

## Security and limitations

Treat INF, ZIP, UDRV, telemetry exports and imported reports as untrusted input. Parsers enforce resource limits; package payloads are not extracted or executed. Hardware-ID matches are candidate relationships, not security verdicts.

The gaming power-plan transition is explicit and separate from inspection. It is currently Windows-only, saves a pre-session snapshot and avoids overwriting a later external plan selection. No performance improvement is guaranteed by selecting a power plan or comparing frametime data.

The Beelzebul repository scanner is a local/static source-assurance tool. It is not endpoint malware protection, process-memory inspection or quarantine.

## Documentation

- [Documentation index](docs/README.md) · [Information architecture](docs/INFORMATION_ARCHITECTURE.md)
- [Feature matrix](docs/FEATURES.md) · [Architecture](docs/ARCHITECTURE.md)
- [UDRV format v1](docs/UDRV_FORMAT_V1.md) · [Device compatibility graph](docs/DEVICE_COMPATIBILITY_GRAPH.md)
- [Telemetry capability inventory](docs/FEATURES.md) · [Gaming and telemetry features](docs/clusters/device-driver-inspection.md)
- [Federated integration](docs/FEDERATED_INTEGRATION.md) · [Windows desktop workflow](.github/workflows/desktop-build.yml)
- [Reaper runtime integration](docs/REAPER_RUNTIME_INTEGRATION.md) · [Security policy](SECURITY.md)
- [Visual publishing standard](docs/README_VISUAL_STANDARD.md)

The Windows release workflow creates a draft GitHub Release for maintainer review. Publishing is a separate maintainer action; the SHA-256 sidecar is not a digital signature.

## Contributing and license

Read [CONTRIBUTING.md](CONTRIBUTING.md) before modifying parsers, schemas, telemetry or system integration. Preserve bounded input handling, explicit permissions and evidence provenance. Do not submit private driver payloads or identifying hardware exports.

Licensed under [Apache-2.0](LICENSE). Preserve third-party notices and attribution.
