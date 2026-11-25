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


## 2026 semantic extension

The original six brand colors remain canonical. Native desktop themes may additionally use this neutral and semantic extension for calm work surfaces, readable dark mode, selection and accessible focus. Blue remains action/focus; red remains critical/destructive.

| Token | Light | Dark |
|---|---|---|
| Workspace | #F4F8FD | #071A2D |
| Surface | #FFFFFF | #0F2A45 |
| Elevated | #EAF1FA | #173A5E |
| Primary text | #122C45 | #E8EDF2 |
| Secondary | #314B66 | #D0DCE8 |
| Muted | #4D6177 | #B3C4D6 |
| Action blue | #004E98 | #70A5FF |
| Focus / hover blue | #1A5FDB | #8AB6FF |
| Critical red | #B5122D | #FF7B86 |
| Critical hover | #9C1026 | #FF9AA2 |
| Border | #CAD8E8 | #31516F |
| Selection | #D9E8FF | #244F82 |

The source validator accepts these tokens and continues to enforce high-contrast text pairs. This does not authorize gradients, color-only signals or decorative motion.
