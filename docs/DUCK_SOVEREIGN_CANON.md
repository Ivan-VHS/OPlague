# Shared desktop design canon

Four native GUI stacks remain independent: Pytyliki/Win32, Reaper/Tk, OPlague/Tk, VentuSample/Qt. Shared semantics do not force one toolkit.

## Palette

| Token | HEX | Use |
|---|---|---|
| Feather white | #FFFFFF | surfaces |
| Light surface | #F4F6FA | light background |
| River blue | #0039A6 | navigation/actions |
| Deep blue | #0A1E46 | text/dark surface |
| Beak red | #D52B1E | focus and signal |
| Banner red | #B51A10 | critical marker |

Composition guide: white 60% · blue 25% · red 15% (visual target, not measured pixel ratio). Preserve WCAG contrast, keyboard focus, visible state text and native control semantics. No gradient or color-only status.
