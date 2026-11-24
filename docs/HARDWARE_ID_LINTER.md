# Hardware ID linter

OPlague includes a local, format-only linter for Windows Plug and Play identifiers.

## Usage

From the repository root:

    python -m tools.hardware_id_linter "PCI\VEN_8086&DEV_15F3&SUBSYS_00008086&REV_03"
    python -m tools.hardware_id_linter --json "USB\VID_046D&PID_C52B&REV_1201"

The command accepts one or more quoted identifiers. It returns exit status 0 when every identifier is structurally valid and 1 when at least one identifier is rejected. Argument errors use the normal argparse exit status.

## What is checked

- The bus prefix must be one supported by OPlague's existing identifier normalizer.
- Path components must be non-empty, bounded, and free of traversal or unsupported characters.
- PCI identifiers require four-hex-digit VEN and DEV fields. Optional SUBSYS, REV, and CC fields are checked when present.
- USB identifiers require four-hex-digit VID and PID fields. Optional REV and MI fields are checked when present.
- Duplicate or malformed attributes are reported.
- ACPI and other supported bus families retain opaque identifiers when OPlague has no sufficiently narrow field rule; the linter does not guess their meaning.

Additional path components are reported separately because a value that resembles a device-instance path should not be presented as an exact hardware-ID string.

## Limits

This is syntax validation only. It does not query the host, prove that a device exists, resolve manufacturer names, establish driver compatibility, inspect package safety, or install or modify anything. Unknown fields are preserved as observations rather than rejected merely because this version does not interpret them.

The linter is offline and uses the existing bounded identifier normalization path from tools.device_graph.
