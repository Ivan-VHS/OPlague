# OPlague

**Native desktop driver management, package engineering, and hardware diagnostics.**

[English](README.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [简体中文](README.zh-CN.md)

OPlague is the home of **DuckDriver OmniCore (DDO)**, a desktop-first project for safer hardware discovery, driver-package inspection, and portable driver bundles.

> **Status:** early active development. The default branch is not yet a release-ready application. This README describes product goals and planned architecture; it does not claim that every workflow is implemented.

## Product vision

- **Hardware inventory:** discover devices and present hardware identifiers, relationships, and driver state.
- **Driver workspace:** import, inspect, validate, catalogue, and compare packages before installation.
- **Universal Driver Container (.udrv):** a proposed portable format for driver payloads, manifests, metadata, compatibility information, and integrity data.
- **DuckDriver OmniCore:** coordinate discovery, analysis, package validation, packaging, and deployment preparation.
- **Profiles and recovery:** preserve known-good configurations and make rollback workflows explicit.
- **Diagnostics:** expose device state and supported system signals, with DPC/ISR latency analysis planned where platform APIs permit.
- **Native UX:** a focused desktop application with a consistent white, blue, and red visual identity.

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

- [ ] Native desktop shell and design system
- [ ] Hardware discovery and searchable device inventory
- [ ] Versioned `.udrv` container specification
- [ ] Package import, inspection, and validation
- [ ] Driver catalogue and compatibility evidence
- [ ] Profile snapshots and guarded recovery
- [ ] Diagnostics, including DPC/ISR analysis where supported
- [ ] Automated tests, signed releases, and platform packaging

## Screenshots

Real application screenshots will be added when a runnable interface is available. Mockups and concept art will not be presented as screenshots of implemented software.

## Contributing

Keep changes focused and reproducible. Include tests or validation notes where practical, document OS/hardware assumptions, and do not commit proprietary driver binaries, credentials, private device data, or unlicensed vendor materials. Privileged operations must remain isolated and reviewable.

## License

See [LICENSE](LICENSE) for the terms that apply to this repository.
