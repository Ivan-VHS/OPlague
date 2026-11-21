# Engineering gates

| # | Gate | Acceptance |
|---:|---|---|
| 1 | Read-only | no driver install/load or registry/device writes |
| 2 | Untrusted input | parse metadata; never execute package payloads |
| 3 | Exact evidence | normalize identifiers; require exact matches |
| 4 | Resource bounds | cap entries, bytes, paths, rows and hash buffers |
| 5 | Trust | separate byte integrity, signature and compatibility |
| 6 | Privacy | minimize exports; explain pseudonymization |
| 7 | Release | tests, schemas, reproducible commands, license |

A future deployment feature requires a separate threat model, signing policy, explicit confirmation, rollback design and tests.

## Shared evolution matrix

This repository adopts the shared [Engineering Evolution Framework](ENGINEERING_EVOLUTION_FRAMEWORK.md): 20 domains, 40 practices, a versioned JSON contract and negative tests. The framework complements existing engineering, project and safety contracts; it does not assert that every technique is applicable or already implemented. Claims of implementation must remain backed by local code, tests or operational evidence.
