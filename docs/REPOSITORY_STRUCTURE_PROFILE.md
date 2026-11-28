# Repository Structure Profile — OPlague

**Normative reference:** [Ivan-VHS Repository Structure Standard](https://github.com/Ivan-VHS/DAK/blob/main/docs/REPOSITORY_STRUCTURE_STANDARD.md).

This profile maps the shared architecture to OPlague's read-only device/package inspection workbench and its native Rust interop crate. It preserves the existing safety boundaries and does not create an artificial monolithic `src/` tree.

## Canonical layout

| Concern | Existing canonical location | Responsibility |
|---|---|---|
| Public project entry | `README*.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE` | Product scope, supported workflows, contribution and security policy |
| Architecture and specifications | `docs/README.md`, `docs/ARCHITECTURE.md`, `docs/INFORMATION_ARCHITECTURE.md`, domain guides | Evidence flow, read-only guarantees, driver/package and telemetry contracts |
| Python workbench | `oplague/`, `tools/` | Application/domain services and bounded inspection/report tooling |
| Native interoperability | `crates/` | Rust crates and their own `Cargo.toml`, `src/` and native tests |
| Verification | `tests/`, `examples/` | Unit, integration, regression and adversarial-fixture coverage |
| Machine contracts | `schemas/`, versioned manifests and root project contracts | Device snapshots, package formats, reports and interoperability schemas |
| Reproducible tooling | `scripts/`, `pyproject.toml` | Validators, build/test entry points and maintenance automation |
| Supporting material | `assets/`, `examples/`, `security/`, `federation/` | Licensed visuals, fixtures, security policy and cross-project contracts |
| CI | `.github/workflows/` | Tests, native builds, documentation, security and contract gates |

## Domain separation

- The read-only inspection boundary is part of the product contract. Directory placement must not imply permission to install, flash, execute or modify driver payloads.
- Python application code, Rust interoperability code, schemas and generated reports retain distinct owners and validation paths.
- Device/GPU snapshots and Pytyliki/Reaper integrations remain versioned contracts. Consumers must not silently reinterpret or weaken their safety guarantees.
- Security evidence, signatures, exact-ID matching and candidate graphs remain separate concepts; a candidate is not an installation recommendation or compatibility certification.

## Formal evidence

Executable contract tests, schema validation and bounded fixtures are the current verification model. Do not add a formal-proof directory unless a real formal method and repeatable checker are adopted. Tests prove only the cases and boundaries they execute.

## Change rule

Moving a component requires updating package imports, crate manifests, schema paths, evidence registries, tests, docs, release packaging and relevant workflows in the same reviewed change.
