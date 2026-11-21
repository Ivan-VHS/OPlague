# Disney Motion System — OPlague

OPlague adopts a restrained, product-focused interpretation of the twelve animation principles. Motion communicates state and spatial continuity; it is never decoration that delays device inventory, package inspection, signature evidence review, or report generation.

## Product contract

- Preserve the current Anatidae white-blue-red identity, Tk desktop architecture, typography and information hierarchy.
- Motion is feedback, never a prerequisite for understanding or operating the application.
- Prefer short, deterministic, interruptible transitions; cancel or replace obsolete motion when newer actions supersede it.
- Respect operating-system reduced-motion preferences and the `UI_REDUCED_MOTION=1` override.
- Never imply that a driver operation, scan, verification, or package inspection completed before its actual result exists.
- Do not introduce a browser runtime or replace the native desktop shell.

## Shared timing tokens

| Token | Duration | Use |
|---|---:|---|
| instant | 0 ms | Reduced motion / immediate state |
| micro | 100 ms | Press and focus feedback |
| fast | 140 ms | Small transition |
| standard | 180 ms | Menu or disclosure |
| spatial | 240 ms | Window or workspace |
| emphasis | 280 ms | Confirmed validation feedback |

## Twelve principles translated to UI

1. Squash and stretch: restrained pressed-state feedback; never distort labels or evidence.
2. Anticipation: focus and hover clarify available actions without delaying activation.
3. Staging: keep a clear focus while preserving inventory and package context.
4. Straight-ahead / pose-to-pose: use explicit state changes; reserve continuous animation for continuous interactions.
5. Follow-through and overlap: bounded sequencing for related surfaces.
6. Slow in / slow out: consistent easing for entry, exit, and repositioning.
7. Arcs: optional for navigation only; dense data tools remain direct.
8. Secondary action: supporting status feedback reinforces the real result.
9. Timing: use shared tokens and never block the Tk event loop.
10. Exaggeration: reserve emphasis for confirmed results and validation failures.
11. Solid drawing: preserve geometry, clipping, focus, and contrast.
12. Appeal: motion remains precise, restrained, and aligned with the product identity.

## Accessibility and performance

Reduced motion removes nonessential transitions without hiding information or changing outcomes. Avoid flashing, decorative loops, parallax, long stagger sequences, and per-row animation in large tables. Skip intermediate frames under load and render the latest state. Keep device inspection and security-related status driven by actual operation results, never animation timers.
