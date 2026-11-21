# UDRV container format v1

This document defines the initial package-inspection contract implemented by
tools/udrv_inspector.py. It is a package structure and integrity format, not
a universal driver-installation format.

## Container layout

A package is either a directory or a ZIP archive with this layout:

    package.udrv/
    ├── manifest.json
    └── payload/
        └── vendor/
            └── driver.inf

The manifest is UTF-8 JSON. Its v1 core schema is:

    {
      "format": "udrv",
      "format_version": 1,
      "id": "vendor.device.driver",
      "version": "1.2.3",
      "payload": [
        {
          "path": "payload/vendor/driver.inf",
          "size": 42,
          "sha256": "64 lowercase hexadecimal characters"
        }
      ]
    }

The id is limited to 128 ASCII letters, digits, dots, underscores, and hyphens.
The version is a non-empty whitespace-free string up to 128 characters.
The payload must contain at least one entry. Paths must be canonical relative
POSIX paths below payload/; absolute paths, parent traversal, backslashes,
duplicate case-insensitive names, symlinks, and special files are rejected.

Every payload entry declares its exact byte length and SHA-256 digest.
The archive or directory must contain exactly the declared payload files:
missing and undeclared files both fail validation. The root manifest.json is
the only file outside payload/.

## Resource limits

| Resource | Limit |
| --- | ---: |
| Manifest | 4 MiB |
| Archive entries | 10,000 |
| One payload file | 512 MiB |
| Total declared payload | 2 GiB |
| Hash read buffer | 1 MiB |

Encrypted ZIP entries are not accepted. The inspector streams payload content
through SHA-256 and does not extract archive members to disk.

## Security and trust boundary

A matching hash proves that the inspected bytes match the manifest, not who
created the manifest. Authenticity requires a separately defined signature
and trusted-key policy. Compatibility and safe installation require separate
OS, device-ID, signing, and vendor-policy validation. The inspector never
executes, loads, or installs a driver and does not treat metadata as authority.

## Compatibility policy

format_version is mandatory. A future major format version must be rejected
until its schema and validation semantics are implemented. Unknown metadata
fields may be retained by producers, but v1 consumers must not infer safety or
compatibility from fields they do not understand.
