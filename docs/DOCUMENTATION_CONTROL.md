# Documentation control

**Baseline date:** 2026-11-26 · **Scope:** README locales, device discovery, package inspection, compatibility evidence, telemetry, security and releases.

## Local publication gates

| Gate | Acceptance |
|---|---|
| Identity | Exact product name, technical position, status, version declaration, stack and license. |
| Platform | Windows-only live PnP; offline workflows described separately. |
| Architecture | Input → bounded inspector/query → normalized evidence → local report. |
| Read-only | No install/remove/enable/unload, driver load, firmware write or device mutation. |
| Untrusted input | INF/ZIP/UDRV/report paths, sizes, entry count and compression limits documented. |
| Compatibility | Exact ID is candidate evidence only, never certification or ranking. |
| Signature | Authenticode metadata is not a device-safety verdict; SHA-256 is not publisher authentication. |
| Telemetry | Provider and missing values are source-attributed; no sensor presence is inferred. |
| Rust component | Diagnostics ABI crate is a bounded integration, not a full application migration. |
| Security scanner | Static repository assurance is not endpoint protection or quarantine. |
| Release | Draft/published state and approval environment documented; no invented release version. |
| Localization | EN/RU/UK/ZH-CN facts and section order aligned. |
| Navigation | Every docs Markdown page cataloged with valid local paths. |
| Legal | Apache-2.0 and upstream attributions preserved. |
| Maintenance | README, schemas, tests and workflow docs updated together on contract changes. |

## README review mapped to the 50-point standard

### Identity and first screen (1–10)
1. Exact repository name and concise technical statement.
2. Metadata for status, version, platforms, stack and license.
3. Evidence-backed name/API/architecture history.
4. Actual diagram or screenshot with truthful version/environment caption.
5. Purpose, guarantees and exclusions in the opening.
6. Reproducible numbers only.
7. Related projects and versioned integration boundaries.
8. Contents list for long/multi-subsystem README.
9. Release chronology belongs in its own section.
10. Consistent technical language.

### Chronology and releases (11–20)
11. Verifiable milestones, not aspirational timelines.
12. Disclose material rewrites or stack changes only when evidenced.
13. Link tags, dates and revisions.
14. Distinguish stable, experimental and draft artifacts accurately.
15. Show contract compatibility and replacements.
16. Branch lifecycle only when maintained.
17. Keep release chronology separate from API reference.
18. Version-labelled matrices where appropriate.
19. Remove stale roadmap summaries.
20. Link milestones to artifacts and migration docs.

### Architecture and contracts (21–30)
21. Dedicated architecture and principles section.
22. Explain trade-offs and explicit non-goals.
23. Short, precise paragraphs.
24. Balance prose, tables, diagrams and commands.
25. Deep protocol detail in docs/.
26. Separate contract, implementation and proposal.
27. Keep locale structure and terminology aligned.
28. Distinguish process, service, package, module and interface.
29. Every section answers an engineering question.
30. Balance depth with quick onboarding.

### Breaking changes and limitations (31–40)
31. Disclose defects, bottlenecks, contract changes and limits.
32. Highlight data-loss, privilege and compatibility risks.
33. Explain why interfaces changed.
34. Separate app limits from OS/toolchain/dependency limits.
35. Compare only through evidence or architecture.
36. List unsupported platforms and workloads.
37. Provide verified workarounds and migration guidance.
38. Retire limitations after tests verify fixes.
39. Keep issue triage out of README.
40. Clarify trust, concurrency, device access and network boundaries.

### Sources and maintenance (41–50)
41. Reproducible benchmark methodology.
42. Separate API/schema, architecture, examples, RFCs and standards.
43. Check all links before a release.
44. State exact versions for schemas, standards and algorithms.
45. Cite audits with issuer/date/scope.
46. Link contribution and vulnerability disclosure paths.
47. Link actual legal/community files and state when absent.
48. Preserve third-party license attribution.
49. Change docs with CLI, schema, configuration and build updates.
50. Test setup commands in a clean environment.

## Evidence vocabulary

- **Specified:** contract exists, behavior is not claimed.
- **Planned:** accepted but not implemented.
- **Partial:** bounded behavior exists with explicit omissions.
- **Implemented:** behavior exists in source and a workflow.
- **Verified:** acceptance is proven in a named environment/revision.

A hardware-ID candidate is not a compatibility verdict. A file hash is not a signature. Signature metadata is not a safety certification. A local source scanner is not endpoint defense.

## Before publication

- [ ] Re-check source/tests/schema and trust boundaries.
- [ ] Verify every local Markdown path and image target.
- [ ] Verify test and CLI commands in a clean Python environment.
- [ ] Keep the four root README translations aligned.
- [ ] Confirm release draft/published state from the workflow.
- [ ] Preserve Apache-2.0 and third-party notices.
