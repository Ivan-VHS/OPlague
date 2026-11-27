# OPlague documentation

**Documentation baseline:** 2026-11-26 · **Project status:** development / Windows-first read-only workbench.

Start with the [root README](../README.md) for platform scope, supported workflows and security boundaries. The [Information Architecture](INFORMATION_ARCHITECTURE.md) page catalogs the maintained documentation library.

## Core references

- [Feature matrix](FEATURES.md) — implemented inspection and reporting capabilities.
- [Architecture](ARCHITECTURE.md) — bounded evidence flow and trust boundaries.
- [UDRV format v1](UDRV_FORMAT_V1.md) — package manifest and resource constraints.
- [Device compatibility graph](DEVICE_COMPATIBILITY_GRAPH.md) — exact-ID candidate semantics.
- [Authenticode](AUTHENTICODE.md) — selected-file signature metadata boundary.
- [GPU telemetry bridge v1](GPU_TELEMETRY_BRIDGE_V1.md) — read-only snapshot contract.
- [Federated integration](FEDERATED_INTEGRATION.md) — Reaper and Pytyliki interfaces.
- [Reaper neural device evidence v1](REAPER_NEURAL_DEVICE_EVIDENCE_V1.md) — local read-only evidence triage and manual-review policy.
- [Release](RELEASE.md) — draft publication workflow and checksum limits.
- [Security](../SECURITY.md) — static repository assurance and disclosure.

## Browse by topic

- [Device, driver and package inspection](clusters/device-driver-inspection.md)
- [Security, safety and evidence](clusters/security-evidence.md)
- [Architecture and system contracts](clusters/architecture-systems.md)
- [Workbench UI and visual system](clusters/ui-workbench.md)
- [Integrations and project federation](clusters/integration-federation.md)
- [Governance, planning and reference material](clusters/governance-planning.md)

## Shared standards

- [Unified documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md)
- [Documentation control](DOCUMENTATION_CONTROL.md)
- [Engineering evolution framework](ENGINEERING_EVOLUTION_FRAMEWORK.md)
- [Repository evolution directives](REPOSITORY_EVOLUTION_DIRECTIVES.md)
- [Contributing](../CONTRIBUTING.md)

## Evidence rule

Read-only inspection is not installation or remediation. Hardware-ID matches are candidates, metadata checks are not certifications, SHA-256 is not a signature, and a static repository scanner is not endpoint protection.
