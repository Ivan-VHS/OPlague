# CLife Evidence Pod — OPlague adapter

CLife is adapted to OPlague's read-only driver workbench as evidence preservation.
It accepts only inventory_report, package_manifest, metric_report and inspection_notes.
Driver binaries, device state, registry state and executable payloads are outside the contract.

Implemented: versioned SHA-256 snapshots with project and artifact-kind binding; atomic local
checkpoint writes; strict schema, size and checksum validation; recovery branches for safe
read-only resume, verified evidence export, hold-for-review and safe stop.

Commands:
python -m oplague clife capture report.json .clife/report.json --project-id oplague-local --artifact-kind inventory_report --generation 1
python -m oplague clife verify .clife/report.json
python -m oplague clife export .clife/report.json recovered/report.json --project-id oplague-local --artifact-kind inventory_report
python -m unittest tests.test_clife -v

No command installs, loads, modifies or rolls back a driver or device. Export writes only the
explicit output file. Keep credentials and unnecessary personal data out of evidence payloads.
SHA-256 is an integrity checksum, not a digital signature.
