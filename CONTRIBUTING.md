# Contributing to OPlague

OPlague is a local Windows device/driver evidence workbench with a separate, reversible gaming power-plan workflow. Contributions must preserve bounded inspection, clear evidence provenance and safe system boundaries.

## Before opening a pull request

1. Use synthetic or sanitized fixtures; remove serial numbers, private paths and personal identifiers.
2. Keep INF/ZIP/UDRV inspection metadata-only and bounded. Do not extract or execute driver payloads.
3. Do not add driver installation, removal, service control, registry mutation, firmware changes or privileged host writes.
4. Treat exact hardware-ID matches as candidates, not compatibility or safety verdicts.
5. Keep gaming-session system changes explicit, snapshot-backed and guarded on restore.
6. Update the English, Ukrainian, Russian and Simplified Chinese documentation when public behavior changes.

## Local verification

~~~sh
python -m compileall -q oplague_app.py oplage_app.py tests
python tools/validate_visual_canon.py ui_theme.py
python -m unittest discover -s tests -v
python -m oplague --verify
git diff --check
~~~

For UDRV changes, also run the relevant inspector tests and validate against the versioned schema.

## Pull request expectations

Describe the input format, bounds, evidence source, safety implications, platform limitations and test cases. Label desktop screenshots and authored architecture illustrations accurately. Keep docs aligned with [FEATURES.md](docs/FEATURES.md) and [DOCUMENTATION_CONTROL.md](docs/DOCUMENTATION_CONTROL.md).

## Security

Do not submit private driver packages or identifying hardware data. See [SECURITY.md](SECURITY.md) for reporting guidance.
