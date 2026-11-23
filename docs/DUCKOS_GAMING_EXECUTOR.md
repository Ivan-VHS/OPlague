# OPlague DuckOS gaming-session executor

**Project author/developer:** Ivan-VHS

This adapter connects DuckOS's `duckos.gaming-session-profile.v1` to OPlague's existing Windows power-plan session functions.

## What can be executed

After explicit user consent, OPlague captures a hardware/power-plan snapshot and can temporarily select the built-in Windows performance or balanced plan. `restore_duckos_game_session()` delegates to OPlague's compare-before-restore logic: if the active plan has been changed externally, that user-selected plan is left untouched.

The adapter does not change CPU/GPU clocks or voltage, fan curves, drivers, registry, services, memory policy, interrupt routing, process priority, affinity or network settings. It is Windows-only through the underlying OPlague implementation. Selecting the same power plan may result in no plan change.

## API

```python
from tools.duckos_gaming_executor import (
    start_duckos_game_session,
    restore_duckos_game_session,
)

started = start_duckos_game_session(session_profile, consent=True, power_mode="balanced")
# On confirmed game exit:
restored = restore_duckos_game_session()
```

## Verification

```sh
python -m unittest tests.test_duckos_gaming_executor -v
```
