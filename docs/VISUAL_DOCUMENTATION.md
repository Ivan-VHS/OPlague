# Visual documentation and graphics contract

**Project:** OPlague · **Scope:** README, Markdown/MDX, diagrams, screenshots, evidence graphics, badges, typography and native desktop motion references.

This contract defines visual presentation for a safety-sensitive, read-only inspection workbench. Visual confidence must never exceed the evidence available in the underlying data.

## Documentation hierarchy

| Surface | Responsibility | Authority |
|---|---|---|
| `README.md` | Product purpose, read-only boundary, real Windows capture, modules, commands and limits | Main branch and CI |
| `README.ru.md`, `README.uk.md`, `README.zh-CN.md` | Localized product entry points | Same facts and safety wording as English |
| `docs/README.md` | Navigation index for technical documentation | Files present in `docs/` |
| `docs/VISUAL_DOCUMENTATION.md` | This graphics and rendering contract | Architecture, schemas and evidence policies |
| `assets/` | Static SVG diagrams and verified desktop captures | SVG source or CI capture |

Keep the GitHub entry point in `README.md`. Do not introduce a duplicate `README.mdx` for repository browsing. MDX is reserved for a configured documentation website where interactive components have a real purpose.

## Markdown typography and navigation

- Use one H1 per page, a factual lead paragraph, then ordered H2/H3 sections with no skipped heading levels.
- Prefer sentence-case titles, concise paragraphs, descriptive links and stable relative paths.
- Use inline code for hardware IDs, INF keys, paths, hashes, schema names and command flags. Use fenced blocks with language identifiers for commands and data examples.
- In tables distinguish **observed**, **candidate**, **advisory**, **verified by test**, **not established** and **not supported**.
- Provide alternative text for every meaningful image. Captions must state whether the image is a real desktop capture, a diagram or a concept preview.
- Never encode severity, trust, compatibility, identity or uncertainty with colour or badges alone.

## Graphics, surfaces and image formats

### SVG and geometry

Use SVG for device-flow diagrams, compatibility-graph explainers, evidence pipelines and stable README infographics. Keep the editable source. SVG must include `viewBox`, descriptive `<title>` and `<desc>`, readable labels and contrast. GitHub-facing files stay static and self-contained: no scripts, events, animation, external fonts, tracking URLs or `foreignObject`. Use explicit legends for edges and node types; a line in a diagram must not look like a confirmed compatibility verdict unless that status is established by the data contract.

### Screenshots and raster images

The Windows workbench screenshot must be captured from the actual desktop build/run workflow. A mock-up or vector map is never labelled as a live application capture. Keep PNG as the reliable GitHub README format. WebP/AVIF are optional derivatives for a configured docs website; retain the PNG source/fallback. Crop only to focus the interface, never to hide warnings, status or relevant context. Do not upscale low-resolution captures.

### Colour, transparency, lighting and texture

Follow the [AETHER-ANAS / Anatidae design contracts](ANATIDAE_DESKTOP_DESIGN_SYSTEM.md) and [UI_MOTION.md](UI_MOTION.md). Blue represents navigation and neutral information; red is reserved for critical/destructive status, not for arbitrary emphasis. Prefer opaque evidence panels and restrained borders. Gradients, blur, transparency, grain, glows and post-processing must never compromise hashes, hardware IDs, INF text, warnings, status labels or tabular alignment.

## Motion, effects and simulation visuals

README graphics and evidence diagrams are static. Native motion is presentation-only and follows the bounded Tk controller and reduced-motion settings documented in [UI_MOTION.md](UI_MOTION.md). Reduce Motion and Eco override Expressive Motion. Do not animate device status or imply a live scan unless a real scan is running and its status is sourced from the application. No decorative effects may delay inventory, package bounds checking, hashing or report generation. Never claim 60/120 FPS or zero jitter without repeatable measurements.

## Diagram and docs tooling matrix

| Tool / format | Best use | Rule |
|---|---|---|
| GitHub Markdown + Mermaid | Small evidence-flow, state and sequence diagrams | Preferred source-first choice on GitHub |
| PlantUML (`.puml`) | Detailed inspection sequence and component relationships | Keep source and static SVG output |
| D2 (`.d2`) | Dense compatibility/evidence architecture maps | Use only with explicit node/edge semantics |
| SVG infographic | Stable diagram fallback for README and release notes | Static, accessible and self-contained |
| Markdown (`.md`) | Canonical portable documentation | Use for README and repository docs |
| MDX (`.mdx`) | Reusable interactive website components | Only in a configured docs site |
| Docusaurus | Versioned docs, sidebars and navigation | Optional adapter, not a dependency |
| VitePress | Markdown docs with Vue-powered site components | Optional adapter, not a dependency |
| Astro Starlight | Structured docs navigation and Markdown/MDX | Optional adapter, not a dependency |
| MkDocs Material | Python ecosystem docs sites and navigation | Optional adapter, not a dependency |
| Shields.io | CI, license and release badges | Use real endpoints only; no trust/security badges without evidence |
| GitHub Pages | Publishing a generated docs site | Only with an actual docs build/deploy pipeline |

Do not introduce multiple documentation generators. GitHub Markdown remains the portable baseline. Use Mermaid when its native rendering is sufficient; keep a static diagram export for environments without a compatible renderer.

## OPlague-specific visual boundaries

OPlague is a read-only Windows workbench for device inventory, driver-package metadata inspection and evidence-based comparison. Visuals must make provenance and confidence boundaries explicit: exact hardware-ID relationships are candidate links, INF target architecture is evidence rather than a compatibility verdict, SHA-256/HMAC/fingerprints do not establish publisher trust or authenticity, and impact profiles are advisory. Nothing in the interface or its diagrams installs, loads, enables, disables or modifies drivers.

For device and package views, keep raw observation, normalized identity, candidate relationship, advisory score and verified result visually distinct. A match edge is not a green “safe” badge. SHA-256 verifies content equality against a known digest, not publisher identity. HMAC pseudonyms and report fingerprints support provenance/consistency but are not proof of authenticity by themselves. Clinical Systems records are operational guidance, not medical or device certification.

## Review checklist

- [ ] All four README languages preserve the read-only and no-install/no-load boundaries.
- [ ] Desktop captures are genuine and retain meaningful status context.
- [ ] Diagram edges and node labels distinguish observation, candidates and verified facts.
- [ ] SVG has title/description/viewBox; no script, animation or remote dependency.
- [ ] Hashes, hardware IDs, warnings and dense evidence remain legible at normal zoom.
- [ ] Badges refer only to live CI, license or releases.
- [ ] Motion does not imply activity or a device-state change.
- [ ] `docs/README.md` indexes this contract.

## References

- [GitHub image and SVG rendering](https://docs.github.com/en/repositories/working-with-files/using-files/working-with-non-code-files)
- [GitHub Mermaid diagrams](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
- [Docusaurus Markdown and MDX](https://docusaurus.io/docs/markdown-features)
- [VitePress Markdown](https://vitepress.dev/guide/markdown)
- [Astro Starlight authoring content](https://starlight.astro.build/guides/authoring-content/)
