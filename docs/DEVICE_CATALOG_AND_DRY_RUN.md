# Device catalogue, snapshots, compatibility evidence, and dry-run plans

## Implemented scope

This layer extends the existing read-only Windows inventory, INF/ZIP inspection,
SHA-256 reporting, UDRV inspector, exact-ID compatibility graph, and Device
Metric Lab. It does not replace those components and does not install or stage
drivers.

### PnP inventory

\`tools/pnp_inventory.py\` queries the local PnP device tree through a fixed
PowerShell script and normalizes:

- instance ID, friendly name, class and class GUID;
- Hardware IDs and Compatible IDs, preserving source order;
- manufacturer, parent instance, service, current driver provider/version/date;
- PnP status, Problem code and present/not-present state.

The query is read-only. \`normalize_pnp_devices()\` is platform-independent and
can be tested with synthetic PowerShell JSON. The GUI uses the same inventory
adapter from a background worker; it does not execute any text from device
properties or block the Tk event loop while querying devices.

### INF evidence and compatibility

\`tools/inf_catalog.py\` extracts [Version] metadata and directly declared IDs
from [Manufacturer] and its model sections. It supports decorated model
section names and line continuations. \`tools/driver_compatibility.py\` compares
that parsed evidence with Hardware IDs and Compatible IDs. An exact Hardware
ID match ranks above an exact Compatible ID match; original PnP ID order is
retained. The score is an OPlague evidence ordering, **not** Windows SetupAPI
driver rank and not an installability guarantee.

The parser deliberately does not evaluate Include/Needs, arbitrary
%Strings% substitutions, co-installers, registry/service side effects or
complex OS applicability expressions. The existing bipartite graph in
\`tools/device_graph.py\` remains the desktop candidate view; the new evidence
index provides a more explicit parser/ranker for CLI and policy plans.

### Versioned registry and snapshots

\`tools/device_registry.py\` provides the \`oplage.device-registry\` v1 schema,
strict duplicate-key rejection, duplicate-identity checks, bounded arrays,
atomic replacement when saving JSON, and content-addressed snapshots. A
registry has current \`devices\`, \`packages\`, and a \`snapshots\` history.
\`create_snapshot()\` creates a SHA-256 snapshot ID; \`append_snapshot()\` adds
it to history and refreshes the current inventory/package view.
\`snapshot_diff()\` reports added, removed, and changed devices/packages plus
numeric metric deltas.

The JSON Schema is published at
\`schemas/device-registry-v1.schema.json\`. Future incompatible schema changes
must use a new version and an explicit migration; v1 readers reject unknown
versions rather than silently reinterpreting them. The desktop Registry tab
can capture a snapshot, validate a registry, and compare the newest snapshots
from two registry files.

### Policy-gated dry-run and freshness guard

\`tools/dry_run.py\` creates a per-device JSON operation plan for \`install\`,
\`update\`, or \`rollback\`. It requires a stable device identity, package
SHA-256, direct match evidence tied to both the selected device IDs and the
IDs declared by the selected INF, completed package audit, and a signature
state. By default, unknown or unsigned signatures block the plan. A
Compatible-ID-only match remains review-required.

The plan contains a digest over its contents and preconditions for the package
hash, device instance ID and inventory revision. \`check_plan_freshness()\`
detects stale or tampered plans and also rejects blocked plans or documents
that violate the non-applying contract.

A plan always has \`will_modify_system: false\` and
\`execution_supported: false\`. There is intentionally no \`apply()\` function
in this release. \`signature_status="trusted"\` is an evidence input, not
something this module verifies; callers must only use it after a platform-backed
trust check such as WinVerifyTrust/catalog verification has actually succeeded.
The desktop Compatibility tab retains the graph-based candidate plan and also
offers loading a strict policy-gated plan from JSON.

## CLI

Run from the repository root:

\`\`\`powershell
python -m tools.oplague_cli registry init registry.json
python -m tools.oplague_cli registry validate registry.json
python -m tools.oplague_cli snapshot create registry.json snapshot-input.json --label baseline
python -m tools.oplague_cli snapshot diff before.json after.json
python -m tools.oplague_cli inf inspect path\to\driver.inf
python -m tools.oplague_cli compatibility device.json candidates.json
python -m tools.oplague_cli dry-run plan plan-input.json
python -m tools.oplague_cli dry-run freshness plan.json --current-digest <sha256> --current-device <instance-id> --current-revision 12
\`\`\`

\`registry init\` refuses to overwrite an existing file. Snapshot input is a
JSON object with optional \`devices\`, \`packages\`, \`metrics\` and \`captured_at\`
fields. Dry-run plan input is a JSON object with \`device\`, \`package\`, and
\`match\` objects, plus optional operation, audit, signature and policy fields.
The package must include \`device_ids\` extracted from its INF and match evidence
must include both \`matched_device_id\` and \`matched_inf_id\`.

The plan command emits complete JSON. Exit code \`2\` means the plan is blocked;
\`0\` means the plan was produced for operator review, not that an installation
occurred. The freshness command returns exit code \`3\` for stale or tampered
plans. \`registry init\` creates an empty v1 registry, and \`snapshot create\`
atomically appends a content-addressed snapshot.

## Safety boundary and next stages

- Scanning and analysis remain read-only and do not unpack or execute foreign payloads.
- A Compatible ID is weaker evidence than an exact Hardware ID match.
- SHA-256 establishes byte identity, not publisher authenticity.
- The parser's declared-ID coverage is intentionally conservative; unsupported INF constructs are reported, not guessed.
- The current signature field is a policy/evidence boundary, not a verifier. A dedicated Windows trust adapter must use platform verification APIs and retain certificate/catalog evidence.
- Windows SetupAPI rank, target OS/build validation and architecture policy need dedicated platform-backed checks.
- UDRV staging, SetupAPI installation, rollback, reboot coordination and post-install PnP verification remain unimplemented. They must be separate modules with explicit elevation, approval, recovery checkpoints and postcondition checks.

## Tests

\`\`\`powershell
python -m unittest discover -s tests -v
\`\`\`

The tests cover INF parsing/matching, PnP normalization, registry validation and
atomic round trips, snapshot diffs, dry-run policy gates, stale-plan detection,
and CLI JSON behaviour. Windows PowerShell execution itself must additionally
be smoke-tested on supported Windows builds.
