# OPlague PE Workbench — integrated package audit

The PE Workbench is the read-only executable and driver-candidate analysis subsystem of OPlague. Its workflow is integrated end to end:

1. Enumerate PE candidates in a selected folder with deterministic ordering and a configurable file ceiling.
2. Validate DOS, PE, COFF and optional headers, then inspect section boundaries and bounded entropy samples.
3. Compute SHA-256 fingerprints, group duplicate files, and summarize architecture and candidate classifications.
4. Emit a versioned JSON audit, an operator table or a Markdown review artifact.

Examples:

    python tools/pe_driver_probe.py C:\DriverPackage
    python tools/pe_driver_probe.py C:\DriverPackage --format json --output reports/driver-audit.json
    python tools/pe_driver_probe.py driver.sys --format markdown
    python tools/pe_driver_probe.py C:\DriverPackage --max-files 12000 --strict

The report schema is oplague.pe-inventory.v1. The scanner is bounded to 512 MiB per file and 50,000 entries per scan by default policy. It skips symbolic-link files and directories. Section entropy is sampled up to 1 MiB per section; a high value is only a review hint, never a malware verdict.

The Authenticode certificate-table directory is located and range-checked, but the signature is not cryptographically verified. A .sys extension or native subsystem is only a driver-candidate hint. The tool never extracts archives, loads, installs, executes or modifies driver payloads. It does not infer publisher trust, OS support or device compatibility.

This is an original OPlague subsystem, not a clone of a driver product. No third-party source, product artwork, interface layouts or copied trademarks are included. Copyright (c) 2026 Ivan-VHS. The repository Apache-2.0 LICENSE remains authoritative.

Test:

    python -m unittest discover -s tests -p "test_pe_driver_probe.py" -v
