# Roadmap governance and bounded CI scale

**Repository:** `Ivan-VHS/OPlague`  
**Policy contracts:** `.architecture/roadmap-governance.v1.json` and `.architecture/ci-scale-policy.v1.json`  
**Validator:** `tools/validate_delivery_contracts.py`  
**Scope:** Windows-first, read-only device/driver inspection and bounded package/evidence analysis.

## Capability maturity

| Status | Required evidence | Permitted claim |
|---|---|---|
| `active` | Existing implementation/control, valid evidence paths, regression verification and an executable acceptance gate | The scoped control exists and its stated checks run |
| `extend` | Existing partial control, explicit gap and a next measurable acceptance gate | The target is only partially delivered |
| `planned` | Explicit blocker, owner/dependency and exit criteria | Not implemented; no shipped-capability claim is permitted |
| `not_applicable` | Explicit product-scope rationale, owner and a trigger that would change the product boundary | The capability is outside this product's current scope; it is not an unfinished feature |

A `not_applicable` status is valid only when the machine-readable roadmap includes a specific reason and the validator tests that reason. Use it for capability areas outside the approved product boundary; do not use it to hide incomplete implementation.

A Markdown checkbox, schema, interface declaration or passing documentation validator is not runtime implementation evidence. OPlague is an evidence-first, read-only system tool; the word “driver” in a plan does not authorize driver installation or hardware writes.

## Priority and change control

- **P0:** safety, data integrity, signature/trust boundary, compatibility break or release blocker. Maintainer review required.
- **P1:** core workflow correctness, evidence quality, maintainability or measurable capability gap. Peer/maintainer review required.
- **P2:** bounded improvement with a supported workaround. Normal review and explicit acceptance evidence required.

Every behavior-changing proposal must document affected platforms and workflows, reproduction evidence, acceptance criteria, risks/dependencies, verification commands and rollback. Semantic roadmap status changes are versioned pull-request changes. Branch updates use an expected head SHA and conflicting branches remain for maintainer resolution.

## CI execution budget

Global ceiling: **5 runner jobs**, **45 minutes per job**, **3 parallel matrix workers**.

| Workflow | Runner jobs | Per-job ceiling |
|---|---:|---:|
| Windows desktop build/package | 2 | 40 min |
| Quality, Repeatability and Native Contract | 1 | 15 min |
| Automation Roadmap Contract | 1 | 10 min |
| Quality remediation matrix | 1 | 15 min |
| Verified Mainline Auto-Merge | 5 | 35 min |
| Update Behind Pull Request Branches | 1 | 15 min |
| Improvement and conflict contract | 1 | 10 min |
| Quality and commercial readiness | 1 | 15 min |
| Safe CI Recovery | 1 | 5 min |

All scoped workflows require explicit concurrency/cancellation policy. Every runner job must declare `timeout-minutes`; matrices require `max-parallel`. These ceilings do not weaken Windows qualification or read-only inspection tests.

## Safe recovery and release boundaries

Safe CI Recovery is manual-only, runs from protected `main`, permits only same-repository allow-listed workflows with failed/timed-out conclusions, reruns failed jobs only, and allows one retry maximum. Forks, cancelled/successful/action-required runs and repeated retries are rejected.

Hardware and package operations remain read-only: no driver/firmware installation, device writes, flashing, clock/voltage control, payload extraction or executable launch is authorized by this roadmap. Production deployment remains inapplicable to this local desktop tool. Public release requires an explicit maintainer release action, a protected review boundary and verified signing/provenance before final publication.

## Toolchain optimization

Workstream 06 remains `extend` until comparable before/after measurements exist for clean and incremental packaging/builds, Python startup, unit-test duration, peak memory and artifact identity. No unmeasured PyInstaller or Python-version change is treated as an optimization.

## Verification

```sh
python tools/validate_delivery_contracts.py --self-test
python -m unittest discover -s tests -p "test_delivery_contracts.py" -v
python scripts/validate_automation_roadmap.py --strict
python -m unittest discover -s tests -p "test_safe_rerun.py" -v
```

These commands validate the contract declarations and regression denials. Windows desktop packaging, complete unit tests, read-only inspectors and the security gates remain authoritative runtime checks.
