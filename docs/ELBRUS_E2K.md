# Elbrus E2K host support

## Scope and safety boundary

OPlague inspects Windows INF/ZIP driver packages and presents evidence; it does not install,
load or modify drivers. On Elbrus Linux, the OS-neutral package-analysis layer can run under
Python 3.10+ where the required standard library is available.

| Capability | E2K Linux status |
|---|---|
| INF text parsing and architecture-decoration extraction | Available; metadata-only |
| ZIP path, size, compression-ratio and SHA-256 inspection | Available; metadata-only |
| Comparison of declared Windows targets | Available as a static report; not an installability verdict |
| Host platform report | Identifies MCST E2K separately from Windows driver target architectures |
| Local Windows Plug-and-Play enumeration | Windows-only; unavailable on Elbrus Linux |
| Windows desktop workbench packaging | Windows-only; not included in the E2K verification job |
| Driver loading / installation | Not implemented on any platform |

**Important:** E2K is not a Windows INF target decoration or a PE machine type in this project's
Windows target catalogue. The E2K host must therefore remain `unknown/not-applicable` for a
Windows-driver architecture match. Adding an E2K host profile must never turn an x86/ARM Windows
driver into a false compatible match.

## Verify on native Elbrus Linux

```sh
bash scripts/elbrus/verify-e2k-host.sh
python -m tools.architecture_profiles --host-info --json
```

The verification script checks that Python reports an E2K host, compiles the platform-neutral
inspection modules, and runs the architecture-profile tests. It does not attempt to query Windows
PnP through PowerShell/CIM, start the Windows GUI, or execute inspected package contents.

## Toolchain and operating-system context

The MCST SDK provides LCC and platform development tools, but OPlague's host-side package parser
does not need a native compiler. For related native components use the official MCST toolchain
matched to the installed Elbrus Linux release.

- [MCST SDK](https://www.mcst.ru/SDK)
- [MCST Elbrus Linux platform matrix](https://www.mcst.ru/elbrus_linux)
- [MCST developer downloads](https://dev.mcst.ru/download/)

## CI

`.github/workflows/elbrus-e2k.yml` is a manual workflow for a self-hosted runner labelled
`self-hosted, linux, e2k`. The normal Windows workflow and Windows-only PnP behavior are retained.
