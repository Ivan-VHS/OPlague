# Inspection report composition

`tools/report_composer.py` combines existing read-only INF/ZIP inspection reports in input order.

| Limit/output | Contract |
|---|---|
| Reports | ≤256 |
| Total reported input | ≤64 GiB |
| Aggregates | packages, bytes, entries, expanded bytes, INF/catalog counts |
| Identity | canonical SHA-256 bundle fingerprint |
| Operation | local JSON composition only |

A digest identifies bytes, not publisher or compatibility. No package extraction, execution, install or system write occurs.
