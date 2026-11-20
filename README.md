# OPlague

**Native desktop driver management, package engineering, and hardware diagnostics.**

[English](README.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [简体中文](README.zh-CN.md)

OPlague is the home of **DuckDriver OmniCore (DDO)**, a desktop-first project for safer hardware discovery, driver-package inspection, and portable driver bundles.

> **Status:** an early Windows x64 desktop preview is implemented. Device discovery, INF/ZIP inspection and normalized metric-profile comparison are read-only; driver installation, UDRV authoring, recovery and live performance telemetry remain roadmap work.

## Product vision

- **Hardware inventory:** discover devices and present hardware identifiers, relationships, and driver state.
- **Driver workspace:** import, inspect, validate, catalogue, and compare packages before installation.
- **Universal Driver Container (.udrv):** a proposed portable format for driver payloads, manifests, metadata, compatibility information, and integrity data.
- **DuckDriver OmniCore:** coordinate discovery, analysis, package validation, packaging, and deployment preparation.
- **Profiles and recovery:** preserve known-good configurations and make rollback workflows explicit.
- **Metric Lab:** compare normalized hardware or benchmark profiles using n-dimensional Euclidean distance, weighted quadratic forms, cosine similarity, orthogonality and repeated-run variance summaries.
- **Diagnostics:** expose device state and supported system signals, with DPC/ISR latency analysis planned where platform APIs permit.
- **Native UX:** a focused desktop application with a consistent white, blue, and red visual identity.

## Systems-language and native-backend matrix

OPlague includes a read-only 66-slot capability catalogue for evaluating optional native tracks: memory-safe and linear-resource models, formal verification, embedded/bare-metal targets, C ABI boundaries, concurrency and deterministic builds.

```bash
python tools/systems_languages.py --verify
python tools/systems_languages.py --profile oplague
python tools/systems_languages.py --profile oplague --available-only
python tools/systems_languages.py --tag formal-verification,embedded --json
```

The probe only checks executable names on `PATH`. OPlague does not load or execute discovered compilers, driver payloads or third-party native modules; a detected compiler is not represented as an implemented backend or a driver-compatibility guarantee.

## Safety principles

1. Inspect packages before trusting them; validate manifests, structure, metadata, and hashes where available.
2. Treat imported packages, scripts, and binaries as untrusted input.
3. Never execute foreign kernel code merely to identify or inspect hardware.
4. Separate read-only discovery and package analysis from privileged installation.
5. Make elevated actions explicit, reviewable, and reversible where the platform allows.
6. Report missing evidence and validation failures rather than guessing compatibility.

The `.udrv` format is a packaging concept, not a guarantee that arbitrary drivers are universally compatible or safe. Installation depends on the operating system, hardware, signing policy, and vendor requirements.

## Architecture map

| Layer | Responsibility |
| --- | --- |
| Native desktop shell | Lifecycle, navigation, settings, and user workflows |
| Hardware discovery | Device enumeration and stable hardware identifiers |
| Driver catalog | Package, version, provider, and compatibility indexing |
| Package validator | Manifest, content, hash, and consistency checks |
| UDRV container | Portable package structure and metadata contract |
| OmniCore orchestrator | Coordinate discovery, analysis, packaging, and deployment stages |
| Diagnostics | Device state and supported performance signals |
| Recovery manager | Profiles, snapshots, and rollback plans |

These are intended architectural boundaries, not a claim that every module is already present on `main`.

## Roadmap

- [x] Native desktop shell (early Windows preview)
- [x] Read-only Windows Plug and Play inventory
- [ ] Versioned `.udrv` container specification
- [x] INF and ZIP package inspection with hash and archive checks, plus deterministic batch report composition
- [ ] Driver catalogue and compatibility evidence
- [ ] Profile snapshots and guarded recovery
- [x] Read-only Device Metric Lab for normalized profile comparison and weighted distance analysis
- [ ] Live diagnostics, including DPC/ISR analysis where supported
- [ ] Automated tests, signed releases, and platform packaging

## Screenshots

Real application screenshots will be added when a runnable interface is available. Mockups and concept art will not be presented as screenshots of implemented software.

## Contributing

Keep changes focused and reproducible. Include tests or validation notes where practical, document OS/hardware assumptions, and do not commit proprietary driver binaries, credentials, private device data, or unlicensed vendor materials. Privileged operations must remain isolated and reviewable.

## Native desktop application

An early **Windows x64 desktop preview** is now included: read-only Windows Plug and Play inventory; INF metadata and ZIP package inspection; SHA-256 calculation and archive path/size/entry-count/compression checks. The preview does not install drivers, load kernel code, extract archives, or execute package content.

- [Windows x64 Releases](https://github.com/Ivan-VHS/OPlague/releases)
- [Desktop build workflow and downloadable CI artifacts](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml)
- [Latest workflow runs](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml?query=branch%3Amain)

A successful run uploads `OPlague-windows-x64.zip`; a `v*` tag publishes the same archive as a GitHub Release. Run from source on Windows with Python 3.10+ using `python oplague_app.py`. UDRV authoring, driver installation, rollback, signing and DPC/ISR diagnostics remain roadmap items.


`oplague_app.py` is the correctly spelled Windows source launcher used by the desktop build.

## Driver target architecture analysis

OPlague detects explicit Windows INF architecture decorations (`NTx86`, `NTamd64`, `NTarm`, `NTarm64`, `NTia64`) and compares them with the normalized host architecture. Results are evidence-based (`explicit_match`, `explicit_nonmatch`, or `unknown`), and are included in standalone INF and ZIP package reports. This does not certify signing, OS-version support, device-ID match, or successful installation. See [Driver Target Architecture Analysis](docs/DRIVER_TARGET_ARCHITECTURE.md).

## Concatenation and report composition

The desktop package inspector supports ordered batch inspection of multiple INF/ZIP inputs and produces a bounded, canonical JSON summary with aggregate counts and a bundle SHA-256 fingerprint. This fingerprint is not a vendor signature or compatibility verdict. See [the composition architecture](docs/CONCATENATION_ARCHITECTURE.md).

## License

See [LICENSE](LICENSE) for the terms that apply to this repository.


## Read-only UDRV integrity inspector

The first executable UDRV tooling is available as a read-only package inspector.
It accepts a directory package or ZIP archive and checks the versioned manifest,
payload inventory, declared sizes, and SHA-256 hashes. It rejects undeclared
files, missing files, path traversal, symbolic links, duplicate paths, malformed
manifests, and packages exceeding documented resource limits.

Run it with:

    python tools/udrv_inspector.py path/to/package.udrv
    python tools/udrv_inspector.py path/to/package.udrv --json
    python -m unittest discover -s tests -p 'test_udrv_inspector.py' -v

The inspector does not extract, install, load, or execute driver payloads and
does not contact external services. It verifies package integrity only; it does
not establish vendor authenticity or driver compatibility.


## Orthogonal metric diagnostics

The desktop application includes a **Metric Lab** tab. Paste two JSON metric profiles with matching keys and values normalized to [0, 1], where higher values mean better results. Optional per-metric weights control the diagonal quadratic form. The analysis reports Euclidean and weighted distance, cosine similarity, angle, orthogonality, energy and per-dimension contributions. The numerical module also summarizes repeated measurements, calculates sample variance and exposes Parseval coefficient energy.

The analyzer does not infer missing values or claim driver compatibility. See [Orthogonal Metric Diagnostics](docs/ORTHOGONAL_METRIC_DIAGNOSTICS.md) for assumptions and examples.

## Exact-ID compatibility graph and dry-run

The desktop **Compatibility & dry-run** tab connects the refreshed local PnP
inventory with hardware identifiers declared in inspected INF `Models`
sections. It creates candidate edges only for exact normalized identifier
matches and reports architecture mismatches separately. Prefix/name similarity
is never treated as compatibility.

A candidate is **not** a driver-rank, signature, trust, Windows-build or safety
verdict. The generated plan is explicitly read-only:
`install_attempted=false`, `system_modified=false`,
`proposed_operation=none`. Manual review and further evidence are mandatory.
See [the compatibility graph contract](docs/DEVICE_COMPATIBILITY_GRAPH.md).
