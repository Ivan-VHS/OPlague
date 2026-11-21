# Human-first governance for local device inventory

Status: implemented for device-snapshot export and pseudonymous identity handling. OPlague remains a read-only driver diagnostics workbench, not an EHR, medical device, clinical decision system, or legal compliance product.

## Implemented behavior

1. **Explicit export consent:** the snapshot CLI refuses to query and export the local PnP inventory unless the operator passes the explicit acknowledgement flag. The Python export API also requires user_confirmed=True.
2. **Protected identifiers:** raw PnP instance IDs are represented by HMAC-SHA-256 pseudonyms, not unkeyed hashes. With no key file, every export uses a fresh random in-memory key, preventing deterministic cross-export matching. The key is never included in the snapshot.
3. **Controlled correlation:** an operator may supply a protected local key file (minimum 32 bytes) to create stable pseudonyms across snapshots. That enables comparison but also makes records linkable to anyone who can use the key; protect it and do not commit it.
4. **Bounded inputs:** identity-key files must be regular, non-symlink files and are limited to 4096 bytes. Keys shorter than 32 bytes are rejected.
5. **Read-only invariant:** PnP collection remains a fixed non-mutating query. No driver install, disable, firmware operation, package execution, or automatic compatibility verdict is added.

## Usage

    python -m tools.federation snapshot --confirm-inventory-export
    python -m tools.federation snapshot --confirm-inventory-export --identity-key-file path/to/private-identity.key --output device-snapshot.json

The confirmation is required because a snapshot includes local device names, classes, status data and pseudonymous identifiers. Use an access-controlled destination for exported reports.

## Scope crosswalk

| Medical-rights concept | OPlague implementation / boundary |
|---|---|
| Informed consent | Explicit opt-in before inventory export; purpose is local diagnostics |
| Consent withdrawal | Stop future exports; previously exported files remain under operator control |
| Confidentiality / minimization | Keyed pseudonyms; ephemeral by default; bounded exported data |
| Access audit | Snapshot digest and deterministic metadata provide integrity checks, not access audit |
| Erasure / retention | No secure-erasure promise; operator controls local file retention |
| Clinical quality, prescribing, research and SaMD | Not applicable; no patient data or clinical decisions are processed |
| Human oversight | Read-only inspection and dry-run matching only; no driver action |

## Security limitations

HMAC pseudonymization is not anonymization. Stable pseudonyms are intentionally linkable across exports that use the same key. The snapshot hash is an integrity fingerprint, not a vendor signature, trusted timestamp, or proof that input data is true. The CLI confirmation is an operator acknowledgement, not identity proofing or legal consent on behalf of another person. Storage encryption, MFA, HSM-backed key management, remote access audit, and jurisdictional controls belong to the deploying environment.
