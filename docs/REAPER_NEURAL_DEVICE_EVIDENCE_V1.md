# OPlague Reaper Neural Device Evidence Policy v1

**Adapter:** integrations/reaper/neural_driver_policy.rpr  
**Status:** local read-only evidence triage; manual review only

## Evidence envelope

The eight-field record uses oplague.neural-device-evidence.v1 and contains:

1. schema identifier;
2. device identity;
3. driver-package identity;
4. source: local_inventory or local_manifest;
5. signature-verification result supplied as a boolean;
6. compatibility score in permille (0–1000);
7. anomaly count (0–10,000);
8. driver-install intent.

The policy rejects remote evidence and malformed values. Unsigned or anomalous evidence is quarantined. Driver-install intent is blocked. Even verified, high-compatibility, anomaly-free evidence is only eligible for MANUAL_REVIEW; no automatic action is authorized.

## Fixed safety properties

Every result is local-only and read-only. Driver installation and firmware writes remain false. The contract does not verify a signature itself: it consumes a signature result supplied by a trusted existing evidence stage. A compatibility score is evidence, not certification.

## Verification

The OPlague Reaper integration workflow checks and executes this file and requires OPLAGUE_REAPER_NEURAL_POLICY:PASS. The fixture covers valid local evidence, unsigned evidence, anomalies, install intent, remote evidence and malformed input.
