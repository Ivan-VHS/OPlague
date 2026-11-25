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

## Current UI/UX contract

The shared interface, accessibility, responsive-layout and motion budgets are documented in [UI/UX 2026 convergence](UI_UX_2026_CONVERGENCE.md). OPlague-specific implementation boundaries are recorded in the [Stage 0.5 profile](UI_UX_PROFILE_STAGE_0_5.md). The retired Codex 40026 document is not part of the current documentation set. Inventory and inspection remain read-only by default; no status style implies that a driver has been changed. Keyboard-only and 200% scaling remain release-level manual checks.

## UI/UX 2026 convergence

See [UI_UX_2026_CONVERGENCE.md](UI_UX_2026_CONVERGENCE.md) for shared tokens, accessibility targets, responsive behavior and motion budgets. The read-only product boundary remains authoritative.
