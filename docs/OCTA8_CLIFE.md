# OCTA-8 + CLife federation

OPlague remains a Python 3.10+ read-only device and driver evidence workbench. Its OCTA-8 adapter uses the shared `ivan-vhs.octa8.v1` JSON envelope: null, boolean, signed 64-bit integer, finite number, UTF-8 text, bytes, sequence and record. The adapter validates shape and produces deterministic SHA-256 digests for reports and cross-project interchange.

## CLife

Run `python tools/clife.py snapshot .`, then `verify ARCHIVE`; recovery uses `restore ARCHIVE --to NEW_DIRECTORY`. Snapshots are bounded, exclude build/VCS/cache output and carry a per-file SHA-256 manifest. Restore refuses to overwrite or merge into an existing directory.

All hardware and package inspection stays read-only. OCTA-8 is a data contract, not a compatibility verdict, driver action or trust proof.
