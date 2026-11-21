# CLife — evidence checkpoint and controlled recovery

OPlague remains a read-only Windows device and driver workbench. CLife adds preservation of project files, exported reports and review evidence; it does not install, load, patch or restore drivers or devices.

## Software mapping

| Simulation concept | OPlague implementation |
|---|---|
| Cryo fault | missing evidence file, interrupted export, archive corruption or stale report |
| Snapshot | ZIP evidence capsule with a SHA-256 manifest |
| Integrity / coherence | verified file digests, sizes and manifest schema |
| Stasis hold | reject invalid archives and unsafe destinations |
| Recovery | materialize a verified evidence copy into a new directory |

## Commands

Run from the repository root with Python 3.10+:

\`\`\`sh
python tools/clife.py snapshot path/to/evidence
python tools/clife.py inspect path/to/snapshot.clife
python tools/clife.py verify path/to/snapshot.clife
python tools/clife.py restore path/to/snapshot.clife --to path/to/recovered-evidence
python -m unittest discover -s tests -p "test_clife.py" -v
\`\`\`

The default archive location is <evidence-root>/.clife/snapshots/. Symlinks and generated folders (.git, build, dist, caches, virtual environments, dependency trees and .clife) are excluded.

## Safety boundary

- CLife copies ordinary files; it does not access device handles or driver-installation APIs.
- Restore is an evidence-copy operation into a **new** directory. It never overwrites the original evidence, an INF package or a system driver.
- SHA-256 is verified for each archived file. Limits are 20,000 files, 128 MiB per file and 1 GiB total uncompressed data.
- A valid hash establishes byte identity against the manifest, not publisher trust, device suitability, driver compatibility or authenticity of the original source.
- No physical cryogenic, biological or quantum-consciousness behavior is implemented.
- The 666,666,666-character pseudocode stream is not generated or persisted.
