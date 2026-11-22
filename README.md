# OPlague — read-only device and driver workbench

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

<p align="center"><img src="assets/readme/dashboard.svg" alt="OPlague project overview" width="100%"></p>

[Source](https://github.com/Ivan-VHS/OPlague) · [Windows desktop workflow](.github/workflows/desktop-build.yml) · [Documentation index](docs/README.md) · [Apache-2.0](LICENSE)

## Live Windows workbench capture

<p align="center"><a href="assets/screenshots/oplague-workbench.png"><img src="assets/screenshots/oplague-workbench.png" alt="Real Windows desktop capture of OPlague" width="100%"></a></p>
<p align="center"><sub>1920×1080 · Click the image to open the original PNG.</sub></p>

Genuine screenshot of the running OPlague desktop application, captured by the Windows packaging workflow. The banner and process diagram are original SVG illustrations; the UI image is not generated or composited.

### Architecture at a glance

<p align="center"><img src="assets/readme/workflow.svg" alt="OPlague implemented data flow" width="100%"></p>

Implemented path: Windows PnP and user-selected files → bounded INF/ZIP inspection → normalized IDs and hashes → candidate evidence report.


[![Windows build](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/desktop-build.yml?branch=main&label=Windows%20build)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)  [![Docs checks](https://img.shields.io/github/actions/workflow/status/Ivan-VHS/OPlague/docs.yml?branch=main&label=Docs%20checks)](https://github.com/Ivan-VHS/OPlague/actions/workflows/docs.yml)  [![License](https://img.shields.io/github/license/Ivan-VHS/OPlague)](LICENSE)


> **Scope:** OPlague is a local read-only desktop workbench for Windows Plug and Play inventory, INF/ZIP driver-package metadata and evidence-based comparison. It does **not** install, load, extract or modify driver payloads. This repository does not publish a hosted web demo, remote API or production device-management service. Documentation was checked against `main` on **2026-11-22**.

## Purpose and boundaries

OPlague helps an operator inspect the current machine's device records, read driver-package metadata and compare normalized hardware identifiers. It is intended for Windows support engineers, hardware reviewers, QA and developers investigating package contents or compatibility evidence.

The result is an evidence record and candidate comparison, not a final safety or compatibility verdict. An exact hardware-ID match does not prove publisher trust, OS compatibility, device suitability or safe installation. Driver deployment remains outside the product.

### What the workbench actually does

| Area | Implemented behavior | Boundary |
|---|---|---|
| Device inventory | reads Windows Plug and Play identity, status, manufacturer and PNPDeviceID | live collection is Windows-only and read-only |
| INF inspection | reads selected metadata, hardware-ID declarations and target architecture | does not run INF directives |
| ZIP inspection | checks paths, sizes, compression ratios, hashes and INF metadata | does not extract or execute package payloads |
| Compatibility graph | forms candidate relationships from exact normalized hardware IDs | candidate links only; manual review remains required |
| Metric Lab | compares user-supplied normalized profiles with weighted distance/variance | advisory analysis, not a device verdict |
| UDRV v1 | validates manifest, sizes and SHA-256 evidence | integrity check, not publisher authentication |
| Authenticode | checks signatures on selected CAT/SYS/DLL/EXE/EFI files through Windows | read-only; trust status does not prove compatibility or driver safety |
| Reports | produces structured evidence, totals and fingerprints | no system write and no driver installation |

The application has five principal tabs: **Devices**, **Package Inspection**, **Metric Lab**, **Compatibility Review** and **Signature Audit**. The theme can cycle through system/light/dark modes; motion preferences include Reduce Motion and Eco Visuals. The disabled Sync-to-Transport option is intentionally unavailable because OPlague has no audio transport or master BPM.

The screenshot is a captured desktop application, not a browser preview. Signature Audit uses the local Windows trust provider and does not change the driver store.


## Quick Start

### Requirements

- Python **3.10 or newer**.
- Tkinter for the desktop UI.
- Windows and `powershell.exe` for live Plug and Play inventory. The inventory uses a fixed local PowerShell/CIM query.
- Git.

The application imports its own repository modules and Python standard-library facilities; a third-party runtime package install is not required for the source launch. PyInstaller is only needed when packaging a standalone executable.

On Linux and macOS, saved data can be inspected, but live Windows PnP inventory is unavailable.

### Run the desktop workbench

From the repository root:

```sh
python oplague_app.py
```

`oplague_app.py` is the correctly spelled entry point; it delegates to the existing `oplage_app.py` implementation module.

### Run tests and CLI checks

```sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python -m unittest discover -s tests -v
```

The project CLI examples:

```sh
python -m oplague --verify
python -m oplague --catalog
python -m oplague --search "ballistic"
python -m oplague --profile 5
python -m oplague --rank reach
python tools/udrv_inspector.py path/to/package.udrv --json
python tools/clinical_systems.py --catalog --pretty
python tools/hardware_id_lint.py "PCI\VEN_8086&DEV_15F3&SUBSYS_00008086&REV_03" --json
```

The optional native Reaper C17 calculation requires an explicit trusted library path:

```sh
python -m oplague --rank-total-native --reaper-library /absolute/path/to/libreaper_ffi.so
```

This is local execution. OPlague does not start an HTTP listener, web UI, API endpoint or localhost preview.

### Build a Windows executable

The desktop workflow uses Python 3.12 and PyInstaller. To package locally:

```sh
python -m pip install --upgrade pyinstaller
python -m PyInstaller --noconfirm --clean --onefile --windowed --name OPlague oplague_app.py
```

The standalone executable is written under `dist/OPlague.exe`. First packaging may take longer while PyInstaller collects the application; no fixed build duration is promised.

## Data, limits and verification scenarios

OPlague has no shared database, login, demo account, remote mock API or hosted fixture service. The data sources are distinct:

- **Device inventory:** actual local Windows Plug and Play records read through `Get-CimInstance`.
- **Package inspection:** a file explicitly selected by the operator.
- **Metric Lab:** JSON entered by the operator. The initial reference/candidate JSON values in the UI are illustrative sample inputs normalized to `[0, 1]`, not live measurements.
- **Automated tests:** local test fixtures and synthetic inputs, not installed drivers or a real driver catalogue.

Try these scenarios:

1. **Refresh devices on Windows:** click **Refresh device list**. The app reads local PnP information and displays name, status, manufacturer and hardware ID.
2. **Inspect a package:** choose an `.inf` or `.zip` file. Review metadata, SHA-256, architecture hints and package bounds; no payload is installed or executed.
3. **Batch inspection:** select multiple local packages and compare their metadata reports.
4. **Metric comparison:** edit the reference/candidate JSON objects. Values must be normalized to `[0, 1]`; compare the weighted output and inspect the supplied weights.
5. **Compatibility plan:** form candidate links from the current device list and inspected INF hardware IDs; review every candidate manually.
6. **UDRV validation:** run `tools/udrv_inspector.py` on a local package and inspect the JSON validation report.
7. **Regression suite:** run `python -m unittest discover -s tests -v`.

### Input and archive limits

The desktop inspector enforces these bounds:

| Input | Limit |
|---|---:|
| INF / ZIP package file | 512 MiB |
| ZIP entries | 10,000 |
| Total expanded ZIP content | 2 GiB |
| Individual INF content | 2 MiB |
| Compression ratio | 200:1 |

The UDRV v1 inspector has its own contract: manifest up to 4 MiB, up to 10,000 entries, a file up to 512 MiB and total payload up to 2 GiB. The inspector reads and hashes bytes in bounded chunks; it does not extract or execute the payload.

There is no built-in latency simulator, HTTP 500 switch, mock network service or browser upload. Errors such as an invalid ZIP, unsafe archive path, oversized INF or unavailable PowerShell inventory are reported locally.

The current device list and inspection results live in the desktop process. Closing the app clears that working session; it does not change the source packages or Windows drivers. Theme and motion preferences are handled by the native preferences layer. There is no browser localStorage, sessionStorage, IndexedDB or cookie state.

## Configuration and access

There is no root `.env.example`, Docker Compose web stack, API key, OAuth account, test login, CORS policy, HTTP proxy or local HTTPS certificate setup. No secrets are needed for normal local inspection. The current app does not document a runtime ENV variable contract; do not invent one.

Relevant in-app controls are the theme cycle (system/light/dark) and motion settings (Reduce Motion, Eco Visuals and Expressive Motion). Sync to Transport/BPM is disabled by design and must not be presented as a working option.

The live PnP query requires Windows PowerShell and the local CIM provider. If that command is blocked or fails, package-file inspection and saved-data review remain separate workflows; the app shows the inventory error instead of substituting a fake device list.

## Architecture and repository map

The data path is: **local input → bounded parser → evidence record → dry-run comparison/report → optional explicit export**.

| Path | Contents |
|---|---|
| `oplague_app.py` | public, correctly spelled desktop entry point |
| `oplage_app.py` | desktop implementation, package inspection and PnP query |
| `tools/` | CLI utilities, report composition, metrics and UDRV inspection |
| `tests/` | unit and regression tests with local fixtures |
| `docs/` | architecture, safety boundaries, schemas and operator guidance |
| `schemas/` | versioned report and package contracts |
| `assets/screenshots/` | captured Windows desktop image |
| `security/` | machine-readable Beelzebul repository policy |
| `.github/workflows/` | Windows packaging and release automation |

The app is a Python/Tkinter desktop program. The Windows inventory path invokes local PowerShell; the package inspector reads local INF/ZIP metadata. There is no frontend/backend deployment, mock server, web port, browser storage, CORS configuration or public live preview. Browser compatibility and responsive viewport rules are therefore not applicable.

## Packaging, CI and release operation

The [Windows desktop workflow](.github/workflows/desktop-build.yml):

1. uses Python 3.12 on Windows;
2. compiles the Python sources and runs the unit tests;
3. validates the visual canon;
4. packages `OPlague.exe` with PyInstaller;
5. captures the running desktop app and uploads the screenshot artifact;
6. creates `OPlague-windows-x64.zip` with the executable, README and license.

The screenshot artifact is retained for 30 days. A Git tag matching `v*` triggers GitHub Release publication. A workflow artifact is a downloadable build, not a hosted web demo.

For rollback of a distributed build, select the previous known-good tagged release/archive. There is no server deployment to roll back. Workflow logs and test output are available in GitHub Actions.

## Troubleshooting

| Symptom | Check |
|---|---|
| The app does not start | use Python 3.10+ with Tkinter and launch from the repository root |
| Device inventory fails | verify Windows, `powershell.exe` and local CIM access; inventory is not implemented on Linux/macOS |
| ZIP is rejected | check archive validity, entry count, expanded size, compression ratio and paths |
| INF is rejected | verify the file is within the 2 MiB INF bound and is validly encoded |
| Package exceeds the limit | the desktop inspector caps package files at 512 MiB |
| Metric comparison fails | enter valid JSON objects and normalize metric values to `[0, 1]` |
| Native rank total fails | check that the explicitly supplied Reaper library exists and is trusted |

The desktop status and dialog messages describe the immediate failure. For CI failures, inspect the corresponding GitHub Actions logs.

## Known limitations, contribution and license

OPlague is deliberately non-destructive. It does not install, load, extract or modify drivers; matching is candidate evidence rather than certification. Live hardware enumeration is Windows-only. The metric profiles are advisory. Hashes establish byte identity, not publisher authenticity or ownership. The UDRV inspector does not execute payloads.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the repository's contribution workflow and validation requirements. Report a problem or propose a change through [GitHub Issues](https://github.com/Ivan-VHS/OPlague/issues) or a Pull Request. Include the OS, Python version, safe sample file type, exact command and expected/actual result. Do not attach private driver packages or sensitive device identifiers without removing identifying data.

License: [Apache-2.0](LICENSE).

## Mapping to the 66 README rules

The web-stand checklist is mapped to the actual desktop workbench rather than copied as a fictional web deployment:

| Rules | README coverage |
|---|---|
| 1–11 · purpose and scope | identifies the read-only workbench, users, actual data sources, limitations and absence of a hosted stand |
| 12–22 · quick start | exact Python/Tkinter requirements, GUI entry point, test commands and executable packaging |
| 23–33 · config and access | states there is no `.env`, test login, API secret, CORS or HTTPS setup; documents actual local PowerShell dependency |
| 34–44 · data and scenarios | separates live local PnP data, operator-supplied packages, sample metric JSON and test fixtures; states bounds and state lifetime |
| 45–55 · architecture and build | maps real source, tools, tests, schemas, docs and Windows package workflow |
| 56–66 · operations and support | documents artifact/release publication, rollback, logs, troubleshooting, limitations, contribution channel and license |

**No public OPlague web-demo URL exists.** The Windows screenshot and release archive are not an online device-management service.

## Unified report envelope

Wrap a JSON evidence report using the shared ivan-vhs.report.v1 format:

    python tools/report_envelope.py --tool oplague --version VERSION --input-file driver.zip < evidence.json

Only the input SHA-256 is recorded, not the local path. See docs/REPORT_ENVELOPE.md and schemas/ivan-vhs.report.v1.schema.json.
