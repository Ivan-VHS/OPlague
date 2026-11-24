# Documentation information architecture

[Project README](../README.md) · [Documentation index](README.md)

This is the canonical navigation map for OPlague. The product README is the entry point, this page is the documentation pillar, and topic hubs connect device and driver inspection, security evidence, architecture and workbench behavior.

## Navigation model

- **Entry point:** the root README states product purpose, local operating scope and read-only boundaries.
- **Pillar:** this map catalogs repository Markdown pages and defines the topic clusters.
- **Topic hubs:** the cluster pages provide contextual routes to detailed contracts and evidence.
- **Authority:** source, tests, schemas and each specific contract determine what is implemented and permitted.

## Topic hubs

- [Device, driver and package inspection](clusters/device-driver-inspection.md) — Read-only Windows device discovery, driver metadata, compatibility and package inspection contracts.
- [Security, safety and evidence](clusters/security-evidence.md) — Trust boundaries, provenance, validation, evidence handling and quality gates.
- [Architecture and system contracts](clusters/architecture-systems.md) — System structure, persistence, runtime boundaries and reusable engineering contracts.
- [Workbench UI and visual system](clusters/ui-workbench.md) — Desktop workbench interaction, motion, accessibility and visual documentation.
- [Integrations and project federation](clusters/integration-federation.md) — Runtime integration points, plugins, external tools and cross-project interfaces.
- [Governance, planning and reference material](clusters/governance-planning.md) — Stewardship, roadmap, catalog and supporting project references.

## Cross-repository boundaries

These repositories have separate responsibilities and release cycles. Follow a project's own compatibility contract before connecting tools or interpreting a shared term as a supported interface.

