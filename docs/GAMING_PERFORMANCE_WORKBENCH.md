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

## Start

Use the "Игровая лаборатория" button in the OPlague desktop header. The workbench can capture a system snapshot, start a temporary power-profile session, restore it and compare two frame-time CSV files.

The profile cache API is available in tools/game_optimizer.py for future profile editors and Mora IPC integration.

## Safety boundaries

This feature does not install, replace, patch, load, unload or download drivers. It does not edit registry keys, BIOS/UEFI settings, voltage/frequency curves, IRQ/MSI affinity, CPU core parking, network settings, services or anti-cheat-sensitive process priorities. It never disables security software. No third-party driver aggregator or untrusted download endpoint is used.

Temperature, VRAM, GPU-engine, WHEA and sensor readings are not fabricated. This release does not provide a sensor backend or an embedded PresentMon capture process; import genuine CSV output from a compatible local telemetry tool. A CSV regression is advisory and does not automatically prove causation. The UI asks the operator to finish the session and restore; it does not change settings based on a single noisy sample.

A power-plan switch is a real system change. OPlague snapshots the previous plan before switching, offers an explicit restore action, and restores only while the active plan is still the plan it set. Driver payload backups and Windows restore points are outside this feature because this workbench does not perform driver deployment.

## Verification

    python -m unittest tests.test_game_optimizer -v

The tests cover exact hardware-ID normalization, PCI/USB identity fields, stable fingerprints, atomic snapshots, power-scheme parsing and validation, bounded CSV analysis, regression thresholds and exact-tuple profile caching.
