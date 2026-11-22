# 1,000-program adoption map: OPlague

This file assigns the device, driver, package-inspection and supply-chain portion of the supplied catalogue. OPlague remains read-only; the catalogue does not authorize installation or kernel mutation.

## Ownership within the catalogue

| Catalogue IDs | Original subject area | OPlague treatment |
|---|---|---|
| 501–560 | Windows system utilities, PnP, INF, WDK, signatures and driver state | Local inventory, INF/CAT metadata, event evidence and signature status |
| 561–600 | Linux/macOS hardware and driver tools | Optional read-only source adapters only when available and testable |
| 601–650 | Archives, binary formats, PE/ELF/Mach-O and forensic tools | Bounded metadata inspection, path/size/type checks and binary header readers |
| 651–700 | Signing, SBOM, vulnerability and supply-chain tools | Local hashes, provenance manifests, license/dependency checks and opt-in advisory scans |

## First implementation wave

- **Archive Risk Triage** — ZIP metadata now reports case-insensitive duplicate paths, symbolic links, encrypted entries, script candidates, loadable-binary candidates and nested archive candidates.
- Findings are triage signals only. Existing path traversal, entry-count, expanded-size and compression-ratio guards still fail closed. No archive entry is extracted or executed.

## Adoption rules

1. Device discovery and package analysis are read-only. No SetupAPI install, driver store mutation, firmware flash, service/registry write or system policy change.
2. A detected .sys, .dll, .exe, script, nested archive or signature is a metadata fact, not a malware verdict or proof of safety.
3. Signature checks must report the trust provider, chain result and timestamp limitations. A missing signature is not silently inferred from a file name.
4. Vulnerability feeds, VirusTotal and cloud scanners are not contacted automatically. Any external lookup must be explicit, optional and documented.
5. Raw hardware IDs, serials, paths and account names are protected or redacted before export. Evidence provenance and hashes remain attached.
6. GPL/copyleft source is not copied into the Apache-2.0 project; only compatible APIs, file formats and independently implemented ideas are adopted.

## Remaining backlog themes

The 501–560 cluster prioritizes SetupAPI/CfgMgr32 read-only inventory, PnP event correlation, device-tree views and Authenticode evidence. The 561–600 cluster prioritizes sysfs, IOKit and Linux module adapters behind platform capability gates. The 601–650 cluster prioritizes CAB/MSI metadata parsing, PE import/section summaries, archive nesting limits, duplicate-path and symlink triage. The 651–700 cluster prioritizes SBOM export, signed provenance, license manifests, vulnerable-driver hash lookups from local databases and reproducible archive comparison.

Nothing in this backlog turns OPlague into a driver installer.
