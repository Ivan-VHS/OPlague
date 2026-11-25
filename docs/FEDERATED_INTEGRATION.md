# Federated integration

| Peer | Transport | Boundary |
|---|---|---|
| Reaper | versioned device-snapshot JSON | explicit file exchange |
| Pytyliki | C ABI v1 | caller-selected trusted library |
| VentuSample | pack-manifest JSON | metadata only |

Validate schemas, versions, bounds and provenance. No implicit DLL/SO lookup, network service, driver operation or audio render request.
