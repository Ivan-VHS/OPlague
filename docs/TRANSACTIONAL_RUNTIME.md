# Evidence Snapshot Transaction Contract v1

OPlague provides `EvidenceTransaction` in `oplague.transactions` for bounded transformations of caller-owned JSON evidence and report objects.

## Safety boundary

OPlague remains a **read-only** workbench for devices, driver packages and inspected workspaces. The transaction class changes only a staged copy in process memory. Committing creates a new in-memory report snapshot; it never writes files, registry entries, driver packages, drivers, firmware, device state or hardware registers.

## Operation map

| Operation | API | Meaning |
|---|---|---|
| `patch` | `tx.patch(path, value)` | Replace an existing nested report field |
| `rebind` | `tx.rebind(evidence_id, value)` | Attach an evidence value to the in-memory report |
| `remap` | `tx.remap({old: new})` | Rename report keys with collision checks |
| `hotSwap` | `tx.hot_swap(report)` | Replace the staged report draft |
| `migrate` | `tx.migrate(schema, transform)` | Apply a monotonic report-schema migration |
| `flash` / `reflash` | `tx.flash()`, `tx.reflash()` | Commit a report snapshot in memory |
| `rollback` | `tx.rollback()` | Restore the last committed report and schema |
| `sync` | `tx.sync()` | Commit against the current generation |
| `async` / `await` | `await tx.async_flash()` | Commit off the event loop and await the snapshot |
| `emit` / `yield` | `tx.emit(name)`, `tx.yield_checkpoint(label)` | Emit an audit event/checkpoint |
| `throw` / `catch` | `tx.throw(message)`, `EvidenceTransaction.catch(fn)` | Raise/capture a transition error |
| `panic` / `assert` | `tx.panic(message)`, `EvidenceTransaction.assert_condition(...)` | Enforce guarded failure/invariants |
| `return` | `EvidenceTransaction.return_value(value)` | Pass a value through |

## Integrity and bounds

Default payload limit is 8 MiB. Snapshots use canonical JSON and SHA-256, migrations require a higher schema version, and stale generation numbers raise `EvidenceConflict`. The report snapshot's timestamp, device identity and source digest remain caller-supplied evidence; the transaction layer does not invent provenance or establish driver authenticity.

## Tests

Run `python -m unittest discover -s tests -p "test_transactions.py" -v`.
