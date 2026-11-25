# OPlague documentation

Start with the [project README](../README.md) for the workbench overview, supported platforms and build instructions. The [documentation map](INFORMATION_ARCHITECTURE.md) is the full catalogue.

## Key pages

- [Features and limits](FEATURES.md)
- [Architecture](ARCHITECTURE.md)
- [Authenticode inspection](AUTHENTICODE.md)
- [Gaming performance workbench](GAMING_PERFORMANCE_WORKBENCH.md)
- [Read-only GPU telemetry bridge v1](GPU_TELEMETRY_BRIDGE_V1.md)
- [Reaper runtime integration](REAPER_RUNTIME_INTEGRATION.md) — optional scalar ABI and policy-only source integration.
- [Driver target architecture](DRIVER_TARGET_ARCHITECTURE.md)
- [UDRV package format](UDRV_FORMAT_V1.md)

The Reaper policy example [reaper_device_evidence_policy.rpr](../examples/reaper_device_evidence_policy.rpr) validates snapshot provenance, freshness, bounded payload metadata and read-only review actions. It does not install or execute drivers.

## Browse by topic

- [Device and driver inspection](clusters/device-driver-inspection.md)
- [Security and evidence](clusters/security-evidence.md)
- [Architecture and contracts](clusters/architecture-systems.md)
- [Workbench UI](clusters/ui-workbench.md)
- [Integrations and federation](clusters/integration-federation.md)
- [Planning and governance](clusters/governance-planning.md)

## Shared rules

- [Documentation standard](UNIFIED_DOCUMENTATION_STANDARD.md)
- [Engineering evolution framework](ENGINEERING_EVOLUTION_FRAMEWORK.md)
- [Repository evolution directives](REPOSITORY_EVOLUTION_DIRECTIVES.md)

Device discovery and package analysis are read-only unless a specific workflow says otherwise. Compatibility candidates and telemetry are evidence, not certification.
