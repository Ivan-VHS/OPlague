# Device/Driver Compatibility Graph and Dry-Run

OPlague now has a read-only candidate-matching layer that connects local
Plug and Play inventory with hardware identifiers declared in inspected INF
`Models` sections.

## Evidence model

The graph only creates candidate edges when normalized hardware identifiers
match exactly. A prefix match, device-name similarity or package filename is
not enough. The parser records supported target architecture decorations and
can flag an architecture mismatch when a host architecture is supplied.

A graph edge means **"this INF declares an identifier also reported by this
device"**. It does not mean the driver is ranked, signed, trusted, compatible
with the current Windows build, or safe to install.

## Dry-run output

The `tools.device_graph.build_dry_run_plan` API and the desktop
**Compatibility & dry-run** tab produce a JSON report with:
- exact-ID candidate edges and the matched identifiers;
- architecture check outcome where known;
- devices for which no exact match was found;
- an explicit manual-review decision;
- safety fields `install_attempted=false` and `system_modified=false`.

The desktop flow requires a refreshed local inventory and at least one
inspected INF/ZIP containing hardware IDs. Individual and batch inspections
feed the same driver candidate catalogue.

## Mandatory gates before any future installation feature

An exact-ID match is only the first gate. A future deployment workflow must
separately validate:
1. Windows edition, build, architecture and target decoration applicability;
2. device instance, compatible-ID ordering, driver rank and current binding;
3. catalog signature, trust chain, revocation state and signing policy;
4. package provenance, payload hashes, INF directives and service configuration;
5. privilege boundary, pre-install snapshot, rollback strategy and post-install health.

No driver installation, staging, extraction, kernel loading, registry change or
network download is performed by this graph or its dry-run planner.

## Tests

`tests/test_device_graph.py` covers INF model extraction, exact identifier
matching, near-match rejection, architecture mismatch, dry-run invariants and
identifier normalization.
