# OPlague documentation

The root [README](../README.md) is the product entry point for setup, live device inventory, package inspection, input limits and safety boundaries. This index routes contributors to the underlying contracts.

## Topic hubs

| Hub | Scope |
|---|---|
| [Device, driver and package inspection](clusters/device-driver-inspection.md) | Windows discovery, INF/ZIP/PE inspection, identifiers and candidate compatibility |
| [Security, safety and evidence](clusters/security-evidence.md) | Trust boundaries, provenance, validation and evidence handling |
| [Architecture and system contracts](clusters/architecture-systems.md) | Runtime structure, persistence, schemas and bounded processing |
| [Workbench UI and visual system](clusters/ui-workbench.md) | Desktop interaction, accessibility, motion and visual assets |
| [Integrations and federation](clusters/integration-federation.md) | Reaper bridge, DuckOS/Mora references and external interfaces |
| [Governance and planning](clusters/governance-planning.md) | Stewardship, maturity, roadmap and reference material |

## Core references

- [Architecture](ARCHITECTURE.md) — implemented inspection and report flow.
- [Features](FEATURES.md) — supported tools and their limits.
- [Device compatibility graph](DEVICE_COMPATIBILITY_GRAPH.md) — exact-ID candidate relationships, not certification.
- [UDRV format v1](UDRV_FORMAT_V1.md) — manifest, hashing and size bounds.
- [Visual documentation](VISUAL_DOCUMENTATION.md) — screenshots, diagrams, theme handling and Markdown.
- [Contributing](../CONTRIBUTING.md) — safe fixtures, tests and review requirements.

## Safety rule

Describe observations separately from conclusions. An exact hardware-ID match, a file hash, a PE header or a metadata signature field does not by itself prove a package safe, trusted or suitable for a machine. Package inspection must remain bounded and must not extract or execute submitted driver payloads.
