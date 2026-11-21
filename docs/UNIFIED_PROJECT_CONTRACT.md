# Unified project contract v1

| Contract | Rule |
|---|---|
| Capabilities | stable ID, implemented/partial status, source evidence |
| Interfaces | versioned format, direction, peer and opt-in |
| Validation | schema, bounds and repository-local evidence |
| Native ABI | caller-selected trusted path; never implicit load |
| Data | treat imported JSON as untrusted |
| Safety | preserve read-only/device and bounded-parser boundaries |

Run `python tools/validate_project_contract.py`. Manifest is an inventory, not a wishlist.
