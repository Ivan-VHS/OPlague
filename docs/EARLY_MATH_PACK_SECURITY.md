# Early-math activity-pack security contract

OPlague provides a read-only validator for the static activity-pack format used by DAK/Mora. The validator treats lesson text as untrusted content and checks a bounded data contract before another application chooses how to display it.

## Accepted content

A pack contains a version identifier, locale, broad age range, teaching principles, age stages, activities, materials, steps and an adult-facing prompt. Every object uses an explicit allowlist of fields. Duplicate JSON keys, non-finite numbers, oversized files, duplicate identifiers, unsupported concepts, out-of-range ages and excessive collections are rejected.

## Privacy and execution boundary

- No child names, identifiers, birth dates, contact information, location or learner history are accepted.
- No profiles, telemetry, analytics, scores, leaderboards or progress tracking are part of the format.
- Timers and network dependencies are forbidden; sessions are adult-guided and child-paced.
- External links, executable URL schemes and embedded executable markup are rejected.
- The validator parses bounded UTF-8 JSON only. It does not execute, render, download or install pack content.
- A successful validation is a structural and policy check, not a pedagogical endorsement or a guarantee of suitability for every child.

The format is data-only and local-first. A consuming application must still render all strings as text, supervise the activity and choose safe, age-appropriate physical materials.
