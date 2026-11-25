# Reaper native expression integration

OPlague remains a Python-based, read-only driver workbench. Its Windows device inventory, package inspection, evidence collection and UI are not rewritten into a general-purpose expression language.

The impact-profile module has a narrowly scoped optional integration with Reaper's native C17 runtime. Reaper evaluates the sum of the five validated ordinal dimensions for each profile; OPlague retains ownership of registry loading, validation, presentation and stable tie-breaking.

## Explicit usage

Build Reaper's native shared library:

```sh
cmake -S /path/to/Reaper -B /path/to/Reaper/build -DCMAKE_BUILD_TYPE=Release
cmake --build /path/to/Reaper/build --parallel
```

Then pass the exact library path to OPlague:

```sh
python -m oplague --rank-total-native --reaper-library /absolute/path/to/libreaper_ffi.so
```

On Windows, use the absolute path to the corresponding built DLL; on macOS, use the built dynamic library path. The filename is platform/toolchain-dependent.

The bridge in `tools/reaper_ffi.py` checks ABI version 1, rejects relative and symlink paths, validates UTF-8 and a 1 MiB expression bound, and never searches PATH, environment variables, the current directory or implicit plugin locations. Loading a shared library executes native code, so only a trusted library explicitly selected by the operator should be supplied.

The optional operation is purely ordinal: it sums five prevalidated integers in the range 1..5. It is not a hardware measurement, driver score, compatibility verdict, installation decision or authorization. All device and package operations remain read-only.

Without the optional call, all existing OPlague functions continue to use their existing Python implementations. There is no runtime download and no required shared-library dependency.

## Shared language/toolchain contract

Reaper's source frontend, МОСТ aliases, Python reference runtime, source-span model and canonical IR belong to the Reaper repository. OPlague deliberately consumes only the separately documented ABI v1 scalar-expression and exact selfhood-lookup entry points. It does not parse `.rpr` files itself and does not embed Reaper Studio or the general Python runtime.

The ABI functions used here do not expose the native AST/IR structs, so adding source provenance to the compiler frontend does not expand the OPlague call surface. The operator-selected library path, ABI version check, source-size limits and ordinal input validation remain mandatory. The expression result is a deterministic arithmetic total over already validated dimensions, not a hardware score, measurement, security assessment or driver recommendation.
