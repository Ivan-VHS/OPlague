# Concatenation and package composition contract

**Status:** architecture contract for the early OPlague implementation. This document does not claim that package composition is already available in the desktop application.

## Purpose

OPlague must distinguish byte-level concatenation from semantic package merging. Joining byte spans is a deterministic storage operation; combining driver packages is a validation workflow that must preserve provenance and compatibility evidence.

## Required operations

| Operation | Contract |
|---|---|
| Byte concatenation | Join ordered byte spans without text decoding or implicit conversion |
| Text concatenation | Join UTF-8 text with explicit encoding and size limits |
| Manifest composition | Combine compatible manifest sections while preserving source package identity |
| Payload composition | Add payload entries by normalized relative path and content digest |
| Metadata aggregation | Retain provider, version, hardware IDs, OS targets, signatures and source provenance |
| Package assembly | Emit a deterministic container only after all validation gates pass |

## Safety and conflict rules

1. Never concatenate executable driver payloads and treat the result as an installable driver. Composition creates a bundle of independently identified files, not a new binary.
2. Normalize archive paths before comparison. Reject absolute paths, parent traversal, drive-qualified paths, reserved device names and duplicate normalized paths.
3. Calculate and verify a cryptographic digest for every payload before composition. Deduplicate only byte-identical content; never infer equivalence from filenames.
4. Preserve each file's original path, source package, provider, version and digest in the composed manifest.
5. Reject conflicting entries by default. A conflict-resolution policy must be explicit, deterministic and recorded; silent last-writer-wins behavior is forbidden.
6. Keep hardware IDs, OS version constraints, architecture, signing state and catalog evidence attached to their originating package. Do not broaden compatibility by unioning incompatible claims.
7. Treat imported manifests, archives and metadata as untrusted input. Enforce entry-count, per-entry size, total expanded size, path-length and nesting-depth limits before allocation or extraction.
8. Build into a temporary destination, validate the complete result, then atomically publish it. On failure, discard the temporary output and leave source packages unchanged.

## Proposed API boundary

The implementation should expose separate operations rather than one ambiguous `concat` call:

- `concat_bytes(parts, limits) -> byte_buffer`
- `concat_text(parts, encoding, limits) -> text`
- `compose_manifests(manifests, conflict_policy) -> manifest_result`
- `compose_payloads(packages, limits) -> payload_plan`
- `validate_composition(plan) -> validation_report`
- `assemble_container(plan, destination) -> package_result`

All operations return structured errors with the source package and entry path where available. The package assembler must require a successful validation report tied to the exact plan digest.

## Determinism and verification

For identical ordered inputs and policy, composition must produce identical normalized manifests and payload ordering. Tests must cover empty input, one input, repeated identical files, conflicting paths, path traversal, invalid encodings, missing digests, size-limit boundaries, incompatible hardware/OS claims, interrupted assembly and cleanup after failure.

## Integration sequence

1. Implement the bounded byte/text primitives.
2. Define and version the manifest composition schema.
3. Add safe path normalization and digest verification.
4. Implement conflict-aware manifest and payload composition.
5. Add transactional container assembly.
6. Integrate the workflow into the desktop UI as a review-first operation; installation remains a separate privileged action.

No installation, signature bypass, compatibility override or source-package mutation is implied by concatenation.
