# Repository Security Assurance v2

## Coverage

The federated assurance workflow audits tracked source and configuration files of **Pytyliki, Reaper, OPlague and VentuSample**. It does not execute inspected source during static scanning. Findings contain rule ID, severity, repository-relative path and line number only; secret values and source snippets are never included.

### Automated controls

- **Source audit:** high-confidence private-key/token patterns, hard-coded credential assignments, developer-machine paths, sensitive-value logging and selected risky APIs.
- **CodeQL:** Python and GitHub Actions source analysis with the extended query suite.
- **Dependency vulnerabilities:** OSV-Scanner compares dependency advisories on Pull Requests and performs a scheduled full scan; GitHub Dependency Review gates pull-request dependency changes, while Dependabot for GitHub Actions, and an offline inventory of dependency manifests, lockfiles, CMake/package declarations and exact pins.
- **Fuzz smoke:** production _parse_manifest, parse_inf_text and inspect_package paths receive deterministic bounded malformed JSON/INF and ZIP-shaped inputs, including traversal entries.
- **Privacy regression:** synthetic-token detection, redaction, local-path handling and policy prohibitions are tested.
- **Federation:** all four repositories are checked for policy/tool parity; actual tracked source and dependency declarations are scanned in each checkout.

## Run locally

1. Run scripts/security_audit.py and scripts/dependency_audit.py.
2. Run scripts/test_privacy_regressions.py.
3. Run scripts/fuzz_smoke.py.
4. Run python -m unittest discover -s tests -v.

The fuzz corpus is fixed-seed and bounded; invalid data is rejected without extracting or executing package payloads. Package format limits, ZIP traversal checks and read-only device inventory remain mandatory.

## Shared score

All four projects use the same 100-point score:

| Category | Weight |
|---|---:|
| Secret hygiene | 20 |
| Privacy leak prevention | 15 |
| Source-risk review | 15 |
| Fuzz robustness | 15 |
| Dependency pin hygiene | 5 |
| Known dependency vulnerabilities (OSV) | 10 |
| Privacy regressions | 10 |
| Federation consistency | 10 |

The federated report also scores cross-repository policy/tool parity, aggregate source findings and dependency pin hygiene. A critical credential finding, known dependency vulnerability, failed fuzz/privacy/federation check or total below 70 fails the assurance gate.

## Boundaries

The scanner is heuristic, not a proof of vulnerability absence. CodeQL adds language-aware analysis. Dependency inventory and pin checks are offline; GitHub Dependency Review checks supported pull-request dependency changes but does not cover every system dependency. Fuzz-smoke is not continuous coverage-guided fuzzing. OPlague remains a read-only inspector: this workflow does not authorize package extraction, execution, loading or driver installation.
