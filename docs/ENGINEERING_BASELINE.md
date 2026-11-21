# Engineering Baseline

**Status:** normative  
**Product:** OPlague Windows driver workbench

## Product boundary

OPlague provides read-only Windows device inventory, bounded driver-package inspection, evidence reporting and offline comparison. It is not a driver installer, device configurator, firmware utility or publisher-trust authority.

## Required behavior

- Live Plug and Play inventory MUST remain read-only. Documented workflows MUST NOT install, remove, enable, disable, roll back or modify a driver or device.
- INF, ZIP, UDRV and imported metadata MUST be treated as untrusted input. Inspection MUST enforce path, entry-count, byte-size, decompression and parsing limits before processing.
- Package payloads MUST NOT be extracted or executed by the inspection workflow.
- Compatibility candidates MUST be created only from exact normalized hardware-identifier matches. A candidate MUST NOT be represented as a compatibility verdict, ranking or installation recommendation.
- Missing evidence MUST remain missing. Hashes establish byte integrity, not publisher identity, signing trust, safety or compatibility.
- Device pseudonyms MUST be described as pseudonyms. HMAC-based identifiers can remain linkable when a protected key is intentionally reused; they are not anonymous data.
- Native interoperability MUST be opt-in and require an explicit trusted library path. Loading a native library executes trusted code in-process.

## Data and evidence contract

Device snapshots and inspection bundles MUST use versioned schemas. Consumers MUST validate schema version, record shape, normalized dimensions and canonical fingerprints before use. Reports MUST preserve conflicts and provenance rather than silently selecting an unsupported conclusion.

## Integration contract

Cross-project communication MUST use published versioned JSON formats or an explicitly documented ABI. Consumers MUST NOT depend on private module layouts or implicit native-library loading. Integration permissions MUST NOT expand the local product's read-only device boundary.

## Verification

Tests and the checked-in implementation determine shipped capability. Documentation MUST distinguish inspected metadata, simulated behavior, candidate evidence and unsupported actions. Any change to a data contract requires schema validation and regression tests.
