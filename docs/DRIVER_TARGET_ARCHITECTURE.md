# Driver Target Architecture Analysis

OPlague adds a read-only architecture classifier for Windows driver INF metadata. It detects explicit architecture decorations and compares them to a supplied or locally inferred host architecture.

## CLI

```sh
python -m tools.architecture_profiles --list --json
python -m tools.architecture_profiles --host amd64 --targets amd64,arm64 --json
python -m tools.architecture_profiles --host arm64 --inf path/to/driver.inf --json
python -m unittest discover -s tests -p 'test_architecture_profiles.py' -v
```

## Supported Windows INF target tokens

| Canonical target | INF decoration | PE machine |
|---|---|---|
| x86 | NTx86 | 0x014C |
| amd64 | NTamd64 | 0x8664 |
| arm | NTarm | 0x01C4 |
| arm64 | NTarm64 | 0xAA64 |
| ia64 | NTia64 | 0x0200 (legacy) |

The classifier also normalizes common host aliases such as `x86_64` to `amd64` and `aarch64` to `arm64`. It deliberately returns unknown for unsupported architecture names rather than inventing Windows driver support.

## Verdict semantics

- **explicit_match:** the INF text declares the normalized host architecture.
- **explicit_nonmatch:** recognized decorated targets exist, but the supplied host target is not among them.
- **unknown:** the host architecture or usable INF target evidence is missing or unrecognized.

An explicit match is only one compatibility signal. OS-version decorations, device IDs, signature policy, catalog integrity, package provenance, kernel ABI and runtime behaviour require separate validation. An explicit non-match is not an automatic rejection because generic or undecorated INF sections may also exist.

## Security boundary

Analysis is metadata-only. The tool never loads, extracts, installs, or executes driver payloads and does not change device state. It is not a driver-signing validator or an installation engine.
