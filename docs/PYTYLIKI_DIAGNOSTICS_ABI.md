# OPlague — Pytyliki Diagnostics ABI Consumer

**Status:** partial native integration; dependent on Pytyliki diagnostics ABI v1 PR #264  
**Implementation:** Rust 2021, no third-party crates  
**Boundary:** explicit local shared-library path; synchronous calls only

## What is implemented in this slice

`crates/pytyliki-diagnostics-abi` is a narrow Rust consumer for the additive Pytyliki diagnostics envelope. It defines the `#[repr(C, align(8))]` record, checks both ABI versions, initializes caller-owned diagnostic storage and calls the real `pytyliki_v1_distance_f64_ex` symbol.

The crate is an integration component, not a claim that the entire OPlague application has migrated to Rust/Slint. The existing application and Python adapter remain unchanged in this slice.

## Memory and execution contract

- The caller owns the Rust slices, output scalar and diagnostic record.
- Slice pointers are borrowed only for the duration of one synchronous FFI call.
- The wrapper does not expose raw native pointers or transfer ownership.
- The build requires `PYTYLIKI_LIB_DIR`; it never performs an implicit library search.
- The shared library is built from the exact Pytyliki commit pinned in the workflow.
- No filesystem, network, hardware, driver or device mutation is performed by this adapter.
- No call is suitable for an audio or other hard real-time callback.

## Binary verification

The Rust tests assert the C layout: 144-byte size, 8-byte alignment and fixed offsets for `code`, `source_offset`, `detail`, `message_size` and `message`. They then call the real C shared library for successful distance evaluation, non-finite input, zero dimension and the 4096-element limit.

The workflow first builds and runs Pytyliki's C11 ABI tests, then compiles and tests the Rust consumer against that same build. A mock library is not used as evidence of ABI compatibility.

## Dependency and release boundary

The workflow pins Pytyliki by commit SHA rather than following a moving branch. Update the pin only after the Pytyliki ABI commit changes and its C11 CI passes. The diagnostics interface remains partial until both repositories' exact-SHA checks pass and the dependency PRs are merged.
