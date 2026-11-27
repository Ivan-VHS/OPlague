# Pytyliki Iron Syntax diagnostics metadata v1

**Canonical vocabulary owner:** Pytyliki  
**Consumer:** OPlague diagnostics ABI crate  
**Schema:** `pytyliki.iron-syntax-ast.v1`  
**Version:** `1.0.0`

The diagnostics crate validates source provenance for Iron AST records after a trusted upstream component has produced the versioned AST. It checks schema, version, canonical owner, record IDs (0–19), bounded record count, source spans, line/column values, and monotonic source order.

The new Rust module is additive and does not change `DiagnosticV1`, its C layout, ABI version, or existing native calls. It does not lex or parse Iron text and does not lower markers to device instructions.

**Security boundary:** `execution_performed` must be `false`. The validator is metadata-only; a valid record is not an authorization to access hardware, MMIO, DMA, drivers, firmware, privileges, or device state. OPlague remains an observer/diagnostics consumer.

The module's unit tests cover the twenty record identifiers and invalid schema/version/owner, execution flags, bounds, source spans, positions and source order. The existing ABI workflow runs the Rust crate tests against the real Pytyliki C shared library.
