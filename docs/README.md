# OPlague documentation

> **Documentation review:** 2026-11-27 UTC · **Status:** development · **Primary target:** Windows

[English README](../README.md) · [Українська](../README.uk.md) · [Русский](../README.ru.md) · [简体中文](../README.zh-CN.md)

OPlague has two separate operator workflows: read-only device/driver/package evidence and a user-confirmed, reversible Windows gaming-session power-plan transition. This index links implementation boundaries, evidence handling, integration contracts and operator guidance.

## Start here

- [Root README](../README.md) — project scope, safety boundaries, quick start and current limitations.
- [Architecture](ARCHITECTURE.md) — inventory, bounded inspection, evidence and reporting flow.
- [Feature matrix](FEATURES.md) — implemented modules and explicit exclusions.
- [Information architecture](INFORMATION_ARCHITECTURE.md) — document catalogue.
- [Documentation control](DOCUMENTATION_CONTROL.md) — evidence and publication acceptance.
- [Unified documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md) — shared maturity and evidence terminology.

## Topic hubs

- [Device, driver and package inspection](clusters/device-driver-inspection.md)
- [Security, safety and evidence](clusters/security-evidence.md)
- [Architecture and system contracts](clusters/architecture-systems.md)
- [UI and workbench visuals](clusters/ui-workbench.md)
- [Integration and federation](clusters/integration-federation.md)
- [Governance and planning](clusters/governance-planning.md)

## Operational references

- [UDRV format v1](UDRV_FORMAT_V1.md) — bounded manifest and payload-integrity inspection.
- [Device compatibility graph](DEVICE_COMPATIBILITY_GRAPH.md) — exact-ID candidate relationships, not certification.
- [Reaper runtime integration](REAPER_RUNTIME_INTEGRATION.md) — versioned snapshot and telemetry policy boundaries.
- [Drive Lens evidence ledger](DRIVE_LENS_EVIDENCE_LEDGER.md)
- [Hardware ID lint](HARDWARE_ID_LINT.md)
- [Quality remediation standard](QUALITY_REMEDIATION_STANDARD.md) · [Quality repeatability native](QUALITY_REPEATABILITY_NATIVE.md)

## Contribution and security

See [CONTRIBUTING.md](../CONTRIBUTING.md) for local verification and review expectations, and [SECURITY.md](../SECURITY.md) for the repository security policy.

Hashes, exact IDs and heuristic metrics are evidence inputs; none independently proves compatibility, safety or publisher authenticity. The gaming-session power-plan operation is a separate, explicitly confirmed Windows state change and must not be described as read-only inspection.
