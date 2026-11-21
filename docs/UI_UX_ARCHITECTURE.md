# OPlague UI/UX and Language-Environment Architecture

**Status:** target architecture for the Windows-first Tkinter workbench. The white-blue-red light/dark theme and adaptive Metric Lab input layout are implemented; full localization, advanced inspectors and physical 8K regression remain acceptance work.

## 1. Product fit

OPlague is a read-only hardware and driver-package workbench. Core jobs are device inventory, bounded INF/ZIP inspection, exact hardware-ID matching, dry-run compatibility planning, metric comparison, device federation and QCS validation. The UI must make evidence and limits more prominent than recommendations: a candidate match is not a compatibility verdict, a hash is not vendor authenticity, and inspection is not installation.

The current shell has Device Inventory, Package Inspector, Metric Lab and Compatibility & Dry-run tabs. Preserve these domain boundaries; do not create one overloaded dashboard.

## 2. Six Anatidae articles as UI invariants

| Article | Invariant | OPlague application |
|---|---|---|
| I. Water-repellent plumage | Isolated, bounded panels | Inventory, archive inspection, metric inputs and compatibility results have separate validation/error surfaces. |
| II. Calm surface, strong engine | Summary first; evidence on demand | Show outcome, evidence and caveat first; expand INF fields, hashes, archive entries and scoring details when requested. |
| III. Rudder and balance | Persistent context | Keep selected device, package, host architecture, inspection time and report fingerprint visible. |
| IV. Webbed feet | Layout follows available space | Tables and inspectors reflow without clipping at high DPI or ultrawide sizes. |
| V. Precise bill | Exact matching and explicit actions | Filter by hardware ID, package, architecture and status; distinguish exact match from heuristic similarity. |
| VI. Flock and wake | Provenance, privacy and mutual rights | Show data origin, hash scope, snapshot version, license metadata and third-party provenance at boundaries. |

## 3. Adaptive workbench

Use logical client dimensions after OS DPI scaling. Support 7680×4320 at 100–300% system scaling.

- **Compact (≤1280 logical px):** one active tab; searchable device details; bounded package summary with collapsible evidence; Metric Lab inputs stack vertically; dry-run output remains separate from device state; read-only safety statement stays visible.
- **Standard (1281–2560):** navigation, active table/editor and evidence inspector. Inventory shows device table + selected-device detail + snapshot status. Package view shows summary + INF/archive evidence + batch queue. Compatibility shows exact-ID candidates + explanation + dry-run preview.
- **Wide / 4K (2561–3839):** side-by-side inventory/detail, package metadata/architecture targets/archive evidence, optional compatibility graph and report composer.
- **8K (≥3840 logical px):** navigation, active workbench, evidence inspector, audit timeline and optional graph. Use space for comparison and provenance; cap text measure at 68–96 characters. Table columns remain independently resizable and scrollable; do not shrink text to fit.

## 4. Tokenized visual system

Components consume semantic tokens, not hard-coded colors:

- `bg-pond`, `bg-surface`, `bg-elevated`: workbench, cards and dialogs.
- `fg-primary`, `fg-secondary`, `fg-muted`: evidence, explanations and metadata.
- `accent-blue`, `accent-blue-hover`, `accent-red`: primary action, hover/selection and destructive emphasis.
- `status-ok`, `status-warn`, `status-danger`: always paired with labels/icons; never color-only.

The concrete light/dark token table is maintained in [ANATIDAE_DESKTOP_DESIGN_SYSTEM.md](ANATIDAE_DESKTOP_DESIGN_SYSTEM.md); older palette preset examples below are historical proposals, not the shipped product palette.

Do not expose alternate accent presets. The production identity uses the single white-blue-red semantic token set in [ANATIDAE_DESKTOP_DESIGN_SYSTEM.md](ANATIDAE_DESKTOP_DESIGN_SYSTEM.md), with light/dark surfaces and normal/high/extra-high contrast modes. Status uses labels/icons/patterns, never color alone. Theme changes update tabs, tables, text widgets, graphs, labels and dialogs atomically.

Include `uiScale` 80–250%, typography, spacing density and border strength. On 8K, focus outlines and separators scale to about 1.5–3 physical px. Motion is 120–220 ms where useful; reduced-motion disables it.

## 5. 20×20 meaning model

The shared 20-concept taxonomy maps to navigation and module metadata:

- E1–E4: language composition, adoption, representation and algorithms.
- E5–E9: machine model, formal checks, tools, computation and system layer.
- E10–E13: catalogues, command interface, syntax and semantics.
- E14–E16: declarative policies, imperative process and procedures.
- E17–E19: local ownership, module author rights and third-party rights.
- E20: fast, calm and inspectable feedback.

The 400 directed `Ei ⊗ Ej` projections form a design crosswalk for QCS profiles, inspection steps, metadata and federation workflows—not a driver scoring algorithm and not 400 implemented features. Reuse [Reaper MOST 400 matrix](https://github.com/Ivan-VHS/Reaper/blob/main/docs/MOST_400_COMBINATORIAL_MATRIX.md); keep OPlague's QCS validator and device snapshot schemas as separate contracts.

## 6. Language, QCS and localization boundary

- QCS UI exposes profile, contour, validation result and source span. QCS validates metadata and handoff markers; it is not a compiler or hardware verifier.
- INF keys, PnP identifiers, JSON schema fields, hashes and machine-readable error codes remain stable and locale-neutral.
- Human-facing labels, explanations, warnings and help are localizable. Target locales: English, Ukrainian, Russian and Simplified Chinese.
- Imported vendor strings remain source data; do not translate or normalize identifiers.
- The 66-entry systems-language catalogue is descriptive metadata. Distinguish PATH-detected tools from actual integration support.

## 7. Trust, privacy and accessibility

- No driver install/remove/enable/disable, firmware update, signing, rollback or device-register operation is exposed.
- Every package operation displays size/entry/expansion limits and whether content was read, extracted or executed. Metadata-only inspection remains the invariant.
- Exact hardware-ID matches and heuristic similarities use different labels and encodings.
- Snapshot pseudonymization is not anonymization; show linkability warnings at export.
- Keyboard navigation, visible focus, accessible names, minimum 40 logical px targets (44 preferred), and reduced-motion support are mandatory.

## 8. Implementation sequence and acceptance gates

1. Centralize ttk semantic colors, fonts, spacing and density tokens.
2. Add persistent theme/scale settings and DPI-aware layout profiles.
3. Add table presets, evidence inspectors and search/filter while preserving tab boundaries.
4. Add locale resources and untranslated-key tests.
5. Add 20×20 crosswalk navigation backed by the canonical matrix with evidence links and explicit statuses.

Acceptance: read-only invariant unchanged; no candidate presented as a verdict; source IDs and JSON keys stable; tables readable at supported scales; theme changes atomic; accessibility and reduced motion work; package/federation tests and desktop CI pass.

## 9. Related architecture

- [Federated integration](FEDERATED_INTEGRATION.md) · [Device compatibility graph](DEVICE_COMPATIBILITY_GRAPH.md)
- [QCS syntax and validator](QUANTUM_CONTOUR_SYNTAX.md) · [UDRV format](UDRV_FORMAT_V1.md)
- [Reaper MOST matrix](https://github.com/Ivan-VHS/Reaper/blob/main/docs/MOST_400_COMBINATORIAL_MATRIX.md)