- [Pytyliki documentation map](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/INFORMATION_ARCHITECTURE.md) — processor-system inspection and bounded computational utilities.
- [Reaper documentation map](https://github.com/Ivan-VHS/Reaper/blob/main/docs/INFORMATION_ARCHITECTURE.md) — language, compiler and runtime integration.
- [VentuSample documentation map](https://github.com/Ivan-VHS/VentuSample/blob/main/docs/INFORMATION_ARCHITECTURE.md) — audio workstation and DSP contracts.
- [DuckOS documentation map](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/INFORMATION_ARCHITECTURE.md) — repository entry-point map.

## Full document catalog

Every Markdown page below has a direct catalog link as well as a topic-level route. Link labels identify the destination rather than repeating generic keywords.

### Device, driver and package inspection

- [AUTHENTICODE](AUTHENTICODE.md)
- [DEVICE COMPATIBILITY GRAPH](DEVICE_COMPATIBILITY_GRAPH.md)
- [DRIVER TARGET ARCHITECTURE](DRIVER_TARGET_ARCHITECTURE.md)
- [HARDWARE ID LINT](HARDWARE_ID_LINT.md)
- [SNAPSHOT CONTINUITY CADENCE](SNAPSHOT_CONTINUITY_CADENCE.md)
- [UDRV FORMAT V1](UDRV_FORMAT_V1.md)

### Security, safety and evidence

- [CLINICAL SYSTEMS CSR120](CLINICAL_SYSTEMS_CSR120.md)
- [DISTRIBUTED SYSTEMS ENGINEERING STANDARD](DISTRIBUTED_SYSTEMS_ENGINEERING_STANDARD.md)
- [DOCUMENTATION CONTROL](DOCUMENTATION_CONTROL.md)
- [DRIVE LENS EVIDENCE LEDGER](DRIVE_LENS_EVIDENCE_LEDGER.md)
- [ENGINEERING BASELINE](ENGINEERING_BASELINE.md)
- [ENGINEERING EVOLUTION FRAMEWORK](ENGINEERING_EVOLUTION_FRAMEWORK.md)
- [ENGINEERING](ENGINEERING.md)
- [IMPROVEMENT CONFLICT STANDARD](IMPROVEMENT_CONFLICT_STANDARD.md)
- [IVAN VHS ENGINEERING PROFILE](IVAN_VHS_ENGINEERING_PROFILE.md)
- [LANGUAGE QUALITY](LANGUAGE_QUALITY.md)
- [PROJECT STEWARDSHIP STANDARD](PROJECT_STEWARDSHIP_STANDARD.md)
- [QUALITY COMMERCIAL STANDARD](QUALITY_COMMERCIAL_STANDARD.md)
- [QUALITY REMEDIATION STANDARD](QUALITY_REMEDIATION_STANDARD.md)
- [QUALITY REPEATABILITY NATIVE](QUALITY_REPEATABILITY_NATIVE.md)
- [ROADMAP GOVERNANCE AND CI SCALE](ROADMAP_GOVERNANCE_CI_SCALE.md)
- [REPORT ENVELOPE](REPORT_ENVELOPE.md)
- [SECURITY](../SECURITY.md)

### Architecture and system contracts

- [ANATIDAE DESKTOP DESIGN SYSTEM](ANATIDAE_DESKTOP_DESIGN_SYSTEM.md)
- [ANATIDAE MOTION CONSTITUTION](ANATIDAE_MOTION_CONSTITUTION.md)
- [ARCHITECTURE](ARCHITECTURE.md)
- [ATOMIC QUANTUM 133](ATOMIC_QUANTUM_133.md)
- [ATOMIC SETTINGS PERSISTENCE](ATOMIC_SETTINGS_PERSISTENCE.md)
- [CONCATENATION ARCHITECTURE](CONCATENATION_ARCHITECTURE.md)
- [DUCKSTORY](DUCKSTORY.md)
- [MOTION CONSTITUTION V2026](MOTION_CONSTITUTION_V2026.md)
- [TRANSACTIONAL RUNTIME](TRANSACTIONAL_RUNTIME.md)
- [UNIFIED PROJECT CONTRACT](UNIFIED_PROJECT_CONTRACT.md)

### Workbench UI and visual system

- [UI MOTION](UI_MOTION.md)
- [UI UX 2026 CONVERGENCE](UI_UX_2026_CONVERGENCE.md)
- [UI UX CODEX 40026](UI_UX_CODEX_40026.md)
- [UI UX SYSTEM](UI_UX_SYSTEM.md)
- [VISUAL DOCUMENTATION](VISUAL_DOCUMENTATION.md)

### Integrations and project federation

- [FEDERATED INTEGRATION](FEDERATED_INTEGRATION.md)
- [OCTA PYRAMID FEDERATION](OCTA_PYRAMID_FEDERATION.md)
- [PLUGIN FEDERATION](PLUGIN_FEDERATION.md)
- [REAPER RUNTIME INTEGRATION](REAPER_RUNTIME_INTEGRATION.md)
- [REPLACEMENT TOOLS](REPLACEMENT_TOOLS.md)
- [RESOURCE ALLOCATION 500 UAH](RESOURCE_ALLOCATION_500_UAH.md)
- [SELF PRODUCT COMPOSITION](SELF_PRODUCT_COMPOSITION.md)

### Governance, planning and reference material

- [CONTRIBUTING](../CONTRIBUTING.md)
- [AUTOMATION ROADMAP](AUTOMATION_ROADMAP.md)
- [DUCK SOVEREIGN CANON](DUCK_SOVEREIGN_CANON.md)
- [FEATURES](FEATURES.md)
- [HUMAN FIRST GOVERNANCE](HUMAN_FIRST_GOVERNANCE.md)
- [MARKET DEVELOPMENT STANDARD](MARKET_DEVELOPMENT_STANDARD.md)
- [MICROBUDGET PLANNER](MICROBUDGET_PLANNER.md)
- [ORTHOGONAL METRIC DIAGNOSTICS](ORTHOGONAL_METRIC_DIAGNOSTICS.md)
- [PROGRAM CATALOG 1000](PROGRAM_CATALOG_1000.md)
- [QUANTUM CONTOUR SYNTAX](QUANTUM_CONTOUR_SYNTAX.md)
- [UNIFIED DOCUMENTATION STANDARD](UNIFIED_DOCUMENTATION_STANDARD.md)
- [README](../README.md)
- [README.Ru](../README.ru.md)
- [README.Uk](../README.uk.md)
- [README.Zh CN](../README.zh-CN.md)

## Maintenance contract

A new page must be listed in its cluster hub and this catalog in the same change, with at least two useful inbound paths. Keep important pages within three to four clicks from the root README. Use direct relative links inside this repository and canonical HTTPS links between repositories. Never imply that read-only inspection deploys, installs or changes a driver unless a verified implementation contract says so.
