# Clinical Systems Reliability — CSR-120

Advisory engineering catalogue; not a medical or diagnostic product.

| Item | Count |
|---|---:|
| Principles | 120 (CSR-001…CSR-120) |
| Domains | 8 |
| Executable telemetry checks | 36 |
| Input/output | JSON / csr-120/v1 |
| Exit codes | 0 healthy/catalog · 1 findings · 2 invalid/error |

| IDs | Domain |
|---|---|
| 001–015 | Transport |
| 016–030 | Signals |
| 031–045 | Homeostasis |
| 046–060 | Defense |
| 061–075 | Dosing |
| 076–090 | Lifecycle |
| 091–105 | Diagnostics |
| 106–120 | Operator |

Run: `python tools/clinical_systems.py --catalog --pretty` or `python tools/clinical_systems.py telemetry.json --pretty`. A registry entry without one of 36 checks is a design concept, not an implemented detector.
