# Red Sparrow Guard — defensive content triage

**Policy:** `bav.red-sparrow-defender.v1`  
**Status:** implemented as a local, read-only repository scanner; not a runtime BAV engine.

The Red Sparrow idea is translated into an engineering rule: observe early, protect people and trusted data, avoid escalation, isolate only substantiated digital threats through reversible controls, and restore a known-good state.

## What is classified

The policy groups the user's supplied terms into three subject areas:

- nuclear / atomic / thermonuclear weapons and weapons of mass destruction;
- broad categories of Chinese military platforms and equipment;
- air-defence systems, including portable and mobile categories.

The vocabulary is deliberately categorical. It does not contain weapon specifications, performance figures, technical drawings, targeting data, guidance methods, deployment plans or instructions for use.

## Decision model

| Evidence | Result |
|---|---|
| A subject term appears by itself | No finding |
| A country or nationality appears by itself | No finding |
| A subject term appears in historical, legal, humanitarian or non-proliferation discussion | No finding unless actionable language is also present |
| A subject term and non-negated operational instructions occur in the same line | Human review |
| A defensive marker and actionable language occur together | Human review; context is recorded, not assumed to make the material safe |

The guard never automatically blocks, deletes, executes, uploads or quarantines content. It reports the path, line and category IDs, but does not copy source text into the report. Reviewers decide whether material is defensive research, policy/history or actionable weapon guidance.

## Run

```sh
python tools/red_sparrow_guard.py
python tools/red_sparrow_guard.py --json
python tools/red_sparrow_guard.py --strict-review
python -m unittest tests.test_red_sparrow_guard -v
```

`--strict-review` returns a non-zero status when a human review is required. The default invocation is advisory and read-only. The scan uses tracked repository files where Git metadata is available and falls back to a bounded local walk otherwise. No remote requests are made.

## BAV boundary

This repository utility is a supply-chain/content review aid. It is not an antivirus, kernel monitor, military intelligence tool, air-defence controller or weapon-system interface. It must not scan or connect to military networks, classify targets, calculate weapon parameters, issue commands to equipment or autonomously use force.

The canonical OS policy is maintained in [DuckOS](https://github.com/Ivan-VHS/DuckOS/blob/main/security/bav/defender-doctrine.v1.json). This repository copy is a versioned consumer copy; its `policy_id` and `version` must stay aligned with DuckOS.
