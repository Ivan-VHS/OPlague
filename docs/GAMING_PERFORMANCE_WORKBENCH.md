# Gaming Performance Workbench

OPlague's gaming workbench extends the existing read-only device and driver inspector with reversible session management and benchmark evidence. It is a local Windows desktop feature; saved files and CSV reports can also be reviewed on other platforms.

## Included behavior

- Reads full Plug and Play IDs and joins them with Windows signed-driver metadata: provider, version, date, INF, IsSigned and Signer. The exact normalized hardware ID remains intact; vendor-only matches are not promoted to exact matches.
- Creates an atomic local JSON snapshot before a game session. It records the host, hardware/driver metadata, active power-scheme GUID and a SHA-256 hardware fingerprint. It does not copy driver binaries or modify the driver store.
- Starts a temporary session using a built-in Windows power scheme (SCHEME_MIN or SCHEME_BALANCED) and restores the previous scheme afterwards.
- Avoids clobbering a power-plan change made by the user or another application while the session is active. In that case restore is skipped and reported.
- Imports PresentMon-compatible CSV frame-time columns, reporting mean FPS, 1% low, 0.1% low, median frame time and p99 frame time.
- Compares benchmark summaries and flags configurable regressions. The operator must choose the same game, scene, resolution and test duration; noisy or non-repeatable runs are not evidence of a driver improvement.
- Caches only operator-confirmed game profiles keyed by exact hardware fingerprint, driver version and game identifier. The cache is local and bounded to 250 profiles.

## Coverage of the 15 requested rules

| Rule | Current implementation |
|---|---|
| 1. Exact hardware identity | Implemented for full normalized PCI/USB and other PnP instance paths; PCI/USB vendor, device, subsystem and revision fields are extracted. |
| 2. Snapshot and rollback | Partial: atomically snapshots hardware/driver metadata and the power plan; guarded power-plan restore is implemented. Driver-store backup and Windows restore-point creation are not implemented because this release never deploys drivers. |
| 3. Trusted driver sources | Partial: the existing inspector supports local INF/ZIP metadata and Authenticode inspection. It does not download or install driver packages. |
| 4. Driver-only installation | Not enabled: there is no driver installer or background component remover. |
| 5. OS/architecture compatibility | Partial: existing INF target architecture and exact-ID analysis remain available. A per-game DX11/DX12/Vulkan/anti-cheat compatibility database is not included. |
| 6. Safe driver overrides | Partial: only operator-selected power mode and local profile metadata are supported. Driver binaries are never patched; no registry/environment/third-party wrapper settings are changed. |
| 7. Power and boost profiles | Partial: a built-in Windows High Performance plan may be enabled for a session after a snapshot and restored afterwards. CPU/GPU frequency, voltage, PCIe, memory and core-parking controls are not changed. |
| 8. Interrupt and I/O tuning | Not enabled: IRQ/MSI affinity and queue-depth changes are intentionally excluded. |
| 9. Memory and shader cache | Not enabled: no VRAM, paging-file or vendor shader-cache controls are changed. |
| 10. Thermal safeguards | Not enabled: this release has no verified sensor/fan/VRM provider. Missing temperatures are never guessed and no fan curve or overclock is applied. |
| 11. Background process isolation | Not enabled: no service, updater, security process or background application is terminated or suspended. |
| 12. Network tuning | Not enabled: MTU, adapter power, queue and protocol settings remain untouched. |
| 13. Adaptive game profiles | Partial: local profiles are keyed to exact game ID, hardware fingerprint and driver version and require operator validation. Automatic game detection and genre/refresh-rate policy selection are not included. |
| 14. 1%/0.1% low and rollback | Implemented for imported measured CSV captures: average FPS, 1%/0.1% low (0.1% only with at least 1,000 frames), median and p99 frametime. Threshold regression attempts guarded restoration of the OPlague power-plan session. WHEA/GPU reset and sensor telemetry are not integrated. |
| 15. Local learning cache | Implemented as a bounded, local cache of operator-confirmed exact-match profiles; it does not learn from unverified or mismatched hardware/game tuples. |

The intentionally disabled items need hardware-specific providers, repeatable validation and platform-native permission/rollback implementations. They must not be simulated with guessed metrics or generic registry tweaks.
 
## Start

Use the "Игровая лаборатория" button in the OPlague desktop header. The workbench can capture a system snapshot, start a temporary power-profile session, restore it and compare two frame-time CSV files.

The profile cache API is available in tools/game_optimizer.py for future profile editors and Mora IPC integration.

## Safety boundaries

This feature does not install, replace, patch, load, unload or download drivers. It does not edit registry keys, BIOS/UEFI settings, voltage/frequency curves, IRQ/MSI affinity, CPU core parking, network settings, services or anti-cheat-sensitive process priorities. It never disables security software. No third-party driver aggregator or untrusted download endpoint is used.

Temperature, VRAM, GPU-engine, WHEA and sensor readings are not fabricated. This release does not provide a sensor backend or an embedded PresentMon capture process; import genuine CSV output from a compatible local telemetry tool. A CSV regression is advisory and does not automatically prove causation. When a compared run crosses a regression threshold, the UI attempts to restore the active OPlague session's previous power plan. The restore guard leaves the system untouched if another application or the user changed the active plan. No automatic driver rollback is attempted.

A power-plan switch is a real system change. OPlague snapshots the previous plan before switching, offers an explicit restore action, and restores only while the active plan is still the plan it set. Driver payload backups and Windows restore points are outside this feature because this workbench does not perform driver deployment.

## Verification

    python -m unittest tests.test_game_optimizer -v

The tests cover exact hardware-ID normalization (including instance-path segments), PCI/USB identity fields, stable fingerprints, atomic snapshots, power-scheme parsing and validation, bounded CSV analysis, percentile sample sufficiency, regression thresholds and exact-tuple profile caching.
