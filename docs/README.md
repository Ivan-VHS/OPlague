> **Navigation:** Start with the [information architecture map](INFORMATION_ARCHITECTURE.md), then select a [topic hub](clusters/device-driver-inspection.md). The map connects the repository's read-only device, driver, security and workbench documentation.

## Topic hubs

- [Device, driver and package inspection](clusters/device-driver-inspection.md) — Read-only Windows device discovery, driver metadata, compatibility and package inspection contracts.
- [Hardware & game performance stack](HARDWARE_GAME_STACK.md) — Fifteen read-only subsystems for firmware/platform inventory, device health, driver candidates, thermal evidence and repeatable game benchmarks.
- [Security, safety and evidence](clusters/security-evidence.md) — Trust boundaries, provenance, validation, evidence handling and quality gates.
- [Architecture and system contracts](clusters/architecture-systems.md) — System structure, persistence, runtime boundaries and reusable engineering contracts.
- [Workbench UI and visual system](clusters/ui-workbench.md) — Desktop workbench interaction, motion, accessibility and visual documentation.
- [Integrations and project federation](clusters/integration-federation.md) — Runtime integration points, plugins, external tools and cross-project interfaces.
- [Governance, planning and reference material](clusters/governance-planning.md) — Stewardship, roadmap, catalog and supporting project references.

---

# Documentation

## Related OS product

[DuckOS — Mora application suite](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/PREINSTALLED_APPLICATIONS.md) documents the seven applications provided by the OS layer. This is a related product reference only; it does not add app-suite capabilities to OPlague.

## Katyuhen ecosystem

[Integration with Katyuhen](KATYUHEN_INTEGRATION.md) records this project's ownership, registered interfaces, peer boundaries and validation requirements. The canonical federation registry is maintained in [DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/ecosystem/katyuhen.v1.json).

## Katyuhen ecosystem

[Integration with Katyuhen](KATYUHEN_INTEGRATION.md) records this project's ownership, registered interfaces, peer boundaries and validation requirements. The canonical federation registry is maintained in [DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/ecosystem/katyuhen.v1.json).

## Normative documentation standard

[Unified documentation and semantics standard](UNIFIED_DOCUMENTATION_STANDARD.md) defines the shared terminology, capability maturity, runtime states, verification outcomes, evidence rules, localization requirements and documentation acceptance criteria. It is normative for this repository; project-specific architecture and implementation evidence remain authoritative for the product itself.

| File | Purpose |
|---|---|
| [VISUAL_DOCUMENTATION.md](VISUAL_DOCUMENTATION.md) | README graphics, evidence diagrams, SVG/raster formats, typography, MDX and rendering rules |
| [FEATURES.md](FEATURES.md) | supported inspection tools and safety boundaries |
| [AUTHENTICODE.md](AUTHENTICODE.md) | local Windows signature inspection and trust boundaries |
| [PROGRAM_CATALOG_1000.md](PROGRAM_CATALOG_1000.md) | read-only binary analysis and SPDX catalogue implementation map |
| [GAMING_PERFORMANCE_WORKBENCH.md](GAMING_PERFORMANCE_WORKBENCH.md) | Reversible game sessions, hardware snapshots, frametime analysis and local profiles |
| [ARCHITECTURE.md](ARCHITECTURE.md) | device and package inspection flow |
| [ENGINEERING.md](ENGINEERING.md) | release and safety gates |
| [PROJECT_STEWARDSHIP_STANDARD.md](PROJECT_STEWARDSHIP_STANDARD.md) | operator, privacy and communication policy |
| [DISTRIBUTED_SYSTEMS_ENGINEERING_STANDARD.md](DISTRIBUTED_SYSTEMS_ENGINEERING_STANDARD.md) | resilience and trust contract |
| [DUCK_SOVEREIGN_CANON.md](DUCK_SOVEREIGN_CANON.md) | shared design tokens |
| [UI_MOTION.md](UI_MOTION.md) | accessible motion preferences, reduced-motion limits and UI performance |
| [UI_UX_SYSTEM.md](UI_UX_SYSTEM.md) | desktop interaction contract |
| [DEVICE_COMPATIBILITY_GRAPH.md](DEVICE_COMPATIBILITY_GRAPH.md) | exact-ID candidate graph; not an automatic verdict |
| [HARDWARE_GAME_STACK.md](HARDWARE_GAME_STACK.md) | 15-subsystem platform, driver-evidence and game-performance report |
| [DRIVER_TARGET_ARCHITECTURE.md](DRIVER_TARGET_ARCHITECTURE.md) | INF and PE machine codes |
| [UDRV_FORMAT_V1.md](UDRV_FORMAT_V1.md) | package manifest, hashing and size limits |
| [DRIVE_LENS_EVIDENCE_LEDGER.md](DRIVE_LENS_EVIDENCE_LEDGER.md) | evidence provenance |
| [CLINICAL_SYSTEMS_CSR120.md](CLINICAL_SYSTEMS_CSR120.md) | 120 principles and 36 advisory telemetry checks |

The root README also links the 20-entry semantic impact-profile CLI and the live Windows screenshot. JSON schemas, tests and source define machine-checked behavior. Hardware matches and ordinal profile rankings are advisory evidence, not certification.


## Motion and embedded graphics

[Motion Constitution v2026](MOTION_CONSTITUTION_V2026.md) is the shared source for timing/easing tokens, adaptive motion, reduced-motion precedence, themes, the 2×2/focus-scene lab layout, SVG/Canvas telemetry rules and the four-domain capability matrix. [UI_MOTION.md](UI_MOTION.md) records the native behavior implemented in this repository; planned showcase features are not reported as shipped.


## Bounded 500 UAH allocation reference

- [Multilingual specification](RESOURCE_ALLOCATION_500_UAH.md) — bounded budget model, scenarios and operating rules.
- [Offline interactive simulator](resource-allocation-500-uah.html) — adjust category amounts and see the remainder or overrun.
- [Example JSON](../examples/resource-allocation-500-uah.json) and [JSON Schema](../schemas/resource-allocation.v1.schema.json).

This is an illustrative personal-budgeting reference, not a claim that the host project manages payments or live retail prices.


## Language quality

[Language and editorial quality](LANGUAGE_QUALITY.md) — orthography, punctuation, lexical precision, syntax, multilingual review and conservative prose checks.


## Project-specific engineering profile

[IVAN_VHS_ENGINEERING_PROFILE.md](IVAN_VHS_ENGINEERING_PROFILE.md) translates the project's direction into concrete architecture boundaries, implementation priorities, human-readable code conventions and acceptance tests. It is a development contract; it does not mark planned work as implemented.


## Cross-project engineering

- [Engineering Evolution Framework](ENGINEERING_EVOLUTION_FRAMEWORK.md) — shared machine-readable 20-domain contract, 40 practices and 20 execution directives.
- [Repository-wide implementation directives](REPOSITORY_EVOLUTION_DIRECTIVES.md) — the 20 requested directions, their engineering meaning and acceptance rules.
