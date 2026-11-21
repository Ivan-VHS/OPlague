# Architecture

| Stage | Responsibility |
|---|---|
| Inventory | read Windows Plug and Play identity/status |
| Inspect | bounded INF/ZIP metadata parsing |
| Validate | paths, size, architecture, hashes |
| Match | exact normalized hardware IDs |
| Analyze | user-supplied normalized metrics |
| Report | evidence, unknowns, manual-review flag |
| Export | explicit confirmation; versioned JSON |

Flow: local input → bounded parser → evidence record → dry-run report. Package payloads are never extracted, executed, installed or loaded. Linux/macOS can inspect saved data; live PnP collection is Windows-only.
