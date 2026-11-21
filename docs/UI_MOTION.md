# Desktop UI motion contract

The desktop UI follows the AETHER-ANAS white/blue/red motion contract, now extended by the shared Anatidae / Pond Motion profile. Motion is functional feedback, not ambient decoration. Decorative ducks, feathers and water layers are reserved for optional showcases; they never sit behind device tables, package evidence or report editors.

## Timing and curves

| Interaction | Budget |
| --- | ---: |
| Direct control acknowledgement | 0–40 ms |
| Hover, focus and state changes | 80–140 ms |
| Pane and graph reflow | 160–240 ms |
| Scene/preset transitions | 260–380 ms |
| Reduced-motion replacement | no more than 80 ms |

The default easing is `cubic-bezier(0.2, 0.8, 0.2, 1)`; click/transient feedback uses `cubic-bezier(0.05, 0.9, 0.2, 1)`. Linear motion is reserved for time/phase indicators. No large-area strobing, uncontrolled parallax or decorative rainbow cycling is permitted.

## Semantic colour

- Blue `#0039A6` / navy `#0B1F3A`: navigation, focus paths and calm state.
- Red `#D52B1E` / `#B51A10`: generation, mutation, clipping and safety events only.
- Signal animations must encode a measured value or state.

## Accessibility and performance

Preferences are persisted separately from theme settings:
- **Expressive Motion** applies a restrained paddle-style ease-out and extends eligible transitions by 1.35×, capped at 380 ms.
- **Reduce Motion** caps any retained transition at 80 ms and removes spatial/window movement; it overrides Expressive Motion.
- **Eco / Low-CPU Visuals** suppresses nonessential visual effects and secondary refresh work; it also overrides Expressive Motion.
- **Sync to Transport / BPM** is enabled only when a real project transport/tempo source exists. It must not pretend to sync when the host has no transport.

All animation work stays on the UI thread and must never block hardware inventory or archive/driver inspection. This application has no audio transport; BPM sync is intentionally unavailable in this UI.

## Anatidae / Pond Motion translation

The shared profile contributes a fast paddle response (`cubic-bezier(0.22, 1.18, 0.36, 1)`), a gentle water glide (`cubic-bezier(0.37, 0, 0.63, 1)`), restrained white/blue/red surfaces and an optional gold accent. OPlague implements the paddle response as a bounded native easing curve in its startup acknowledgement. Browser-only fixed parallax, blur, particles and animated backgrounds are intentionally not copied into the precision workbench. All animation stays on Tk's UI thread and never touches inventory, archive inspection or report work.
