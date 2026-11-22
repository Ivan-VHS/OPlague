# Contributing to OPlague

Thank you for helping improve OPlague. OPlague is a read-only workbench for Windows PnP inventory, bounded INF and ZIP inspection, package evidence, and review workflows.

## Preserve the project boundary

The application inspects and reports; it does not install, update, extract, execute, or repair drivers. Keep package parsing bounded and treat archive paths, INF text, manifests, and device identifiers as untrusted input. Heuristics must be presented as observations that require human review, never as malware verdicts, compatibility guarantees, or safety claims.

## Before opening a pull request

1. Read README.md and the relevant inspection, evidence, and architecture documents under docs/.
2. Add focused tests for malformed inputs, size boundaries, path traversal, duplicate entries, and unknown identifiers where relevant.
3. Preserve source provenance and distinguish machine-collected facts from reviewer notes or derived observations.
4. Update README.md, README.uk.md, README.ru.md, and README.zh-CN.md when user-visible behavior, supported limits, report fields, or examples change.
5. Update the device snapshot, UDRV, or report schema when a machine-readable contract changes.
6. Keep Windows-only inventory paths explicit; portable parsers and validators should remain testable without Windows hardware.

## Local checks

    python -m compileall -q oplague tools tests
    python -m unittest discover -s tests -v
    python tools/udrv_inspector.py --help
    python .github/scripts/check_readme_links.py
    python .github/scripts/check_readme_parity.py

Run the project-contract, federation, and schema validators used by CI when their related inputs change. Use small temporary fixtures rather than real driver packages for parser tests.

## Pull request expectations

Explain the evidence or workflow problem, how the change affects collected facts and derived observations, the limits applied to untrusted input, tests run, and any known false positives or unsupported formats.

## Security and review

Do not add driver installation, automatic remediation, payload extraction, or payload execution. Do not label a package safe or malicious based only on heuristic structure checks. Report security concerns through SECURITY.md and avoid publishing private device inventories or machine identifiers.
