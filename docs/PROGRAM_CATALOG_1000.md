# OPlague catalogue implementation map

This repository owns the read-only device, driver-package, binary-header and supply-chain evidence portion of the shared 1,000-item adoption catalogue.

## Catalogue ownership

| Catalogue IDs | Subject area | OPlague treatment |
|---|---|---|
| 501–560 | Windows system utilities, device APIs, INF and driver trust | PnP inventory, INF/UDRV parsing, Authenticode evidence and hardware-ID matching |
| 561–600 | Linux and macOS device discovery | Imported evidence and platform-specific source adapters; unavailable sources stay unknown |
| 601–650 | Archives and binary analysis | Bounded ZIP/INF inspection and the new PE/COFF header reader |
| 651–700 | Signatures, SBOM, hashes and supply-chain assurance | Local signature evidence, hash verification, SPDX file inventory and licence-policy inputs |

## First implementation wave

- **PE/COFF header inspection** — `tools/pe_inspector.py` reads the DOS header, PE signature, COFF machine, PE32/PE32+ optional header, sections and certificate-table directory. It never maps or executes the image. A certificate-table directory is reported as metadata, not as a verified signature.
- **SPDX 2.3 file inventory** — `tools/sbom_inventory.py` creates a reproducible local file inventory with SHA-256 checksums, stable SPDX identifiers and explicit `NOASSERTION` licence fields. It is not a dependency resolver and does not infer licences from filenames.
- **Provenance boundary** — the inventory namespace is derived from both canonical relative paths and file hashes. A hash establishes the observed bytes, not author identity, legal ownership or permission to redistribute.

## Adoption rules

1. Driver installation, firmware flashing, module loading and system writes remain outside OPlague.
2. Package and binary inputs are parsed as data only; untrusted scripts and embedded payloads are never executed.
3. A PE certificate directory is not a trust result. Authenticode verification remains a separate platform-backed inspection.
4. SPDX `NOASSERTION` is retained when licence evidence has not been collected. A content hash proves file identity, not authorship or usage rights.
5. Inventory size, per-file size, recursion and archive expansion limits are checked before large reads.
6. Third-party code is not copied into this Apache-2.0 repository; formats and independently implemented parsers are used instead.

Each feature is called implemented only after its parser and boundary tests pass in CI.


The file inventory is intentionally offline. It does not query OSV, VirusTotal, LOLDrivers or any other remote feed. Network-backed vulnerability and reputation checks require a separate explicit integration, current signed data and a recorded source timestamp.