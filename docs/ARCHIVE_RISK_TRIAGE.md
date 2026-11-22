# Archive risk triage

ZIP package inspection now emits an additional `archive_security` block using only central-directory metadata already read by OPlague.

It reports case-insensitive duplicate paths, ZIP symbolic-link entries, encrypted entries, loadable-binary candidates, script-like files and nested archive/package candidates. A bounded sample of findings is included for the report. Existing hard limits still reject path traversal, excessive entry counts, excessive expanded size, oversized INF files and suspicious compression ratios.

The result is a manual-review aid, not malware detection, publisher verification, a compatibility verdict or a driver-installation recommendation. OPlague does not extract, execute, load or install package contents as part of this analysis.

## Catalog links

This adopts safe metadata-inspection ideas from 7-Zip/zipinfo, libarchive, Binwalk, PE viewers and supply-chain inventory tools (catalog items 601–650 and 651–700). It does not embed their code or automatically query remote reputation services.
