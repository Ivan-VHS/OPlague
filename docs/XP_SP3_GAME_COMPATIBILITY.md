# Windows XP SP3 game hardware compatibility audit

**Project author/developer:** Ivan-VHS

OPlague adds a read-only compatibility audit for the shared `duckos.game-launch-profile.v1` contract. It translates XP-era requirements into host-side findings that can be reviewed alongside existing PnP, signed-driver and GPU telemetry snapshots.

The audit calls out Glide-wrapper dependencies, legacy DirectDraw/Direct3D and OpenGL paths, 8/16-bit display modes, non-4:3 layouts, high refresh rates, EAX/DirectSound, DirectInput and DirectPlay/IPX requirements. When supplied, a device snapshot is used only to identify display adapters and the driver evidence already present in that snapshot.

Run it with:

```sh
python tools/xp_game_compatibility.py game-profile.json
python tools/xp_game_compatibility.py game-profile.json --hardware device-snapshot.json --output compatibility-report.json
```

No driver is installed or replaced. The tool does not edit the registry, change a display mode, alter a power plan, terminate services, open ports or modify network settings. Findings are diagnostic recommendations, not proof that a game will run.
