# Atomic-Quantum 133 — OPlague evidence adapter

OPlague integrates the shared 133-function catalogue as a read-only evidence and simulation-report inspection domain. It validates operation identifiers and accepts explicitly supplied simulation telemetry; it does not control devices, install drivers, or infer that a physical quantum system exists.

## Families

| Ordinals | Family | Scope |
|---|---|---|
| 001–022 | State | Qubit/atom initialization, normalization, rotations and level models |
| 023–044 | Entanglement | Bell/GHZ/W construction and correlation measurements |
| 045–066 | Measurement | Projective sampling, readout, feedback and telemetry |
| 067–088 | Noise / ECC | Channels, syndrome primitives and code helpers |
| 089–110 | Atomic dynamics | Lattice, potential and transport models |
| 111–133 | Algorithms / telemetry | Algorithmic kernels and health metrics |

## Evidence boundary

- Canonical manifest: `schemas/atomic-quantum-functions.v1.json`; schema: `schemas/atomic-quantum-functions.v1.schema.json`.
- Imported values must carry a source, unit, timestamp/window, uncertainty and a declared quality label before they can be compared.
- Simulation, estimated and observed values are distinct evidence classes. A simulation report is never promoted to an observed hardware measurement.
- This adapter is read-only: no system driver, firmware, registry or device state is changed.

See [OPlague architecture](ARCHITECTURE.md) and [DRIVE-LENS evidence ledger](DRIVE_LENS_EVIDENCE_LEDGER.md).
