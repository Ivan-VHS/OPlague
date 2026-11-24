# Automation Roadmap — OPlague

**Contract:** `anatidae.automation-roadmap.v1`  
**Repository:** `Ivan-VHS/OPlague`  
**Default branch:** `main`

## Scope

Device and driver inspection, compatibility evidence, hardware snapshots, diagnostics, and safe read-only analysis.

Stack: Native systems tooling, C/C++, Python 3.

This roadmap turns the 20 requested directions into traceable workstreams. It distinguishes existing automation from work that still needs to be built: **active** means a relevant control already exists; **extend** means a control exists but does not yet deliver the full target; **planned** means it is not enabled and must not be described as implemented.

## Execution phases

1. **Baseline and contract.** Keep the roadmap, schema, documentation, and evidence references synchronized. The contract workflow checks the registry on pull requests, relevant pushes, a weekly schedule, and manual dispatch.
2. **Continuous verification.** Extend existing CI, architecture, quality, branch-synchronization, and verified auto-merge controls without duplicating them or weakening required checks.
3. **Recovery, scale, and release gates.** Introduce bounded recovery and resource-aware validation only after tests. Deployment and publication remain disabled until a protected target, rollback procedure, and human approval are defined.

## Workstream register

| ID | Direction | Priority | Status | Current evidence |
|---|---|---:|---|---|
| `01-plan-governance` | Запланировать | P0 | active | `.architecture/roadmap-governance.v1.json`, `.architecture/roadmap-governance.v1.schema.json`, `validate_delivery_contracts.py`, `test_delivery_contracts.py` |
| `02-organize-triggers` | Организовать | P0 | active | `.github/workflows/verified-auto-merge.yml`, `.github/workflows/update-behind-pr-branches.yml` |
| `03-systematize-sync` | Систематизировать | P0 | active | `project-contract.json`, `federation/octa-pyramid.v1.json` |
| `04-prioritize-change-flow` | Приоритизировать | P1 | active | `improvement-conflict.yml`, `quality-remediation.yml`, `.github/ISSUE_TEMPLATE/engineering_improvement.yml` |
| `05-refresh-project-config` | Актуализировать | P0 | active | `project-contract.json`, `.architecture/resilience-policy.json` |
| `06-optimize-toolchain` | Оптимизировать | P1 | extend | `.architecture/resilience-policy.json`, `.architecture/resilience-policy.schema.json` |
| `07-synchronize-branches` | Синхронизировать | P0 | active | `.github/workflows/update-behind-pr-branches.yml` |
| `08-integrate-projects` | Интегрировать | P0 | active | `project-contract.json`, `federation/octa-pyramid.v1.json` |
| `09-modernize-quality-flow` | Модернизировать | P0 | active | `.github/workflows/quality-remediation.yml`, `quality-remediation.v1.json` |
| `10-automate-diagnostics` | Автоматизировать | P0 | active | `.github/workflows/quality-remediation.yml`, `.github/workflows/update-behind-pr-branches.yml` |
| `11-structure-test-updates` | Структурировать | P0 | active | `.github/workflows/quality-repeatability-native.yml`, `tests/test_inspector.py` |
| `12-scale-validation` | Масштабировать | P1 | active | `.architecture/ci-scale-policy.v1.json`, `.architecture/ci-scale-policy.v1.schema.json`, `validate_delivery_contracts.py`, `test_delivery_contracts.py`, Windows and verified merge workflows |
| `13-implement-verification` | Реализовать | P0 | active | `.github/workflows/quality-commercial.yml`, `.github/workflows/quality-remediation.yml` |
| `14-coordinate-deployment` | Координировать | P2 | planned | `.github/workflows/verified-auto-merge.yml`, `project-contract.json` |
| `15-consolidate-test-matrix` | Консолидировать | P1 | active | `.github/workflows/quality-repeatability-native.yml`, `tests/test_inspector.py` |
| `16-improve-recovery` | Усовершенствовать | P1 | active | `safe-ci-recovery.yml`, `automation-rerun-policy.v1.json`, `validate_safe_rerun.py`, `test_safe_rerun.py` |
| `17-test-controls` | Протестировать | P0 | active | `.github/workflows/quality-remediation.yml`, `tests/test_inspector.py` |
| `18-verify-observability` | Верифицировать | P1 | active | `verified-auto-merge.yml`, `update-behind-pr-branches.yml`, `safe-ci-recovery.yml` |
| `19-document-automation` | Документировать | P1 | active | `docs/README.md`, `docs/DOCUMENTATION_CONTROL.md`, this roadmap |
| `20-release-publication` | Развернуть | P2 | extend | `.github/workflows/desktop-build.yml`, `docs/RELEASE.md`, `project-contract.json` |

