# Anatidae Desktop Design System — OPlague

**Status:** the white-blue-red theme, persistent System/Light/Dark selector, adaptive Metric Lab grid and per-monitor DPI request are implemented. Advanced inspector layouts and physical 8K visual certification remain release work.

## 1. Product principles

OPlague is a Windows-first, read-only hardware and driver-package workbench. Its information architecture remains divided into Device Inventory, Package Inspector, Metric Lab and Compatibility & Dry-run. The design must make evidence and limitations more prominent than recommendations. A candidate match is not a compatibility verdict, a hash is not vendor authenticity, and inspection is not installation.

## 2. White-blue-red semantic tokens

| Token | Light | Dark |
|---|---|---|
| Workspace | \`#F4F8FD\` | \`#071A2D\` |
| Surface | \`#FFFFFF\` | \`#0F2A45\` |
| Elevated | \`#EAF1FA\` | \`#173A5E\` |
| Primary text | \`#122C45\` | \`#E8EDF2\` |
| Secondary text | \`#314B66\` | \`#D0DCE8\` |
| Muted | \`#4D6177\` | \`#B3C4D6\` |
| Primary blue | \`#004E98\` | \`#70A5FF\` |
| Blue hover | \`#1A5FDB\` | \`#8AB6FF\` |
| Action red | \`#B5122D\` | \`#FF7B86\` |
| Red hover | \`#9C1026\` | \`#FF9AA2\` |
| Border | \`#CAD8E8\` | \`#31516F\` |
| Focus | \`#1A5FDB\` | \`#8AB6FF\` |
| Selection | \`#D9E8FF\` | \`#244F82\` |

Do not add unrelated green, yellow, violet or teal accents. Success/warning/error states always include a text label or icon. Primary body text targets WCAG AAA contrast (7:1); button labels and large actionable graphics target at least 4.5:1. The theme module exposes a contrast calculator and automated regression tests.

## 3. Components and typography

- Primary inspect/compare actions use blue fill and contrasting text. Secondary actions use a neutral surface with blue text and a fine border. Destructive emphasis is red; the product does not expose driver deployment or modification actions.
- Ttk controls use generous vertical padding, visible focus and 44px-preferred hit areas. Data tables use larger row height and remain independently scrollable.
- Segoe UI is the application font. Consolas is reserved for machine-readable evidence and diagnostic JSON.
- Use an 8pt rhythm: 8/16/24/32 logical px. Do not shrink text or hardware identifiers to force a table into the window.

## 4. Adaptive layout and HiDPI

Metric Lab editors reflow between three, two and one columns based on available container width. Inventory and package inspectors retain resizable tables and scrollable evidence. Long IDs and hashes remain selectable and horizontally scrollable rather than clipped.

The application requests Per-Monitor V2 DPI awareness before Tk initialization. Geometry remains in logical pixels and follows Windows display scaling. For 4K/8K workspaces, use the extra area for evidence panes and comparison context, not microscopic text or excessive whitespace. A real 7680×4320 multi-scale regression is still required before claiming certification.

## 5. Materials, motion and accessibility

The Tk shell uses the \`clam\` ttk theme to keep semantic colors predictable; the native Windows title frame remains platform-owned. Dense evidence surfaces stay opaque. Mica/Acrylic and shared-element motion are not claimed in the current Tk implementation.

The interface is motion-light by default. No perpetual animation or autoplay is introduced. Keyboard traversal, visible focus, readable labels and explicit status text remain mandatory. Color is never the only carrier of state. Theme changes repaint ttk, Text, Listbox, Entry and Menu surfaces together.

## 6. Persistence and implementation

- Theme mode is one of System, Light or Dark.
- The selected mode persists in a versioned per-user JSON file under the application configuration directory.
- \`OPLAGUE_UI_THEME=light|dark\` remains an explicit environment override for deployment and testing.
- Hardware identifiers, INF keys, JSON schema fields, hashes and machine-readable codes are not translated or normalized by the theme layer.
- All UI changes preserve metadata-only package inspection, archive bounds, read-only PnP discovery and candidate-only compatibility semantics.

## 7. Screenshot capture plan

Capture the running app in System/Light/Dark; Device Inventory with a selected row; Package Inspector with INF/ZIP evidence; Metric Lab at three/two/one-column widths; Compatibility/Dry-run with a candidate explanation; keyboard focus; and 8K/HiDPI at the chosen Windows scaling. An illustrative SVG is not a live screenshot and must be labelled as such.

## 8. Release checklist

- [ ] Existing System/Light/Dark theme behavior remains compatible.
- [ ] Theme choice survives restart and the environment override works.
- [ ] Semantic palette and WCAG contrast tests pass.
- [ ] Metric Lab reflows without clipped or undersized editors.
- [ ] Tables preserve full hardware IDs and report content.
- [ ] Focus and keyboard navigation remain visible.
- [ ] No driver installation, removal, enable/disable, signing or firmware action is added.
- [ ] Real-device 8K and multi-monitor screenshots are captured before certification.
