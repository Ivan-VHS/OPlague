# Feature matrix

| Module | Output | Boundary |
|---|---|---|
| Inventory | PnP IDs, status, manufacturer | read-only |
| INF/ZIP | metadata, paths, SHA-256 and archive-risk triage | no extraction/execution; risk indicators are not malware verdicts |
| Authenticode | Windows signature status, signer and timestamp metadata | selected files only; no install/load or safety verdict |
| Architecture | x86/amd64/arm/arm64/ia64 mapping | target evidence |
| Compatibility | exact normalized hardware-ID edges | candidate only |
| UDRV v1 | manifest, file sizes, SHA-256 | no install/load |
| Batch reports | ordered summaries and fingerprint | local only |
| DRIVE-LENS | HMAC pseudonyms and provenance | no verdict |
| Snapshots | versioned device JSON | offline compare |
| Metrics | weighted distance, cosine, variance | supplied values |
| Clinical Systems | 120 principles, 36 executable checks | advisory only |
| Reaper | manifest/snapshot exchange | versioned JSON |
| Pytyliki | native metric cross-check | explicit trusted library |

No feature certifies a driver or changes device state.
