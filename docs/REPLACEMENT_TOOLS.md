# Original replacement tools

The new tools/pe_driver_probe.py utility is an independently written, read-only Portable Executable (PE) inspector for driver-package triage. It reads bounded PE headers and computes SHA-256 fingerprints for .sys, .dll and .exe files. It reports machine architecture, subsystem, optional-header format and a cautious driver-candidate hint.

Run:

    python tools/pe_driver_probe.py C:\DriverPackage --json

The scanner does not extract archives, load drivers, install devices, execute binaries or modify the inspected package. A .sys extension or native subsystem is only a candidate signal. Signature verification, publisher trust, OS compatibility and hardware compatibility are deliberately not inferred; use the existing OPlague evidence and Authenticode components for those separate checks.

This is not a clone of DriverStore Explorer, DriverView or another driver utility. It is an original PE-header reader and does not reuse third-party source code, product artwork, interface layouts or trademarks.

The new source and tests are original OPlague contributions, copyright (c) 2026 Ivan-VHS, under Apache License 2.0. The repository LICENSE remains authoritative.

Test:

    python -m unittest discover -s tests -p "test_pe_driver_probe.py" -v
