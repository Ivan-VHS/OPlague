# Mental Wellbeing & Depression Awareness v1 — Code Safety Standard

**Policy ID:** `mental-wellbeing-code-safety.v1`  
**Applies to:** OPlague Windows device inventory, INF/ZIP/UDRV inspection, reports and federation  
**Status:** Engineering guardrails; not a clinical protocol

## Why this exists

This standard translates the non-stigmatizing, help-seeking and self-care themes in the supplied *Mental Wellbeing & Depression Awareness v1* material into engineering safeguards. The supplied transcript contains only opening and closing segments; its missing middle is not reconstructed. Personal stories, sponsor material, timestamps and the quoted prevalence figure are not clinical evidence or executable rules.

OPlague is a read-only device and driver-package workbench, not a mental-health product. Hardware state must never be used to diagnose, screen, score or infer a person's psychological state.

## Non-negotiable safeguards

- **No diagnosis or inference:** never infer depression, distress, disability, motivation or psychological traits from device inventory, driver status, hardware identifiers, system errors, package contents or usage patterns.
- **No medical advice:** do not recommend medication, treatment, dosage, therapy or clinical decisions. Do not describe hardware or driver compatibility as a measure of human wellbeing.
- **Read-only system boundary:** preserve the no-install, no-load, no-flash and no-driver-modification design. Inspection must not execute packages or scripts.
- **Privacy by default:** hardware IDs, serial-like values, host names, paths and timestamps may identify a device or person. Minimize them in exports and logs; pseudonyms are not anonymization guarantees. Do not introduce health or personal-state fields.
- **Archive and parser safety:** preserve entry-count, path traversal, decompressed-size, compression-ratio, manifest and payload bounds. Fail closed on malformed INF, ZIP or UDRV input.
- **No telemetry:** do not upload inventories, package contents, reports, identifiers or wellbeing-related text. Any future optional telemetry requires a separate informed opt-in and documented retention/deletion controls.
- **Respectful wording:** status messages describe evidence and uncertainty, never blame or characterize the operator.
- **Blameless engineering:** security incidents and device-inspection failures are described through reproducible conditions and corrective actions, not personal fault or health assumptions.

## OPlague-specific threat model

| Surface | Required protection |
|---|---|
| Windows Plug and Play inventory | Fixed read-only queries; minimize identifiers; no inference about a user |
| INF / ZIP inspection | No extraction or execution; bounded paths, entries, sizes and compression |
| UDRV manifests and payloads | Validate declared size, hash, count and path; never install or load |
| Device graph / compatibility | Exact matches are candidate evidence only, not certification or a clinical signal |
| Batch reports / federation | Minimize identifiers, preserve provenance and uncertainty, redact local paths |
| Metric Lab / profiles | Explain metrics as technical comparison only; never score people or wellbeing |

## Change acceptance checklist

A change touching inventory, package inspection, compatibility, reports, federation or persistence is ready only when:

1. Device and package inputs remain read-only and bounded.
2. No package, script, driver or manifest-directed payload is executed.
3. Personal identifiers are minimized and sensitive values are not logged by default.
4. No psychological or medical inference is introduced.
5. Reports separate observed facts, derived metrics and uncertain candidate links.
6. Tests cover path traversal, oversized archives, malformed metadata and safe failure.

## Automated enforcement

`mental-wellbeing-code-safety.v1.json` is the machine-readable policy contract.  
`scripts/check_mental_wellbeing_guardrails.py` validates required prohibitions, OPlague-specific read-only boundaries and this document. The dedicated GitHub Actions workflow runs the validator on pushes and pull requests. This policy gate does not replace archive fuzzing, package-security review or privacy review.

## Scope and limitations

This is a software privacy and safety standard, not diagnosis, screening, counselling, crisis response or treatment guidance. OPlague must not infer health from a computer's hardware or present inspection output as clinical information.
