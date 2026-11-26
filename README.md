# OPlague — device and driver evidence workbench

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

> A local, read-only workbench for Windows device inventory, bounded driver-package inspection, hardware-ID candidate analysis and source-attributed telemetry.

**Specification**

| Field | Current record |
|---|---|
| Repository | [Ivan-VHS/OPlague](https://github.com/Ivan-VHS/OPlague) |
| Project status | Development; Windows-first inspection workbench |
| Product version | No single version declared in the project contract |
| Main stack | Python 3.10+; JSON Schema; bounded native integration components |
| Runtime scope | Windows, Linux and macOS for supported offline workflows |
| Live device inventory | Windows only |
| Desktop platform | Windows |
| License | [Apache-2.0](LICENSE) |
| Code of Conduct | Not published (no root `CODE_OF_CONDUCT.md`) |
| Last documentation review | 2026-11-26 |

<p align="center"><img src="assets/oplague-workbench-preview.svg" alt="OPlague workbench architecture preview" width="100%"></p>
<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="OPlague workbench screenshot" width="100%"></a></p>

## Contents
- [Purpose and scope](#purpose-and-scope)
- [Architecture and data flow](#architecture-and-data-flow)
- [Requirements and quick start](#requirements-and-quick-start)
- [Interfaces and evidence](#interfaces-and-evidence)
- [Security and limitations](#security-and-limitations)
- [Release and documentation](#release-and-documentation)

## Purpose and scope

OPlague is a local evidence workbench for read-only Windows Plug-and-Play inventory, bounded INF/ZIP/UDRV metadata inspection, exact normalized hardware-ID candidate matching, local metrics and GPU telemetry export. Offline file and report analysis is available outside Windows where the relevant workflow does not require live Plug-and-Play data.

The product does not install, remove, enable, unload or modify drivers. It does not execute package payloads, certify device compatibility or claim that a metadata match is a safety verdict.

## Architecture and data flow

~~~mermaid
flowchart TB
  U["User-selected device or file"] --> I["Bounded inspector"]
  I --> N["Normalize IDs, paths, sizes and hashes"]
  N --> E["Evidence record and candidate graph"]
  E --> R["Local report / versioned JSON snapshot"]
  P["Windows PnP read-only query"] --> E
  G["NVIDIA telemetry source (read-only)"] --> T["GPU telemetry snapshot"]
  T --> R
  R -.-> X["No install, load, extraction or certification"]
~~~

The core flow is local input → bounded parser or fixed read-only system query → normalized evidence → report. Untrusted archive metadata is constrained before analysis. Imported driver payloads are not extracted or executed.

## Requirements and quick start

Requirements: Python 3.10+ for the current tools; Windows for live Plug-and-Play inventory. Offline file/report inspection can run on supported Python environments.

~~~sh
python -m venv .venv
python oplague_app.py
~~~

Run the project tests and inspect a user-selected local package:

~~~sh
python -m unittest discover -s tests -v
python tools/udrv_inspector.py path/to/package.udrv --json
~~~

The UDRV command validates manifest, declared file inventory, size, hash and path/resource constraints. It does not install, load, extract or execute the payload.

## Interfaces and evidence

| Interface | Contract | Boundary |
|---|---|---|
| Device snapshot | `oplage.device-snapshot.v1` | Versioned JSON; pseudonymous device fingerprint |
| GPU telemetry | `oplage.gpu-telemetry.v1` | Read-only source metadata; unavailable values remain unknown |
| UDRV | UDRV v1 manifest | Bounded validation only |
| Batch report | `oplage.inspection-bundle.v1` | Ordered local summary and deterministic digest |
| Pytyliki | `pytyliki.c-abi.v1` | Optional native call through an explicitly trusted library |
| Reaper | Versioned JSON comparison | Offline comparison; no device mutation |

Exact normalized hardware-ID matches create candidate edges only. They do not rank, certify, install or declare a driver safe. NVIDIA telemetry is source-attributed; the presence of a GPU or provider is not assumed.

## Security and limitations

> **Read-only boundary:** no driver package or payload is installed, loaded, extracted or executed by the documented inspection path.

Treat INF, ZIP, UDRV and imported report files as untrusted. Parsers enforce entry, path, size and compression limits; SHA-256 identifies content changes but is not a digital signature or publisher authentication. Authenticode metadata is collected only for selected supported files and does not establish device compatibility or operational safety.

Live Plug-and-Play collection is Windows-only. Offline report and package analysis is separate from live inventory. The Rust 2021 diagnostics ABI consumer is a bounded integration component, not a full Rust/Slint migration of the workbench. The repository's project contract does not declare a single product version.

The Beelzebul repository scanner is a local/static source assurance tool; it is not endpoint malware protection, process-memory inspection or quarantine. See [SECURITY.md](SECURITY.md) for the scanner's exact behavior and disclosure process.

## Release and documentation

Start with [Documentation Index](docs/README.md) and [Information Architecture](docs/INFORMATION_ARCHITECTURE.md).

- [Feature matrix](docs/FEATURES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [UDRV format v1](docs/UDRV_FORMAT_V1.md)
- [Device compatibility graph](docs/DEVICE_COMPATIBILITY_GRAPH.md)
- [GPU telemetry bridge v1](docs/GPU_TELEMETRY_BRIDGE_V1.md)
- [Federated integration](docs/FEDERATED_INTEGRATION.md)
- [Windows release distribution](docs/RELEASE.md)
- [Security policy](SECURITY.md)

The Windows release workflow creates a **draft** GitHub Release for maintainer review. Its SHA-256 sidecar detects byte changes relative to the digest; it is not a digital signature and does not authenticate the publisher. Release publication is a separate maintainer action.

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing parsers, schemas, candidate matching or telemetry. The repository is licensed under [Apache-2.0](LICENSE); preserve upstream notices and attribution.

## Release history

No single product version is declared in the current project contract. Do not infer a release version from a draft workflow or package metadata. Public releases and support states must be tied to actual tags and published release artifacts. Breaking changes to JSON schemas or the UDRV manifest require an explicit version and migration note.