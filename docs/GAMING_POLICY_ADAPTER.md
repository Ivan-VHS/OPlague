# OPlague capability evidence adapter

**Project author/developer:** Ivan-VHS

OPlague contributes measured Windows hardware, NVIDIA telemetry, Windows reliability events, frame-time CSV summaries, atomic snapshots and operator-confirmed local profiles to DuckOS's 66-rule policy.

## Supported evidence

The adapter can declare these DuckOS provider IDs available when matching evidence is supplied: `hardware_profile`, `gpu_telemetry`, `vram_metrics`, `reliability_events`, `frame_time`, `power_plan`, `session_snapshot` and `compatibility_profiles`.

Every other provider remains unavailable. In particular, an NVIDIA temperature reading is telemetry, not a thermal-control or fan-control provider. A Windows power-plan snapshot is not proof that CPU/GPU clocks or voltages are controlled.

## Safety

The adapter does not start/restore a power session, touch drivers, write the registry, terminate services, change network settings or set process priorities. It accepts only validated evidence records and returns a DuckOS-compatible capability map. Unknown and unavailable values stay unavailable.

## Verification

```sh
python -m unittest tests.test_gaming_policy_adapter -v
```


## Sequential rollout

Rollout gate: this PR stays in draft until DuckOS PR #75 is merged. Then it is the second stage of the gaming-policy rollout.
