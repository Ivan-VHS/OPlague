# Reaper System Runtime ABI adoption contract

**Consumer:** OPlague  
**Provider:** Reaper System Runtime ABI v1  
**Status:** security boundary and proposed read-only integration profile.

## OPlague's trust model remains unchanged

OPlague is a local-first, read-only Windows device and driver-package inspection workbench. Imported INF, ZIP, UDRV, PE and related package content is untrusted evidence, not executable input. This integration must not turn OPlague into a driver installer or a generic privileged execution host.

Reaper System Runtime ABI v1 is a capability-gated host adapter interface with 42 operation descriptors. It does not itself implement OS services, and a registered operation is not proof of a working platform adapter.

## Preserve the existing Reaper FFI

- Keep the current Reaper FFI ABI v1 functions and their behavior.
- Keep explicit absolute-path selection of a trusted native library.
- Reject relative paths and symlink-based library indirection under the existing loading policy.
- Do not search PATH, environment variables, the current directory or implicit plugin folders.
- Do not load a library solely because an imported package or report names it.
- Keep OPlague's report generation, validation, ranking and device evidence ownership in OPlague.

The new System Runtime ABI version is independent from the existing Reaper scalar FFI ABI. OPlague must verify both versions separately when both interfaces are used.

## Initial capability profile

| Capability | Default |
|---|---|
| FS_HANDLE | Allow only for an operator-selected evidence root |
| FS_READ | Allow only for read-only inspection of that root |
| CLOCK | Allow for deterministic timestamps and elapsed-time measurement |
| CRYPTO | Allow only for local hash/MAC/entropy operations with explicit semantics |
| FS_WRITE | Deny |
| PROCESS_INSPECT / PROCESS_CONTROL | Deny |
| THREAD_CONTROL | Deny unless a separately reviewed, bounded local worker adapter requires it |
| SYNC | Deny unless strictly process-local and reviewed |
| NETWORK | Deny |
| MMIO / DMA / IRQ / port I/O | Not part of this ABI; deny through separate policy |
| Firmware and driver mutation | Deny; never exposed through this integration |

A capability may be granted only by an explicit local policy after validating the operation and target. An imported manifest cannot grant itself authority.

## Safe data flow

1. The operator selects an evidence file or trusted library.
2. OPlague validates path type, canonical location, file size and format.
3. OPlague parses the file as untrusted data using bounded readers.
4. An optional Reaper call receives only a small validated scalar or bounded byte payload.
5. OPlague validates the returned status and length before adding it to a report.
6. The report records provenance, ABI version and whether a value came from Reaper or the native OPlague path.

No Reaper call may mutate a driver package, device, registry setting, service state or firmware. No package content is passed to a shell or arbitrary process runner.

## Required tests

- ABI version mismatch is rejected before symbol use.
- Missing capabilities are denied before host dispatch.
- Oversized and malformed request/response buffers are rejected.
- An adapter that reports output larger than capacity is treated as a contract violation.
- Filesystem paths cannot escape the selected evidence root through traversal or symlinks.
- Package inspection continues to work when no Reaper library is installed.
- The driver inventory and package-inspection path remains read-only.

## Maturity

This page records a proposed consumer contract. It does not claim that OPlague currently calls System Runtime ABI v1, that the new services have a Windows adapter, or that a driver operation is implemented. Any future expansion beyond read-only evidence requires a separate security review and a new versioned contract.