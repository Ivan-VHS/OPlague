# OPlague — Driver Workbench

[![Windows desktop build](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml/badge.svg)](https://github.com/Ivan-VHS/OPlague/actions/workflows/desktop-build.yml) · Python 3.10+ · Windows · Apache-2.0
**Developer:** [Ivan-VHS](https://github.com/Ivan-VHS)

**Read-only workbench for Windows device inventory, driver-package inspection and evidence-based comparison.** It does not install, load or modify drivers.

[English](README.md) · [Русский](README.ru.md) · [Українська](README.uk.md) · [简体中文](README.zh-CN.md)

![Illustrative desktop preview](assets/oplague-workbench-preview.svg)
<sub>Illustrative interface reconstruction, not a live capture.</sub>

| Workbench | Evidence | Boundary |
|---|---|---|
| Device inventory | Plug and Play identity, status, hardware IDs | read-only |
| INF/ZIP | metadata, hashes, paths, resource limits | no extraction/execution |
| Architecture | INF target vs host | evidence, not verdict |
| Compatibility graph | exact normalized hardware-ID edges | candidate only |
| UDRV v1 | manifest, payload sizes, SHA-256 | no install/load |
| DRIVE-LENS | provenance, HMAC pseudonyms, attribute/time-window grouping | no automatic verdict |
| Batch reports | ordered results, totals, fingerprint | no system write |
| Metric Lab | normalized vectors, weighted distance, variance | user-supplied data |
| Clinical Systems | 120 principle records, 36 telemetry checks | advisory only |

## Run and test

```sh
python oplague_app.py
python -m unittest discover -s tests -v
python tools/udrv_inspector.py path/to/package.udrv --json
python tools/clinical_systems.py --catalog --pretty
```

## Numeric reference

| INF target | PE machine |
|---|---:|
| NTx86 | 0x014C |
| NTamd64 | 0x8664 |
| NTarm | 0x01C4 |
| NTarm64 | 0xAA64 |
| NTia64 (legacy) | 0x0200 |

UDRV v1: manifest ≤4 MiB · entries ≤10,000 · file ≤512 MiB · total ≤2 GiB · hash buffer 1 MiB.

Exact ID/hash matches do not prove publisher trust, OS compatibility or safe installation. Reaper integration is versioned JSON; Pytyliki native metrics require an explicit trusted library path.

[Features](docs/FEATURES.md) · [Architecture](docs/ARCHITECTURE.md) · [UDRV](docs/UDRV_FORMAT_V1.md) · [Stewardship](docs/PROJECT_STEWARDSHIP_STANDARD.md) · [Design](docs/DUCK_SOVEREIGN_CANON.md) · [Docs index](docs/README.md) · [License](LICENSE)
