# OPlague multi-syntax source audit

**Project author/developer:** Ivan-VHS

OPlague can consume a Reaper syntax-only validation report and verify that it belongs to the exact source bytes being reviewed. The audit checks the report schema, syntax identifiers, non-executing validation marker and SHA-256 digest.

It also compares declared capability requirements with the shared frontend policy. For example, the safe Python subset does not provide filesystem access, network access, subprocess execution or native FFI. A source package that declares those requirements is marked blocked instead of being treated as safe merely because it parses.

Example workflow:

```sh
python -m reaper syntax --check --syntax python ./mod-script.py --json > syntax-report.json
python tools/multisyntax_source_audit.py ./mod-script.py syntax-report.json --require-capability pure
```

The audit is read-only. It never executes the source, changes host settings, installs runtimes or grants capabilities. A "reviewed" result means the supplied syntax evidence and declared capabilities match this policy; it is not a full sandbox or proof that arbitrary runtime behavior is safe.
