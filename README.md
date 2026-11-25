# OPlague — Device, Driver and Gaming Workbench

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

[![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) [![Docs checks](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/docs.yml?branch=main&label=Docs%20checks)](https://github.com/Ivan-VHS/OPlague/actions/workflows/docs.yml) [![Apache-2.0](https://img.shields.io/github/license/Ivan-VHS/OPlague)](LICENSE)

<p align="center"><img src="assets/readme/dashboard.svg" alt="OPlague project overview" width="100%"></p>
<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="OPlague Windows workbench" width="100%"></a></p>

OPlague is a local desktop workbench for device and driver inspection, compatibility evidence, package analysis and gaming-performance diagnostics.

**Default boundary:** inspection is read-only. Device discovery and user-selected file analysis do not install, enable, unload or modify drivers. Compatibility candidates and telemetry are evidence for review, not certification.

## Capabilities

- Windows Plug-and-Play inventory and bounded INF/ZIP package inspection.
- PE and Authenticode inspection, normalized hardware IDs, hashes and SPDX inventory.
- Device compatibility evidence, UDRV package validation and structured reports.
- Local gaming telemetry, frametime analysis and reversible per-user performance sessions.
- Versioned, read-only NVIDIA GPU telemetry export for DAK/Reaper; unsupported readings remain unknown.

See [Features](docs/FEATURES.md), [Architecture](docs/ARCHITECTURE.md), [Authenticode](docs/AUTHENTICODE.md), [Driver target architecture](docs/DRIVER_TARGET_ARCHITECTURE.md), [UDRV format](docs/UDRV_FORMAT_V1.md) and [Gaming workbench](docs/GAMING_PERFORMANCE_WORKBENCH.md) and [GPU telemetry bridge v1](docs/GPU_TELEMETRY_BRIDGE_V1.md).

## Run and test

Requirements: Python 3.10–3.12 for the current desktop tools and validation scripts.

```sh
python oplague_app.py
python -m unittest discover -s tests -v
python -m oplague --verify
python -m oplague --catalog
```

Inspect a package:

```sh
python tools/udrv_inspector.py path/to/package.udrv --json
```

Build a standalone Windows executable with PyInstaller:

```sh
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name OPlague oplague_app.py
```

## Integration and evidence

- [Documentation index](docs/README.md) · [Reaper runtime integration](docs/REAPER_RUNTIME_INTEGRATION.md)
- [DAK and Mora integration](https://github.com/Ivan-VHS/DAK/blob/main/docs/GAMING_PERFORMANCE_INTEGRATION.md)
- [Shared ecosystem standards](https://github.com/Ivan-VHS/DAK/blob/main/docs/SHARED_STANDARDS.md)

Source, schemas and tests define current behavior. The workbench does not flash firmware, install drivers or automatically certify hardware compatibility.

[Contributing](CONTRIBUTING.md) · [Security policy](SECURITY.md) · [Apache-2.0](LICENSE)
