# Anatidae Desktop Design System — OPlague

**Status:** implemented Tk theme baseline and responsive Metric Lab inputs; full evidence-inspector orchestration, locale completion and physical 8K regression remain future acceptance work. This specification is the authoritative white-blue-red UI contract for OPlague.

## 1. Design intent

OPlague is a Windows-first, read-only hardware and driver-package workbench. Its UI must make evidence and limits more prominent than recommendations. A candidate match is not a compatibility verdict, a hash is not vendor authenticity, and package inspection is not driver installation. Device inventory, Package Inspector, Metric Lab and Compatibility/Dry-run remain separate workflows.

## 2. White-blue-red tokens

| Semantic token | Light theme | Dark theme |
|---|---|---|
| Workspace | \`#F4F8FD\` | \`#071A2D\` |
| Surface / editor | \`#FFFFFF\` | \`#0F2A45\` |
| Elevated surface | \`#EAF1FA\` | \`#173A5E\` |
| Primary text | \`#122C45\` | \`#E8EDF2\` |
| Secondary text | \`#314B66\` | \`#D0DCE8\` |
| Muted text | \`#4D6177\` | \`#B3C4D6\` |
| Primary blue | \`#004E98\` | \`#70A5FF\` |
| Blue hover | \`#1A5FDB\` | \`#8AB6FF\` |
| Action / danger red | \`#B5122D\` | \`#FF7B86\` |
| Red hover | \`#9C1026\` | \`#FF9AA2\` |
| Border | \`#CAD8E8\` | \`#31516F\` |
| Focus | \`#1A5FDB\` | \`#8AB6FF\` |
| Selection | \`#D9E8FF\` | \`#244F82\` |

No unrelated green, yellow, violet or teal accent is introduced. State is conveyed with an icon/word and supporting color, never hue alone. Body text targets 7:1 contrast; action labels target at least 4.5:1. Imported vendor strings, PnP identifiers, JSON keys, hashes and machine-readable codes remain unchanged.

## 3. Controls and typography

- Primary inspect/compare actions use blue fill; secondary actions remain white/surface with blue text; any irreversible-danger presentation uses red. The product itself still exposes no driver installation/removal controls.
- Ttk buttons use generous padding and clear focus styling. Prefer 44px interactive height; table rows use a larger touch-friendly row height and remain independently scrollable.
- Segoe UI is used for UI text. Consolas is reserved for machine-readable evidence and diagnostic JSON.
- Use an 8pt spacing rhythm. On narrow windows, Metric Lab input groups stack into two or one columns rather than becoming tiny side-by-side editors.
- Theme switching repaints ttk widgets, ScrolledText/Text content, Listbox and menus together.

## 4. Adaptive layout and HiDPI

The app requests Per-Monitor V2 DPI awareness before constructing Tk. Inventory, reports and compatibility outputs use expanding table/text areas; Metric Lab recalculates its 3/2/1-column input layout from the available width. Keep hardware IDs and hashes selectable and horizontally scrollable rather than clipping or truncating evidence.

The 8K target is logical-size preservation, not physical-pixel density inflation. At 7680×4320, use Windows scaling and additional inspector space; never shrink text to fill a wide panel. Real hardware at multiple scale factors still needs visual regression before 8K certification.

## 5. Materials, motion and accessibility

Tk uses the \`clam\` theme for stable semantic colors and spacing; the Windows title frame remains native. Surfaces are opaque, layered and readable. Mica/Acrylic and animated glass effects are not claimed. The interface is motion-light by default and has no perpetual or auto-playing animation.

Keyboard traversal, visible focus, meaningful tab labels, table selection, selectable report text and explicit validation messages are required. Safety notices remain visible: metadata-only inspection, bounded archive reads, exact-ID matching and pseudonymized-but-linkable snapshots.

## 6. Platform implementation ledger

| Area | Current implementation |
|---|---|
| Theme | \`tools/ui_theme.py\`: shared white-blue-red light/dark token maps, ttk styling and Text/Listbox/Menu repaint |
| Persistence | Versioned theme preference under the user's application config directory |
| Theme control | Header Light/Dark toggle |
| Responsive layout | Metric Lab inputs reflow between 3, 2 and 1 columns |
| DPI | Per-monitor DPI awareness requested before Tk initialization |
| Domain invariants | Read-only device inventory and package inspection behavior remains unchanged |
| Not claimed | Driver deployment, Mica/Acrylic, CSS container queries, full locale parity or certified 8K screenshots |

## 7. Visual review capture plan

Capture both themes while the app is running; Device Inventory with selected rows; Package Inspector summary and detailed evidence; Metric Lab at three-column and stacked widths; Compatibility/Dry-run candidate details; visible focus; and 8K/HiDPI layout at OS scaling. Illustrations and SVG mockups must not be presented as live application screenshots.

## 8. Release checklist

- [ ] Light/dark token and contrast tests pass.
- [ ] Theme change updates ttk, Text and Listbox surfaces atomically.
- [ ] Theme choice survives restart.
- [ ] Metric Lab stacks at compact widths with no clipped editors.
- [ ] Device tables retain readable columns and selectable full hardware IDs.
- [ ] Focus, keyboard operation and reduced-motion baseline work.
- [ ] Read-only/no-driver-install invariant remains intact.
- [ ] Candidate matches remain explicitly non-verdicts.
- [ ] Real-device 8K screenshots are completed before certification.
