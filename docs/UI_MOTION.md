# OPlague desktop UI motion contract

OPlague follows the AETHER-ANAS white/blue/red contract. Motion is functional feedback, not ambient decoration. The 2026 Motion Lab concepts are implemented as native Tk transitions and are constrained by the application's read-only hardware and package-inspection role.

## Timing and curves

| Interaction | Budget |
| --- | ---: |
| Direct control acknowledgement | 0–40 ms |
| Hover, focus and state changes | 80–140 ms |
| Pane and report changes | 160–240 ms |
| Scene/preset transitions | 260–380 ms |
| Reduced-motion replacement | no more than 80 ms |

The default easing is `cubic-bezier(0.2, 0.8, 0.2, 1)`. Native top-level presentation uses a bounded mass-spring-damper solver (semi-implicit Euler, capped 32 ms delta, two substeps). Expressive Motion increases spring response and duration by 1.35x, capped at 380 ms.

## Modes and visual language

- **Normal** uses restrained spring feedback and default durations.
- **Expressive Motion** uses a stronger spring response for window presentation.
- **Reduce Motion** removes spatial movement and caps retained transitions at 80 ms.
- **Eco / Low-CPU Visuals** suppresses nonessential effects and applies the same 80 ms ceiling.
- Reduce Motion and Eco always override Expressive Motion.

The blue/white/red theme remains semantic: blue for navigation and calm state, red for critical or destructive-looking status only. Liquid Glass, portal glow and mesh references are translated into opaque readable data surfaces, subtle border emphasis and clear focus feedback. Pointer-following magnets, parallax, large-area blur and decorative background motion are not applied to inventory tables, hashes, INF data or compatibility reports.

## Accessibility and safety

Preferences are stored independently of theme settings. The previous preference format remains readable; Expressive Motion defaults to off. Native OS reduced-motion preference and `UI_REDUCED_MOTION` are respected.

This application has no audio transport, so BPM sync remains unavailable. Animation runs only on the UI thread. It must never delay hardware inventory, package hashing, archive-bound checks, report composition or driver inspection. Animation never installs, enables, disables or modifies drivers; all existing read-only and dry-run boundaries remain unchanged.
