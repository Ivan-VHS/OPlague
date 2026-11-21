# Project stewardship and anonymous operating principles

**Status:** normative project-governance guidance. It strengthens planning and communication; it does not authorize new device, driver, registry or firmware operations.

## Purpose

Maintain a trustworthy device and driver diagnostics workbench through disciplined inspection, transparent decisions, privacy-aware reporting and evidence-led communication. Confidence must come from inspectable evidence and explicit limits—not from dramatic warnings, unsupported compatibility claims or promotional reach.

## Operating principles

1. **Operator intent first.** Inspection and export are distinct actions. Explain the purpose, data scope and consequences before an operator confirms an export.
2. **Read-only means read-only.** Inventory, comparison and dry-run analysis must not mutate device, driver, service, registry, firmware or kernel state.
3. **Evidence before verdict.** Distinguish observed identifiers and package metadata from inferred compatibility, trust or health. Missing evidence must remain unknown rather than becoming a green status.
4. **Privacy by minimization.** Collect and export only necessary fields. Explain the difference between anonymization and pseudonymization; keyed pseudonyms can remain linkable.
5. **Accountability by role.** Assign decisions to an explicit maintainer or operator role. No personal status, popularity, gender, age or relationship grants technical authority.
6. **Credibility before attention.** Do not create fear, false urgency or sensational incident labels to increase engagement. Warnings must be proportional to verified risk.

## Decision record

For changes to inventory collection, package inspection, compatibility logic, identity handling or export formats, record:

- **Operator problem and intended outcome.**
- **Decision owner and affected platform boundary.**
- **Collected fields, provenance and privacy impact.**
- **Evidence:** exact identifiers, package metadata, hashes, test fixtures and unsupported conditions.
- **Alternatives and uncertainty.**
- **Failure handling, rollback and review trigger.**

Changes that expose additional device identity or enable new side effects require an explicit privacy and safety review before implementation.

## Execution rhythm

1. **Intake:** classify reports by safety, privacy, system impact, affected platform, reproducibility and confidence.
2. **Inspect:** use bounded, non-mutating queries and preserve source provenance.
3. **Normalize:** retain original evidence where permitted and make transformations explicit.
4. **Compare:** match only exact, documented keys; distinguish candidate relationships from confirmed compatibility.
5. **Export:** preview fields, obtain explicit confirmation and use a protected destination.
6. **Review:** validate fixtures, tests, documentation and the actual side-effect boundary before release.

Keep operator-facing workflows predictable: inventory → evidence → comparison → review → explicit export. Do not make destructive controls appear to be ordinary inspection actions.

## Communication, feedback and public credibility

- Label observations, inference, confidence and unknown values separately.
- A package digest establishes byte integrity, not publisher identity, safety or compatibility.
- A compatibility graph edge is a reviewable candidate, not an automatic driver recommendation.
- PnP pseudonyms are not anonymous when a protected key permits correlation. Explain key custody and retention in plain language.
- Prioritize feedback by safety impact, affected systems, reproducibility, confidence and remediation cost.
- Report incidents with verified scope, affected versions, safe mitigations and a next update. Do not publish personal device identifiers or secrets in public issues.
- Avoid fear-based marketing, unsupported health scores, sensational labels and claims of live diagnosis without the required telemetry.

## Incident and conflict protocol

Use **stabilize → assess → contain → communicate → recover → review**. Stop or isolate the affected read-only workflow if it leaks data or produces misleading output; preserve minimal diagnostic evidence; identify affected exports; communicate the known scope; fix and test the issue; then document prevention actions. Security reports and private identifiers belong in approved private channels.

## Sustainable stewardship

Maintain a risk register covering privacy, identifier correlation, package parsing, platform coverage, false positives, export handling and recovery. Give each risk an owner, mitigation and review date. Keep personal, household and family details out of device snapshots, logs, test fixtures and release examples. Contributors should be able to hand off work without exposing private data or relying on one individual.

Review standards must be fair and role-neutral. Disagreement is resolved through evidence, safety constraints and documented authority—not personal pressure or social status.

## OPlague-specific acceptance gates

- Device inventory and package inspection remain read-only; a new feature must not imply driver installation, removal, enablement, rollback, signing or firmware changes.
- Imported packages and metadata are untrusted input. Apply path, size, decompression and parsing bounds; never execute package payloads during inspection.
- Compatibility decisions use exact normalized hardware identifiers and report missing or ambiguous evidence explicitly.
- Snapshot export requires explicit operator confirmation and minimizes sensitive fields.
- Ephemeral keyed pseudonyms remain the default unless cross-snapshot correlation is deliberately enabled with protected key handling.
- A health or trust status remains unknown when source coverage is incomplete; do not manufacture certainty from missing telemetry.

## Release review checklist

- [ ] The workflow is clearly described as inspection, comparison or export.
- [ ] No device, driver, registry, service, firmware or kernel mutation was introduced implicitly.
- [ ] Inputs, paths, payloads and batch sizes are bounded.
- [ ] Evidence, confidence, unknowns and privacy implications are visible.
- [ ] Export consent and identifier handling are explicit.
- [ ] Tests cover malformed input, incomplete evidence and failure paths.
- [ ] Public warnings and claims are proportional to verified behavior.

**Interpretation rule:** this standard does not turn inspection into device management, pseudonymization into anonymity or candidate matching into a compatibility verdict.
