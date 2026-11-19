# OPlague — native driver management workstation

[English](README.md) · [Українська](README.uk.md) · [Русский](README.ru.md) · [简体中文](README.zh-CN.md)

**OPlague is the project name for a planned native desktop application focused on driver inventory, package unification and controlled device maintenance.**

## Repository status

This repository is currently a project bootstrap: it contains the license and README, but no application source, build system, installer, automated tests or runnable desktop binary. The product description below defines the intended direction; it must not be read as a claim that these features are already implemented.

## Product direction

- **Device inventory:** enumerate hardware and collect identifiers, current driver/provider/version and device status.
- **Driver package workspace:** inspect package metadata, compare versions and maintain a local, traceable package catalogue.
- **Unified package concept:** investigate a normalized `.udrv` container with manifests, payload references, compatibility metadata, hashes and signatures. A universal package must not bypass vendor installation requirements or Windows driver signing.
- **Compatibility analysis:** match hardware IDs, OS build, architecture and package constraints before proposing an installation.
- **Controlled operations:** preview changes, create restore/recovery points where supported, require explicit confirmation for privileged changes, and record operation logs.
- **Native desktop UX:** a clear device-centric workspace with search, filters, package details, diagnostics and operation history.

## Screenshots

No runnable OPlague application or genuine application screenshots are present in this repository yet. No mockups are presented as product screenshots. Add captures only after a real desktop build can be launched.

## Planned engineering gates

1. Establish the native application shell, build pipeline and automated tests.
2. Implement read-only device discovery and exportable inventory.
3. Add driver package parsing and metadata validation.
4. Implement compatibility checks and a dry-run installation plan.
5. Add privileged install/rollback workflows with signing checks, audit logs and recovery handling.
6. Capture real screenshots from tested application builds and update this README.

## Safety and platform boundaries

Driver installation and removal can make a system unbootable or disable hardware. OPlague must never silently replace drivers, disable signature enforcement, install unsigned packages, or modify kernel-level components without an explicit user-approved operation. Package metadata, hashes and signatures must be verified before installation. Unsupported devices and OS combinations must fail closed.

These are design requirements, not existing guarantees: the current repository does not yet implement driver operations.

## Development

There is no build or run command yet because application source and build configuration have not been added. The next implementation milestone is a reproducible native desktop skeleton with CI and tests.

## License

[Apache License 2.0](LICENSE).

> 千里之行，始于足下。 — A journey of a thousand miles begins with a single step.
