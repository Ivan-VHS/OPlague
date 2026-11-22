# Reaper language integration

OPlague remains a read-only Windows device and package workbench. Reaper 0.2 provides an optional automation language for validating versioned snapshots, comparing normalized metrics, ranking the existing semantic profile catalogue and emitting a versioned JSON report.

## Executable example

\`automation/reaper/device_audit.rpr\` is the canonical integration script. It consumes two versioned OPlague snapshots, validates each through Reaper's built-in contract adapter, compares their metrics, runs read-only catalogue operations and writes \`build/reaper-oplage-report.json\`.

The test fixture generator \`automation/reaper/create_fixtures.py\` creates deterministic synthetic devices with fixed timestamps and a caller-managed test HMAC key. It does **not** invoke Windows PnP, inspect the CI host, read actual device identifiers or install/modify drivers.

Run from the OPlague repository root with the Reaper source checkout available:

\`\`\`sh
python automation/reaper/create_fixtures.py
PYTHONPATH=/path/to/Reaper python -m reaper --check automation/reaper/device_audit.rpr
PYTHONPATH=/path/to/Reaper python -m reaper --engine vm automation/reaper/device_audit.rpr
python -m tools.reaper_report build/reaper-oplage-report.json --json
\`\`\`

The same script is also executed using Reaper's tree-walk reference interpreter in the integration CI.

## Boundaries

- OPlague owns Windows PnP collection, INF/package analysis and device evidence.
- Reaper owns \`.rpr\` orchestration, bounded JSON import/export and schema-aware metric comparison.
- CI uses synthetic snapshots only; it never runs a device inventory.
- The comparison is read-only and does not certify compatibility, publisher trust or installation safety.
- Existing optional Reaper C17 / Pytyliki numerical bridge remains separate from the Reaper 0.2 scripting runtime.
- C17 is still a partial native Reaper compiler track; this workflow executes the Python reference VM.
