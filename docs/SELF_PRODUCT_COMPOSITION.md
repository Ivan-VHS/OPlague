# Vertical Self-Product

OPlague lifts its own device/driver candidate graph through repeated boolean
matrix squaring. It is a read-only relationship-analysis operation.

For the initial adjacency matrix A, each level computes A(k+1)=A(k)×A(k)
over the boolean semiring: AND combines a path segment and OR combines
alternative paths. Level 1 therefore reports paths of length 2; level 2
reports paths of length 4. A device-to-device relation can show that two
devices share an exact-ID candidate driver path.

## Evidence and limits

- API: vertical_self_product in tools/self_product.py.
- Only edges marked exact_identifier_candidate participate. Architecture
  mismatches are excluded.
- Node count is limited to 256, input edges to 32,768, and depth to 8.
- The full relation count is reported, but at most 4,096 pair details are
  emitted per layer.
- Node IDs are represented by stable SHA-256 references in the report; raw
  PnP identifiers are not copied into the output. These references remain
  linkable pseudonyms, not anonymization.
- A path is discovery evidence only. It is not a driver compatibility verdict,
  ranking, signature check, trust decision or installation instruction.
- The operation does not install, remove, enable, disable or modify drivers or
  device state.

## Verification

tests/test_self_product.py covers shared exact-candidate paths, self-loops,
architecture mismatch exclusion, vertical path lengths, identifier handling
and resource limits.
