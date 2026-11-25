# Quality and commercial readiness

The machine profile `quality-commercial.v1.json` contains 20 × 3 evidence controls.

| Gate | Required evidence |
|---|---|
| Quality | exact observations, tests, bounded parsing |
| Execution | repeatable inspection, export and recovery |
| Commercial | license, rights, support, delivery cost, demand |

Run `python tools/quality_commercial.py --format json`. A profile is not proof of sales, market fit or profitability.
