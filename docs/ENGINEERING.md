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
