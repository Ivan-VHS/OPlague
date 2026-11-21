# Correction / coverage / defect matrix

The profile `quality-remediation.v1.json` preserves 20 canonical triplets.

| Stage | Acceptance |
|---|---|
| Detect | reproducible input and expected/actual result |
| Diagnose | confirmed root cause |
| Correct | smallest coherent patch |
| Cover | regression + boundary tests |
| Verify | CI and evidence paths |
| Close | review, limitation, rollback note |

Run `python tools/quality_remediation.py --format json`. “Complete coverage” never means unbounded processing.
