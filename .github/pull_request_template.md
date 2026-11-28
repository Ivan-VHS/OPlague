This PR explains one focused change to OPlague's inspection, evidence or defensive tooling.

## What changed
Describe what the tool now observes, validates or reports, and identify the inputs it consumes.

## Why
What concrete inspection or assurance gap does this close?

## Implementation and evidence
- [ ] Input formats, parser limits and resource bounds are documented.
- [ ] Malformed, truncated, stale and unsupported inputs are handled explicitly.
- [ ] Evidence provenance and comparison rules are clear.
- [ ] Hash integrity, signature validity, publisher trust and compatibility are kept separate.
- [ ] Read-only behavior is preserved unless a separately reviewed scope explicitly says otherwise.

## Verification
List exact test commands and CI runs. Include negative fixtures and boundary cases where relevant. Mark anything not run as pending.

## Read-only and privacy boundaries
- [ ] No host driver, firmware, registry or service state is changed.
- [ ] Packages are not installed, extracted or executed by inspection-only tools.
- [ ] Candidate matches are not presented as a compatibility or safety verdict.
- [ ] Serial numbers, secrets and personal identifiers are not added to fixtures or reports.
- [ ] Known false positives and unsupported formats are described.

## Dependencies
Link related PRs and branches, including the source of any shared ABI or contract.
