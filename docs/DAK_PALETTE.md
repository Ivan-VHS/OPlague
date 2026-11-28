# OPlague visual system — Imperial Noir workbench

OPlague shares the DAK black/white/gold foundation for window chrome and navigation, while keeping its domain status colors distinct. The workbench remains read-only by default: visual state never suggests that a driver was installed, a device changed, or a performance setting was applied.

| Role | Value | Use |
|---|---|---|
| Canvas | `#050505` | Main workspace |
| Surface | `#101010` | Inspector and report panels |
| Elevated | `#181818` | Secondary cards and popovers |
| Text | `#FFFFFF` | Primary content |
| Secondary | `#E5E5E5` | Supporting copy |
| Muted | `#A6A6A6` | Metadata and hints |
| Action | `#FFD700` | Primary action and selection |
| Hover / focus | `#FFE45C` | Pointer and keyboard focus |
| Border | `#3A3A3A` | Structural boundaries |
| Selection | `#3A3100` | Selected row background |
| Success | `#2EAD68` | Confirmed read-only result |
| Warning | `#FFD700` | Caution requiring review |
| Error | `#FF6B72` | Failed or unsafe inspection |
| Information | `#6CA8FF` | Neutral technical information |

The status text/icon always accompanies its color. Normal text targets 4.5:1 contrast and primary content targets 7:1 where practical. Glass effects are optional surface treatment; reports, tables and inspection details remain opaque enough to read at every scale.

Legacy System/Light/Dark/Amber preference values continue to normalize to the fixed DAK palette. No runtime network assets or cloud fonts are required.
