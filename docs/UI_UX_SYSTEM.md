# OPlague UI/UX system

**Status:** implemented in the Tkinter desktop workbench. The Windows-first device workflow and its read-only boundary are unchanged.

## Product surface

OPlague is a hardware inventory and driver-package diagnostic workbench. Its primary screens are Device Inventory, Package Inspector, Metric Lab and Compatibility Dry-run. The layout is data-first: status, provenance, hashes, exact hardware-ID evidence and safety boundaries matter more than decorative effects.

## Visual language

- **Brand:** deep navy and white work surfaces, blue primary actions, restrained red warning accents.
- **Dashboard structure:** grouped workbenches, compact action bars, stable tables, explicit status text and scrollable JSON/report areas.
- **Theme modes:** the header control cycles System, Light and Dark. OPLAGUE_UI_THEME=light or dark may explicitly override system appearance.
- **Native foundations:** preserve native ttk controls when practical; use a consistent dark-mode fallback where native themes cannot provide a readable dark palette.
- **Opaque data surfaces:** inventory, JSON, hashes and diagnostic reports remain solid and high contrast. No simulated glass is placed beneath dense data.

## Platform adaptation

| Environment | UI direction | Implementation boundary |
|---|---|---|
| Windows | Fluent-inspired spacing, native controls and clear desktop workbench hierarchy | Primary desktop target |
| macOS | Native ttk appearance where available; dark fallback palette | Portable file analysis only; live PnP discovery remains Windows-only |
| GNOME/Linux | Libadwaita-inspired spacing and predictable ttk components | Not a GTK/Libadwaita application |
| Web dashboards | Same information hierarchy for future monitoring views | No web dashboard is claimed today |

## Interaction and accessibility

- Inventory refresh is read-only; status text states the operation and result.
- Package inspection never extracts or executes package payloads.
- Compatibility remains an exact-ID candidate dry-run, not a verdict or installation action.
- Use row selection, textual labels and explicit statuses alongside color.
- Keep tables resizable and report panes scrollable for long paths and JSON.
- Preserve keyboard navigation and visible focus through native controls.

## Shared visual contract

| Token | Light | Dark |
|---|---|---|
| Page | #F3F6FA | #101827 |
| Surface | #FFFFFF | #172337 |
| Text | #172337 | #EEF3FA |
| Muted | #5C6B80 | #A7B4C7 |
| Accent | #2563EB | #6EA8FE |
| Alert | #DC2626 | #F87171 |
| Report | #FFFFFF | #111C2E |

## Related repositories

- [Pytyliki processor workstation](https://github.com/Ivan-VHS/Pytyliki/blob/main/docs/UI_UX_SYSTEM.md)
- [Reaper language and Studio](https://github.com/Ivan-VHS/Reaper/blob/main/docs/UI_UX_SYSTEM.md)

## Validation checklist

- The theme selector applies System, Light and Dark palettes without altering business logic.
- Inventory columns, inspector output, metric editors and compatibility reports remain readable.
- Device inventory, package parsing, hashing, dry-run planning and report composition preserve current behavior.
- No UI affordance suggests driver installation, removal or execution is available.
