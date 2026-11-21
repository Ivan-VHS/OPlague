#!/usr/bin/env bash
set -euo pipefail

PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python 3 is required for OPlague's platform-neutral inspection tools." >&2
  exit 2
fi
"$PYTHON" - <<'PY'
import platform
import sys
machine = platform.machine().strip().casefold()
if machine not in {"e2k", "elbrus", "elbrus-2000"}:
    raise SystemExit(f"Not an Elbrus E2K host: platform.machine()={machine!r}")
if sys.version_info < (3, 10):
    raise SystemExit("Python 3.10+ is required")
print(f"Verified host: {platform.machine()} / Python {platform.python_version()}")
PY

"$PYTHON" -m compileall -q tools tests
"$PYTHON" -m unittest discover -s tests -p "test_architecture_profiles.py" -v
"$PYTHON" -m tools.architecture_profiles --host-info --json
