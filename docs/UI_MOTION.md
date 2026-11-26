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
- The persisted motion model contains only three preferences: Reduce Motion, Eco Visuals and Expressive Motion.

The blue/white/red theme remains semantic: blue for navigation and calm state, red for critical or destructive-looking status only. Liquid Glass, portal glow and mesh references are translated into opaque readable data surfaces, subtle border emphasis and clear focus feedback. Pointer-following magnets, parallax, large-area blur and decorative background motion are not applied to inventory tables, hashes, INF data or compatibility reports.

## Accessibility and safety

Preferences are stored independently of theme settings. The previous preference format remains readable; Expressive Motion defaults to off. Native OS reduced-motion preference and `UI_REDUCED_MOTION` are respected.

Animation runs only on the UI thread. It must never delay hardware inventory, package hashing, archive-bound checks, report composition or driver inspection. Animation never installs, enables, disables or modifies drivers; all existing read-only and dry-run boundaries remain unchanged.

## Motion implementation profile

The shared duration tokens are `instant=0`, `micro=100`, `fast=140`, `standard=180`, `spatial=220` and `emphasis=320` milliseconds. Expressive Motion scales the selected token by 1.35, with a hard ceiling of 380 ms. Reduce Motion or Eco caps any retained transition at 80 ms and takes precedence over Expressive.

The Tk spring solver uses semi-implicit Euler integration, two substeps and a maximum 32 ms frame delta. It is presentation-only and snaps to its destination when settled or when its bounded duration is reached. Preferences live in `ui-motion.json` under the user's application configuration directory; old settings load with Expressive disabled by default.


## Anatidae / Pond Motion integration

OPlague reuses the existing bounded Tk spring controller for the duck-inspired paddle response. The shared tokens are `PADDLE_EASING = cubic-bezier(0.22, 1.18, 0.36, 1)` and `WATER_EASING = cubic-bezier(0.37, 0, 0.63, 1)`; the second is reserved for optional showcase artwork. Expressive Motion remains a stronger spring preset with a duration multiplier capped at 380 ms. Reduce Motion and Eco take precedence and cap retained motion at 80 ms.

Duck, feather, ripple and parallax effects are optional landing/showcase motifs only. They do not appear behind the inventory, hash, INF, archive, device graph or compatibility evidence surfaces. Animation is presentation-only on the Tk UI thread; it never delays package inspection or changes driver state.

See the [shared Anatidae motion constitution](ANATIDAE_MOTION_CONSTITUTION.md).


## Motion Constitution v2026 mapping

The shared token, accessibility and documentation source is [Motion Constitution v2026](MOTION_CONSTITUTION_V2026.md). This native contract remains the authority for what this application actually ships.

- Canonical easing names: `--ease-spring` (bounded paddle response) and `--ease-snappy` (predictable state transitions); native curves are mapped in this document.
- Canonical scale envelope: `--motion-scale` = 0.4×–2.2× and spring stiffness multiplier 0.7–1.4. These are shared design tokens; they are not exposed as user controls unless the application UI and runtime explicitly implement them.
- Reduced Motion: OS preference and `UI_REDUCED_MOTION` take precedence; spatial/ambient motion is removed, state changes remain immediate, and only essential feedback may retain a fade of up to 80 ms.
- Theme/layout parity: light/dark themes, keyboard focus and high-DPI layouts remain required. 2×2 overview and focus-scene are showcase layout targets, not a claim that this native product already provides those views.
- Telemetry graphics: SVG/Canvas/native-paint charts must bind to sourced model values, show units and an accessible textual equivalent, and expose stale/error/unknown states. Demo data must be labelled.

### Product-specific maturity

OPlague has a native Tk spring controller and persisted Reduce Motion/Eco/Expressive preferences. Its device inventory, INF/ZIP inspection, SHA-256 and compatibility relationships are read-only. USB ripple, firmware OTA rings, device DPI/Hz controls and driver installation/update flows are unavailable and must not be presented as live controls or telemetry.
