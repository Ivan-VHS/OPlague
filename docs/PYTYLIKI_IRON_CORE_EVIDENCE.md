# Pytyliki Iron Core evidence intake

**Status:** read-only AST envelope validator  
**Upstream:** Ivan-VHS/Pytyliki, Iron Core AST v1  
**OPlague role:** validate and attach source-structure evidence to local inspection workflows

## Data flow

The Pytyliki CLI may emit a JSON AST via pytyliki-iron --ast-json. OPlague accepts that JSON only as caller-supplied, untrusted evidence. The validator checks the v1 envelope, bounded source size, exact marker catalogue, semantic IDs, closed blocks, byte ranges, version/policy counts and marker-count consistency.

The fixture in examples/iron_core/inspection.ast.json is a small contract example. It is not evidence from a physical processor, verified source checkout or CI run.

## Trust boundary

- verificated is a source-authored claim and is never promoted to a GitHub check, signature, human approval or trusted provenance.
- The AST explicitly states that semantic validation, execution and hardware access were not performed.
- The validator rejects those fields if they claim otherwise.
- The JSON does not contain a source digest or an authenticated producer signature. Provenance remains caller-supplied and untrusted.
- OPlague does not execute Pytyliki code, load a native module, contact the device, install drivers, write firmware or change kernel state.

## API

Import validate_iron_core_ast from tools.iron_core_evidence. It returns an immutable evidence summary or raises IronCoreEvidenceError. The complete mirrored JSON Schema lives at schemas/pytyliki.iron-core-ast.v1.schema.json.

## Validation

Run python -m unittest tests.test_iron_core_evidence or python -m unittest discover -s tests -p test_iron_core_evidence.py. The dedicated CI workflow runs this suite when the integration files change.
