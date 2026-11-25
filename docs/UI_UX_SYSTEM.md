# OPlague UI/UX

| Surface | Interaction |
|---|---|
| Inventory | read-only refresh; visible status |
| Package inspector | metadata, hashes, limits; no extraction |
| Metric Lab | JSON profiles; rejects invalid dimensions |
| Compatibility dry-run | exact ID candidates; manual review |
| Reports | scrollable, copyable, explicit export |
| Settings | versioned local theme preference |

Themes: System / Light / Dark. Keep tables resizable, data surfaces opaque, keyboard focus visible and status text explicit. Live PnP is Windows-only; saved-file analysis is portable.

## 40026 Codex

The shared interaction contract is maintained in [Duck UI/UX Foundation — Stage 0.1](https://github.com/Ivan-VHS/DuckOS/blob/main/docs/UI_UX_STAGE_0_1.md); the [OPlague UI/UX Profile — Stage 0.5](UI_UX_PROFILE_STAGE_0_5.md) records only this product's implementation notes and boundaries. Light/Dark themes expose brand-compliant Success/Warning/Error/Info text roles and validate all semantic text pairs against 4.5:1 WCAG AA. Inventory and inspection remain read-only by default; no status style implies that a driver has been changed. Keyboard-only and 200% scaling remain release-level manual checks.

## UI/UX 2026 convergence

See [UI_UX_2026_CONVERGENCE.md](UI_UX_2026_CONVERGENCE.md) for shared tokens, accessibility targets, responsive behavior and motion budgets. The read-only product boundary remains authoritative.
