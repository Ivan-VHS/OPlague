# Documentation control

**Scope:** OPlague README family, operator guidance, schemas, screenshots, diagrams and system-integration documentation.

## Acceptance gates

| Gate | Requirement | Evidence |
|---|---|---|
| Evidence | Claims link to source, tests, schemas or CI | Code/test/CI references |
| Maturity | Separate implemented, partial, simulated and planned features | Feature matrix |
| Safety | Read-only inspection remains distinct from explicitly reversible system actions | Source and tests |
| Data bounds | Document file/archive sizes, parser limits and supported formats | Parser code and schemas |
| Trust | Hashes and hardware IDs are not described as authenticity or safety proof | Wording review |
| Privacy | No private identifiers, serials or user-local paths in examples | Fixture/diff review |
| Visual provenance | Screenshot means real application capture; diagram means illustration | Asset review and captions |
| Adaptive rendering | Light/dark hero pair shares dimensions and fallback text is meaningful | SVG assets and picture block |
| Commands | Launch, test and CLI examples match the current tree | Python modules and tests |
| Localization | All four languages retain equivalent safety scope and commands | README comparison |
| Navigation | Important documents appear in the index and information map | Documentation map |
| Review | Links, Mermaid, images and git diff --check are checked | CI/local validation |

## Maturity vocabulary

- **Implemented:** behavior exists in source.
- **Partial:** only a subset is implemented.
- **Simulated / advisory:** a model or recommendation, not a system action or certification.
- **Planned:** design intent without an available implementation.
- **Verified:** a named check passed on a stated revision/environment.

## Publication checklist

Update the feature matrix and owning technical contract when behavior changes. Do not convert a candidate match, hash, heuristic or passing test into a broad safety claim. Preserve the distinction between package inspection and the separate gaming power-plan session.
