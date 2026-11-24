# README and Visual Documentation Standard

**Scope:** OPlague README family, documentation indexes, diagrams, screenshots and visual assets. Source, tests, schemas and CI remain authoritative.

## Publishing contract

- Lead with a factual product statement and identify Windows-only/live-data boundaries.
- Keep theme-aware hero, CI/license badges, navigation and an exact quick start above the fold.
- Distinguish read-only device/driver inspection from the separate reversible gaming power-plan workflow.
- Do not describe hardware-ID matches, hashes, heuristics or metrics as safety verdicts or certification.
- A documentation refresh is not a software release or a product-version claim.

## README sequence

Hero → one-line pitch → badges/navigation → safety boundary → requirements/quick start → documentation-revival comparison → capability matrix → visual overview → Mermaid pipeline → configuration/access → repository map → verification/status → contribution/license.

## Theme-aware hero

Use `assets/readme/hero-banner-light.svg` and `assets/readme/hero-banner-dark.svg` with identical dimensions and viewBox. Select with `<picture>` and `prefers-color-scheme`; retain useful fallback alt text. Keep SVGs self-contained and free of remote assets.

## Screenshot and diagram integrity

- A screenshot must be a committed capture of the real application and link to its original file.
- A workflow/architecture drawing must be captioned as an illustration, not a screenshot.
- Use a two-column, one-row visual grid, meaningful alt text and concise captions.
- Do not display private device IDs, serial numbers, package paths or fabricated inventory.
- If no verified capture exists, declare that and use labelled schematics only.

## Technical accuracy

- Every command must match the current Python modules and tools.
- Describe live PnP collection as Windows-specific.
- Keep driver payload inspection bounded and metadata-only; do not imply extraction, execution or installation.
- Document the explicit power-plan session separately from read-only inspection.
- Do not invent environment variables, accounts, API keys, hosted services or deployment URLs.

## Localization and acceptance

Keep English, Ukrainian, Russian and Simplified Chinese versions aligned in scope, safety wording and commands. Preserve exact CLI spellings and filenames. Check links, image paths, Mermaid syntax, badge workflow paths and `git diff --check`.
