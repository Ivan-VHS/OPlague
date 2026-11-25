# OPlague GPU telemetry bridge v1

OPlague can export a bounded, read-only GPU sensor snapshot for ingestion by DuckOS. The first provider is the existing local NVIDIA `nvidia-smi` collector. Unsupported values remain JSON `null`; the exporter never fills missing sensors with estimates.

## Export

From the OPlague repository root:

```sh
python -m tools.gpu_telemetry_export --output dist/gpu-telemetry.json
```

The output follows [oplage.gpu-telemetry.v1.schema.json](../schemas/oplage.gpu-telemetry.v1.schema.json) and contains:
- device name and driver version;
- GPU temperature, utilization, VRAM use/total, board power and graphics/memory clocks where supported;
- UTC capture time, provider identity and a SHA-256 digest over the canonical payload without the digest field;
- `controls_performed: false` and `source.mode: read_only`.

The snapshot does not contain user identifiers, voltage requests, clock writes, fan controls, memory contents, driver binaries or shader data. The current provider is NVIDIA-only. An unavailable or unsupported provider produces an explicit unavailable snapshot, not fabricated metrics.

## DuckOS / Reaper integration

DuckOS's `duckos/gpu/oplage_bridge.rpr` accepts a parsed record only after the trusted file-ingest layer has validated the JSON schema and snapshot digest. It converts values into a monotonic Reaper sample; UTC timestamps are not treated as monotonic clocks.

The bridge keeps the following rules:
- missing sensors remain unknown;
- every record is bounded to sixteen GPU devices;
- values are checked for plausible type and range;
- telemetry never grants device, memory, clock or voltage capabilities;
- OPlague's snapshot is evidence, not authorization to load or replace a driver.

## Trust boundary

The SHA-256 field detects accidental or transport-level changes only when compared with a digest computed from the received canonical payload. It is not a signature or source attestation. The kernel must independently verify the OPlague publisher/build provenance or accept the file only as untrusted local telemetry.

The first version is read-only and contains no direct hardware controls. AMD and Intel providers require their own verified, read-only telemetry adapters and must preserve the same schema semantics.
