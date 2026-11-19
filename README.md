# OPlague — DuckDriver Core

**OPlague** is the repository for **DuckDriver Core (DDC)**: a planned native desktop orchestrator for hardware inventory, driver lifecycle management, device diagnostics and cross-vendor peripheral capabilities.

> **Project status:** architecture and product specification stage. The current repository does not yet contain the implemented driver-management engine or desktop client. Planned capabilities are not represented as already working features.

## Product direction

DDC is designed to be more than a driver updater. It aims to provide one local workspace for:

- **Hardware Inventory** — enumerate devices, buses, controllers, hardware IDs and active driver packages.
- **Semantic Hardware Graph** — explore relationships between devices, controllers, buses, drivers and resource dependencies.
- **Driver Vault** — import, verify, catalogue and preserve original driver packages; stage controlled install/update/rollback workflows.
- **UDB Hub** — unify supported HID, RGB, cooling and audio capabilities through explicit device adapters.
- **Latency Lab** — inspect supported DPC/ISR and device-event telemetry, correlate spikes and produce diagnostic reports.
- **Time Duck** — save driver/configuration snapshots and switch between reviewed profiles with a visible change plan.
- **Duck-Agent** — guided diagnostics, including user-initiated analysis of local crash dumps.
- **DuckMesh** — optional, opt-in compatibility insights based on privacy-minimized aggregate telemetry.

## Architecture

The intended architecture separates four layers:

1. **Platform Access** — OS-specific adapters and documented system APIs.
2. **Hardware Introspection** — inventory, package analysis, resource observations and telemetry.
3. **Orchestration / UDB** — capabilities, dependency resolution, conflict analysis, profiles and snapshots.
4. **Native UI** — Tri-Color Duck UI, connected to the local service through versioned IPC.

Proposed foundation: Rust (Edition 2024), Slint native UI, wgpu for specialized graph/telemetry rendering, FlatBuffers IPC, and SQLite in WAL mode. Windows 11 x64 is the first implementation target; Linux and macOS support will be capability-driven rather than assumed to be identical.

## Design identity

Tri-Color Duck UI uses a white/porcelain canvas, cobalt-blue structure and vermilion-red critical accents. The Duck mascot is an operational status metaphor: calm state, active scan, expert inspection and warning. It is not a substitute for textual status or accessible controls.

## Safety principles

- Read-only inventory by default.
- UI does not run with administrator privileges.
- Privileged operations are executed by a restricted local service and require explicit user approval.
- Original signed driver packages are preserved and verified; modified package files are never described as retaining their original WHQL signature.
- No disabling driver-signature enforcement, Secure Boot or OS security controls.
- Every supported system change has an audit trail and a documented recovery path.
- Unsupported hardware/platform operations are shown as unsupported, not simulated.

## Documentation

- [DuckDriver Core — functional and architecture specification](docs/architecture/DUCKDRIVER_CORE_SPEC.md)

The specification translates the source design manifesto, DDC product concept and HMGA engineering principles into finite, testable requirements. Language-compiler concepts unrelated to driver management are excluded; their applicable ideas (type safety, explicit effects, composition and isolation) are carried into the software design.

## Development sequence

1. Native Rust workspace, domain model, local service and IPC.
2. Read-only Windows inventory, Driver Inspector and Hardware Graph.
3. Driver Vault, signature/provenance checks and controlled lifecycle operations.
4. Time Duck snapshots, profiles and diagnostics.
5. UDB adapters for supported device families.
6. Additional platform adapters and optional DuckMesh.

See the architecture specification for acceptance criteria, security boundaries, platform constraints and the detailed roadmap.
