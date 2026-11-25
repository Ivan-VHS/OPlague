# Documentation control

| # | Rule |
|---:|---|
| 1 | implemented claims cite code/tests |
| 2 | no private identifiers or local paths |
| 3 | separate implemented / partial / planned |
| 4 | document supported formats and limits |
| 5 | version breaking interfaces |
| 6 | verify links, examples, numbers and exclusions |

## Internal information architecture

| # | Rule | Acceptance |
|---:|---|---|
| 7 | Topic ownership | Every important page belongs to one primary topic hub and appears in the central information map. |
| 8 | Navigation depth | Important device, driver and security contracts are reachable within three to four steps from the root README. |
| 9 | No orphan pages | Every important page has at least two useful inbound paths, normally the central catalog and its topic hub. |
| 10 | Contextual links | Link pages when they describe a real evidence flow, compatibility relationship or inspection workflow. |
| 11 | Descriptive anchors | Use the target module or contract name; avoid vague labels and keyword repetition. |
| 12 | Scope consistency | README, topic hubs and detailed documents agree on read-only behavior, trust boundaries, input handling and maturity. |
| 13 | Canonical targets | Use direct relative paths in this repository and canonical HTTPS links across repositories; avoid avoidable redirects and duplicate targets. |
| 14 | Breadcrumbs | Topic hubs link to the documentation home and parent information map; add breadcrumbs to new deep-level pages. |
| 15 | Link density | Keep links useful and contextual; avoid repetitive link blocks and link-heavy paragraphs. |
| 16 | Publication propagation | Add new documents to their topic hub and catalog in the same change, then link them from relevant existing material. |
| 17 | Link maintenance | Check renamed and removed paths and periodically audit for broken or obsolete links. |
| 18 | Measurement | Measure navigation only where a supported published documentation surface offers privacy-respecting analytics; do not invent GitHub Markdown telemetry. |
| 19 | Accessibility | Use descriptive links, normal same-tab internal navigation and targets usable on small screens. |

The [information architecture map](INFORMATION_ARCHITECTURE.md) is the navigation source for this repository. It does not override code, tests or schemas and does not extend the product beyond its documented read-only scope.
