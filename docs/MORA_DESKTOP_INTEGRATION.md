# Mora desktop integration — OPlague

OPlague joins the Mora workspace as the read-only device and driver-package workbench. Mora supplies the common desktop catalogue and initial theme; all inspection and reporting remain inside OPlague.

## Workspace contract

- Manifest: mora-app.json, version 1.
- Launch entry point: oplague_app.py.
- Window model: a separate native Tk window.
- Theme hand-off: MORA_THEME_MODE=dark or light.
- The application remains local; no remote device-management service is introduced.

The canonical manifest schema, discovery rules and local host are maintained by [DuckOS / Mora](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/MORA_DESKTOP.md).

## Shared appearance

Mora's startup theme is read before OPlague applies its saved appearance. The visual palette uses the same semantic values as the other family applications:

| Role | Dark | Light |
|---|---|---|
| Page | #071A2D | #F4F8FD |
| Surface | #0F2A45 | #FFFFFF |
| Text | #E8EDF2 | #122C45 |
| Primary | #70A5FF | #004E98 |
| Signal | #FF7B86 | #B5122D |

The value is an initial preference, not a live remote theme channel. OPlague's own theme controls remain usable after startup.

## Safety and product boundaries

Mora does not elevate OPlague, grant new privileges or request driver installation. Device inventory stays read-only; INF and ZIP parsing remains bounded; package contents are not extracted or executed. Exact hardware-ID matches remain candidate evidence, not a compatibility or safety verdict.

Live Plug and Play collection remains Windows-only. Saved-file inspection and report viewing retain the platforms supported by the application itself.

## Verification

    python -m compileall -q oplague_app.py oplage_app.py tests
    python -m unittest discover -s tests -v

The integration does not replace UI_UX_SYSTEM.md, UI_MOTION.md or the read-only product contract.
