# OPlague Hardware & Game Performance Stack

The stack joins OPlague's existing device and driver evidence tools into one Windows hardware profile and game-performance report. It contains 15 subsystems and emits a versioned JSON report. Live collection is Windows-only; saved snapshots can be analysed on other platforms.

## The 15 subsystems

| # | Subsystem | Implemented behavior |
|---:|---|---|
| 1 | Host inventory | Windows edition/build, architecture, platform manufacturer and model |
| 2 | Firmware / UEFI | SMBIOS BIOS vendor/version/date, Secure Boot and TPM presence; read-only |
| 3 | CPU topology | Processor model, cores, logical processors, reported clock and load |
| 4 | Memory topology | Installed capacity, available memory and DIMM speed metadata |
| 5 | GPU inventory | Adapters, driver version/date, current resolution and refresh rate |
| 6 | PnP / bus inventory | Present devices, PCI/USB/ACPI/HID bus counts and exact IDs in local memory |
| 7 | Driver inventory | Bound driver packages, provider, version and INF name |
| 8 | Device health | Configuration Manager problem codes and known diagnostic descriptions |
| 9 | Windows Update discovery | Opt-in search for offered driver updates; search metadata only |
| 10 | Driver compatibility | Exact hardware-ID candidate graph using the existing device graph matcher |
| 11 | Signature evidence | OS-reported IsSigned; certificate-chain trust is not inferred |
| 12 | Thermal watchdog | ACPI thermal-zone values when firmware exposes them |
| 13 | Power policy | Active scheme and battery state; no policy changes |
| 14 | Game runtime | Configurable process detection and CPU-time/working-set snapshot |
| 15 | Game performance planner | Average FPS, 1% low, optional 0.1% low and frame-time percentiles |

## Usage

\`\`\`powershell
# Local Windows inventory; exact hardware IDs are redacted in the report
python -m tools.hardware_game_stack --output reports/hardware-game-stack.json

# Optional Windows Update driver discovery (network search only)
python -m tools.hardware_game_stack --discover-windows-update-drivers --output reports/driver-candidates.json

# Analyse a saved snapshot on Windows, Linux or macOS
python -m tools.hardware_game_stack --snapshot hardware-snapshot.json

# Supply a local, manually curated exact-ID driver catalogue
python -m tools.hardware_game_stack --snapshot hardware-snapshot.json --driver-catalog driver-catalog.json

# Add benchmark samples and a game process name
python -m tools.hardware_game_stack --snapshot hardware-snapshot.json --benchmark benchmark.json --game MyGame-Win64-Shipping

# Include exact hardware IDs only for a deliberate local diagnostic export
python -m tools.hardware_game_stack --snapshot hardware-snapshot.json --include-hardware-ids
\`\`\`

Benchmark JSON accepts frame_times_ms or fps_samples. Compare captures made in the same scene, resolution, graphics preset, driver version, power source and background workload. A 1% low is a diagnostic metric, not a promise of a particular game frame rate.

## Safety and compatibility

The collector uses fixed PowerShell/CIM/PnP queries and optional Windows Update Agent search. It does not execute INF directives or package payloads. It does not download, stage, install, remove or load drivers; modify the registry; change power plans; set process affinity; edit game settings; write PCI configuration space; access MSRs/MMIO/SMBus directly; or flash UEFI/BIOS firmware.

A matching hardware ID produces a candidate, not a compatibility or safety verdict. A real deployment workflow would also need OS build and INF target checks, Windows driver ranking, catalog signature and publisher verification, package provenance, explicit operator approval, rollback and post-install health checks. Windows kernel driver signing policy also prevents arbitrary byte-level repair of closed vendor binaries from being a reliable generic strategy.

Windows Update search is off by default. The opt-in flag can contact the configured update service but invokes only the search operation; it does not call download or install APIs.

ACPI thermal zones may not expose CPU package or GPU hotspot sensors. Missing readings remain unknown rather than being interpreted as safe. The report's safety fields explicitly record that the collector has not made system changes. Exact PnP IDs are omitted from reports by default.

## Tests

\`\`\`powershell
python -m unittest tests.test_hardware_game_stack -v
python -m unittest discover -s tests -v
\`\`\`
