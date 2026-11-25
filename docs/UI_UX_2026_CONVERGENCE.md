# UI/UX 2026 — shared product interface contract

**Maintainer:** Ivan-VHS · **Product:** OPlague  
**Design language:** AETHER-ANAS / Anatidae — consistent white/blue/red identity adapted to native platform behavior.

This contract is for a read-only hardware and driver inspection workbench. Clear evidence, bounded actions and explicit state matter more than ornamental effects.

## Semantic palette

| Token | Light | Dark | Role |
|---|---|---|---|
| bg | #F4F8FD | #071A2D | Workspace |
| surface | #FFFFFF | #0F2A45 | Main panels |
| elevated | #EAF1FA | #173A5E | Secondary surfaces |
| fg | #122C45 | #E8EDF2 | Primary text |
| secondary | #314B66 | #D0DCE8 | Supporting text |
| muted | #4D6177 | #B3C4D6 | Metadata |
| blue | #004E98 | #70A5FF | Primary actions/navigation |
| blue_hover | #1A5FDB | #8AB6FF | Hover and focus |
| on_blue | #FFFFFF | #071A2D | Text on blue |
| red | #B5122D | #FF7B86 | Critical/destructive states |
| red_hover | #9C1026 | #FF9AA2 | Critical-action hover |
| on_red | #FFFFFF | #071A2D | Text on red |
| border | #CAD8E8 | #31516F | Boundaries |
| focus | #1A5FDB | #8AB6FF | Keyboard focus |
| selection | #D9E8FF | #244F82 | Selected content |
| selection_fg | #122C45 | #FFFFFF | Text on selection |
| disabled | #6B7C90 | #9BAFC4 | Disabled text |

Blue is the normal action/navigation/focus language. Red is reserved for critical and destructive states. Keep data surfaces opaque and stable.

## Hierarchy and density

- Keep device inventory, package inspection, metric comparison, compatibility dry-run and reports clearly separated.
- Use an 8 px spacing rhythm, visible column headings and explicit status text.
- Prefer 40–44 px actions and 38–44 px controls; dense tables may use 34–36 px rows if readable.
- Use monospace text for hashes, hardware IDs, JSON and diagnostic output.
- Preserve resizable columns, scrollable reports and clear metadata/export boundaries.

## Accessibility and input

- Give controls accessible names and visible keyboard focus; retain native keyboard navigation and resizing.
- Target 4.5:1 contrast for normal text and 3:1 for focus; aim for 7:1 body text where practical.
- Never present compatibility or safety as a color-only badge. Show evidence, caveats and readable status text.
- Reduced Motion overrides Expressive Motion. Eco suppresses nonessential visual work and respects native OS settings.

## Motion 2026

| Event | Timing |
|---|---:|
| Direct acknowledgement | 0–40 ms |
| Hover/focus/state | 80–140 ms |
| Pane transition | 160–240 ms |
| Context transition | 260–380 ms |
| Reduced-motion replacement | ≤80 ms |

Expressive Motion may scale supported transitions by 1.35×, capped at 380 ms. Reduced Motion removes spatial movement and caps retained fades at 80 ms; Eco follows the same conservative path. Animation remains on the UI thread and never blocks inventory or file analysis. OPlague has no audio transport; BPM sync remains unavailable.

## Responsive and high-DPI

Reflow metric input panels instead of shrinking editors. Validate narrow/wide windows, keyboard-only use and 100%, 125%, 150% and 200% scaling. Manual monitor review is pending until performed.

## Product-specific implementation

OPlague is a hardware and driver inspection workbench. Keep inventory and package analysis read-only, make hashes and compatibility evidence easy to inspect, and retain scrollable reports and resizable tables. Do not add driver installation, firmware flashing or hidden device mutation as UI decoration. There is no project audio transport, so BPM sync stays disabled.

## Engineering references

- [Qt Accessibility](https://doc.qt.io/qt-6/accessible.html) · [Qt High DPI](https://doc.qt.io/qt-6/highdpi.html)
- [WCAG 2.2 Focus Appearance](https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html)
- [Microsoft Windows app design](https://learn.microsoft.com/windows/apps/design/)

Targets are documented; this file does not claim all manual acceptance checks have passed.
