# Early Mathematics Content Assurance Profile v1

**Status:** proposed read-only inspection profile; generic educational-pack validation is not currently claimed as implemented.  
**Owner:** OPlague owns structural and provenance evidence only. DAK remains the authority for curriculum, child UX and age-appropriate supervision.

## 1. Purpose and non-goals

DAK may import a versioned, offline early-mathematics content pack. Such files are untrusted input even when they contain only text. OPlague can eventually extend its bounded, read-only inspection approach to report package structure, resource limits, schema identity and provenance metadata.

OPlague must not claim that a pack is pedagogically correct, suitable for a particular child, medically safe, malware-free or cryptographically trusted merely because it parses or matches a schema.

## 2. Threat model

Treat the package, manifest, file names, text, metadata and declared resource sizes as attacker-controlled. Relevant risks include:

- oversized JSON, excessive nesting, duplicate keys, non-finite numeric tokens and malformed UTF-8;
- duplicate activity identifiers or conflicting manifest entries;
- path traversal, absolute paths, symlinks and archive entries escaping the package root;
- archive bombs, excessive entry counts, giant individual files and decompression ratios;
- remote URLs, executable scripts, HTML event handlers or unexpected binary payloads embedded in a text-only pack;
- misleading hashes, claimed publisher names or unverifiable signatures;
- hidden personal data in metadata, file names, image EXIF or audio tags.

## 3. Read-only validation pipeline

A future implementation should follow this order:

1. Accept only an explicitly selected local file or folder.
2. Check file type, total size, entry count and all size limits before parsing.
3. Parse metadata with duplicate-key rejection, strict UTF-8, finite-number checks and bounded nesting.
4. Validate the declared pack schema identifier and supported version.
5. Validate unique IDs, age-range bounds, allowed learning domains and safety fields.
6. Reject executable or remote content and path references that escape the declared package root.
7. Report unknown fields, unsupported resources and missing provenance as explicit findings.
8. Export a report only after explicit user action.

Inspection must not extract archive payloads to arbitrary paths, execute scripts, load plugins, install packages or mutate the source.

## 4. Resource budgets

Resource limits must be explicit, versioned and enforced before allocation. At minimum, a profile must bound:

- total package bytes;
- number of entries and nesting depth;
- manifest and activity count;
- per-field and total text length;
- per-resource bytes and total unpacked bytes, if an archive format is later supported;
- parsing time or operation count.

No default should be interpreted as unlimited. An unknown format or exhausted budget produces an incomplete/unknown result, not a clean verdict.

## 5. Verdict vocabulary

Use narrow, evidence-backed states:

- **schema_match:** the declared schema identifier and structural rules match a supported version.
- **schema_mismatch:** required fields, field types, enumerations or cross-field constraints fail.
- **resource_limit:** a configured size, depth, count or operation budget is exceeded.
- **unsafe_reference:** a path or external reference violates the package policy.
- **unknown:** evidence is insufficient, a format is unsupported or a required verifier is unavailable.

These states describe inspection evidence only. They do not certify the educational content, guarantee the absence of malware or authorize installation.

## 6. Child-safety and privacy checks

Structural checks should flag missing supervision instructions for activities involving water, small parts, food/allergens or outdoor materials. The authoritative DAK schema determines required fields; OPlague reports evidence and does not rewrite the activity.

A pack should contain no learner records. Reject or flag names, birth dates, voice recordings, location history, biometric identifiers and other unnecessary personal data. Image and audio resources, if ever supported, must have a documented metadata-stripping policy and remain local.

## 7. Trust and integrity

A hash can show whether bytes changed relative to a recorded digest; it does not establish who published them. A publisher field is a claim, not proof. Cryptographic signature verification requires an implemented verifier, a pinned trust store, key lifecycle rules and test vectors. Until those components exist, signature state must remain unknown and must not be represented as verified.

## 8. Integration boundaries

- DAK validates the content schema before rendering and owns the child-facing safety and accessibility policy.
- Reaper validates mathematical semantics if an activity contains a formal operation; this is independent of package integrity.
- Pytyliki is an optional numerical provider and must never receive learner identity.
- VentuSample may provide local generated audio examples; audio assets are still bounded untrusted files.
- OPlague is an optional read-only audit path, not a runtime prerequisite for a basic offline activity.

No package is executed as code. No new kernel, driver, firmware or privileged service capability is introduced by this profile.
