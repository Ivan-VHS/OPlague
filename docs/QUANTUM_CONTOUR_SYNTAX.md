# Quantum Contour Syntax (QCS)

QCS is a compact, Swift-inspired **systems-contract notation** for describing
the hardware domain, declared invariant and explicit handoffs around a block
of low-level code. OPlague includes a parser and metadata validator. QCS is not
a compiler, code generator, formal verifier or hardware-access layer.

## Minimal form

~~~swift
|~ domain:mmio(addr: 0x40021000), invariant:!, arch:arm64, budget:120ns ~|
func togglePin(register: UInt32, bit: UInt8) {
    register ^= 1 << bit
    register ->> writeMMIO(register)
}
|~ end ~|
~~~

A contour opens with |~ and closes with ~|. The body ends at |~ end ~|.
Swift-like body text is preserved, not compiled or executed.

## Header contract

| Attribute | Meaning | Rule |
| --- | --- | --- |
| domain | Hardware / execution domain | Required; one of 66 profiles |
| invariant | Declared certainty | Required: ! guaranteed, ? conditional, ~ asynchronous / unresolved |
| arch | Target architecture | Optional identifier, e.g. arm64 |
| budget | Declared execution budget | Optional duration, e.g. 120ns, 2us, 1ms or 800cycles |
| Other keys | Extension metadata | Preserved as non-empty text |

The operators ->> and <-~ are recorded, not executed. The first marks a
handoff; the second marks a borrow / ownership release. Neither proves
ownership correctness, timing, memory ordering or hardware behaviour.

## The 66 domain profiles

These are named views over one grammar, not 66 separate languages or compilers.

| # | Dialect | Domain | # | Dialect | Domain |
|---:|---|---|---:|---|---|
| 1 | SwiftCore-ASM | regfile | 34 | CryptoAsmSwift | crypto |
| 2 | KernelSwift | irq | 35 | EnclaveSwift | enclave |
| 3 | BareSwift | mmio | 36 | PermSwift | privilege |
| 4 | SliceSwift | page | 37 | HashSwift | hash |
| 5 | VoltSwift | pmu | 38 | RandSwift | trng |
| 6 | TrapSwift | trap | 39 | AuditSwift | trace |
| 7 | RingSwift | atomic | 40 | SandboxSwift | sandbox |
| 8 | SlabSwift | slab | 41 | SignSwift | verify |
| 9 | BootSwift | boot | 42 | MemTagSwift | memTag |
| 10 | BusSwift | bus | 43 | FaultSwift | tmr |
| 11 | CtxSwift | contextSwitch | 44 | KeySwift | secretZeroize |
| 12 | PtrSwift | pointer | 45 | GateSwift | logic |
| 13 | ArenaSwift | arena | 46 | ClockSwift | clock |
| 14 | BorrowSwift | borrow | 47 | FpgaSwift | fpga |
| 15 | CacheSwift | cache | 48 | DspSwift | dsp |
| 16 | DmaSwift | dma | 49 | AdcSwift | adc |
| 17 | PageSwift | mmu | 50 | PwmSwift | pwm |
| 18 | HeapSwift | heap | 51 | SpiSwift | spi |
| 19 | PackSwift | bitfield | 52 | I2cSwift | i2c |
| 20 | RefCountSwift | refcount | 53 | UartSwift | uart |
| 21 | ZeroCopySwift | zeroCopy | 54 | CanSwift | canFd |
| 22 | GuardSwift | stackGuard | 55 | FsmSwift | fsm |
| 23 | SimdSwift | simd | 56 | VmSwift | vm |
| 24 | LockSwift | spinlock | 57 | ByteSwift | bytecode |
| 25 | FenceSwift | fence | 58 | JitSwift | jit |
| 26 | FiberSwift | fiber | 59 | IrSwift | ir |
| 27 | PipeSwift | pipeline | 60 | MacroAsmSwift | macro |
| 28 | CoreSwift | affinity | 61 | HyperSwift | hypervisor |
| 29 | TimerSwift | timer | 62 | LinkSwift | linker |
| 30 | EventSwift | event | 63 | ElfSwift | elf64 |
| 31 | ActorAsmSwift | actorBox | 64 | DbgSwift | debug |
| 32 | BatchSwift | batchIo | 65 | ABI Swift | abi |
| 33 | WatchSwift | watchdog | 66 | QcsSwift | qcsMeta |

## Use

~~~bash
python -m tools.qcs validate path/to/example.qcs
python -m tools.qcs validate path/to/example.qcs --json
python -m tools.qcs dialects
python -m unittest discover -s tests -p 'test_qcs.py' -v
~~~

Input is limited to 1 MiB. Contours cannot nest, require a non-empty body and
must close explicitly. Errors include line and column information.

## Scope and safety

- No compilation, code generation, JIT, DLL loading, device I/O, register
  access, driver installation or privilege escalation is performed.
- invariant ! is a declaration, not a machine-checked proof.
- budget is metadata, not a real-time deadline guarantee.
- This dialect catalogue is separate from OPlague's existing 66-entry
  third-party systems-language / toolchain catalogue.
- Any future executable backend requires independent safety review, target
  validation, reproducible builds and tests.
