# Authenticode inspection

OPlague can ask Windows PowerShell to inspect Authenticode metadata for selected
\`.cat\`, \`.sys\`, \`.dll\` and \`.exe\` files. The report includes Windows' signature
status and, when available, signer subject, issuer, certificate thumbprint,
validity dates and timestamp signer.

## What it does

- Calls the built-in \`Get-AuthenticodeSignature\` command locally.
- Sends selected paths as JSON on standard input; paths are not embedded in
  PowerShell source.
- Limits each request to 100 existing files and uses a bounded process timeout.
- Keeps the result as a read-only JSON report.

## What it does not prove

A \`Valid\` status is the operating system's Authenticode result for that file.
It does not certify that a driver is safe, suitable for a particular device,
compatible with the current Windows build, or correctly represented by a
catalogue file. Catalog-based package verification is a separate operation.
OPlague never installs, loads, extracts, repairs or deletes a driver as part
of this inspection.

The feature is Windows-only. Other platforms report that Authenticode
inspection is unavailable rather than substituting a guessed result.
