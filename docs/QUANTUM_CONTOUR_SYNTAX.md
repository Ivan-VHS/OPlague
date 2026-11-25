# QCS contour syntax

| Layer | Contract |
|---|---|
| Lexing | bounded UTF-8 tokens and source positions |
| Parsing | contour metadata and handoff markers |
| Validation | schema, domain and frame checks |
| Output | explicit diagnostics and JSON |
| Excluded | compiler, firmware or hardware control |

Run `python -m tools.qcs dialects` and `python -m tools.qcs validate file.qcs`. A passing syntax check does not validate a driver or device.