## Operating rules

- The new roadmap workflow is read-only and uses `contents: read`.
- The roadmap validator is also run inside the existing verified merge gate (or the CI gate for VentuSample).
- Existing verified auto-merge remains conditional on successful checks and repository protection; this roadmap does not bypass either.
- Branch synchronization must use an expected head SHA, operate only on eligible same-repository pull requests, and leave conflicts for maintainers.
- Diagnostics, schema checks, and scheduled audits must be deterministic, bounded, and non-destructive.
- Automated code correction may produce a reviewable proposal; it must not silently rewrite source or commit directly to `main`.
- This roadmap does **not** authorize production deployment, external publication, secret rotation, destructive cleanup, firmware flashing, or driver installation.
- A workstream marked `planned` or `extend` is not complete. Update its status only with implementation and passing evidence.

## Validation

Run locally:

```bash
python scripts/validate_automation_roadmap.py --strict
```

The validator uses only the Python standard library and checks all 20 identifiers, project metadata, safety settings, documentation coverage, and the existence of every referenced evidence file.

## Additional execution controls

- **Prioritization (04):** new improvement issues require P0/P1/P2, impact, reproduction evidence, acceptance criteria, risk/dependency notes, verification and rollback.
- **Recovery (16):** `.github/workflows/safe-ci-recovery.yml` is manual-only, runs from protected `main`, permits failed/timed-out allow-listed validation runs from this repository only, reruns failed jobs only, and enforces two total attempts (one retry). Fork runs, cancellations, successful runs, unlisted workflows and exhausted attempts are rejected.
- **Observability (18):** the recovery decision is written to the GitHub Actions step summary with workflow, run ID, branch, commit and attempt number. Every recovery request is linked to its original Actions run.
- **Documentation (19):** policy, implementation, tests, issue intake and workflow are linked by the roadmap registry and its evidence validator.

## Deliberate release boundaries

Workstream 14 remains planned because these repositories do not have a production service deployment target; local desktop/CLI packaging is not production deployment. Workstream 20 is now `extend`: tag packaging verifies the archive checksum and creates a draft GitHub Release behind the `release-review` environment. It remains incomplete until administrators configure and verify required reviewers in that environment, and a maintainer reviews the signing/provenance and publication process. The recovery workflow does not deploy or publish artifacts.

## Governance and bounded CI

- **Workstream 01:** the governance policy and schema define evidence-based maturity states, P0/P1/P2 review rules, versioned status changes, expected-head branch updates and release boundaries. The roadmap validator runs the executable negative-case tests.
- **Workstream 12:** the scale policy applies to the Windows desktop package, verified auto-merge, roadmap, quality, remediation, branch synchronization, conflict governance and safe recovery workflows. Every scoped runner has a timeout; workflow concurrency and matrix parallelism are explicit.
- **Read-only boundary:** the policy never authorizes driver installation, firmware updates, device writes, payload extraction or executable launch. Windows hardware inventory remains evidence collection only.
- **Release boundary:** the tag workflow creates a draft release only. A maintainer must inspect it and complete signing/provenance review before public publication. No production deployment is configured.
- **Toolchain optimization (06):** remains `extend` until comparable build/package and test-duration baselines are recorded; no unmeasured compiler, Python or PyInstaller change is accepted.
