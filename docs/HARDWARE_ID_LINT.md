# Hardware ID linter

Run a local syntax inspection with:

```sh
python tools/hardware_id_lint.py "PCI\VEN_8086&DEV_15F3&SUBSYS_00008086&REV_03"
python tools/hardware_id_lint.py "USB\VID_046D&PID_C534" --json
```

The linter normalizes case and slash direction, splits known structured bus fields, checks field widths and hexadecimal characters, and explains what each parsed field represents. PCI and USB vendor IDs are deliberately not translated into manufacturer names: the repository does not embed a stale or incomplete vendor catalogue. Unknown fields are preserved and reported as uninterpreted rather than guessed.

The result answers only “does this string fit the syntax rules the linter understands?” It does not prove that a device exists, that a particular driver matches it, or that a package is safe. OPlague remains read-only; the linter does not access the Windows device manager, install anything, inspect package payloads or change the host.
