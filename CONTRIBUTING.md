# Contributing to OPlague

OPlague is a local, read-only Windows device and driver evidence workbench. Keep observations separate from conclusions, and keep dry-run planning separate from system changes.

## Before opening a pull request

1. Provide a minimal INF, ZIP metadata or synthetic hardware-ID fixture. Remove serial numbers and other personal identifiers.
2. Keep package inspection bounded and metadata-only. Never extract or execute submitted driver payloads during analysis.
3. Do not add driver installation, removal, service control, registry edits, firmware changes or privileged host mutation.
4. Exact ID matches are candidates, not proof of compatibility or safety. Structural heuristics are not malware verdicts.
5. Add deterministic tests and document input limits and known false positives.

## Local verification

```sh
python -m unittest discover -s tests -v
python tools/hardware_id_lint.py "PCI\VEN_8086&DEV_15F3" --json
python tools/validate_project_contract.py
```

## Pull request expectations

Describe evidence sources, resource limits, privacy handling and the exact scope of each conclusion. Do not include live machine serials, private inventory exports or proprietary driver payloads. Avoid issue-closing keywords in PR descriptions; maintainers close issues after review.
