# CloudLens design decisions

11 October 2026. Base reference: unchanged root `design.md`. Product requirements: root `AGENTS.md`. Editable target: [CloudLens — Mobbin UI](https://app.paper.design/file/01M4MW38GRY3Z78ZV60Y0HKE9P/p-1-0).

## Visual adaptations

1. Preserve gallery-white canvas, near-black ink and primary pills, neutral tint hierarchy, hairlines, 16px fields, 24px cards and stadium controls. No gradients, decorative shadows, glass or coloured dashboard tiles.
2. Omit commercial blue because the application has no commercial emphasis. Communicate incident/status distinctions with words and markers, not invented red/green semantics or numerical confidence.
3. No licensed Saans asset was supplied. Paper confirmed Inter variable availability (weight axis 100–900). Map 652 → 650 and 456 → 450. Use 600 for actions. Apply Inter directly to Paper Text nodes because the initial imported typography used a system fallback despite the font token.
4. Replace the marketing 56–80px hierarchy with page 32/40, section 24/32, card 20/28, body 16/24, supporting 14/20. Use 14/22 system monospace for log evidence. Natural tracking and sentence case remain.
5. Use 4/8/12/16/24/32/48px spacing. Replace large marketing gaps with compact product grouping; outer group gaps are 32px. Maintain 44px interactive targets.
6. Use #707070 for essential supporting text and placeholders; omit #adadad from essential small text. Use the supplied tint ladder and hairline geometry. Do not make a numerical accessibility-conformance claim from PNG inspection alone.
7. Adapt the detached neutral navigation pill to CloudLens wordmark, Investigate, History and Session. Do not copy Mobbin branding, commercial pages, social sign-in, marquees, testimonials or an inverse marketing footer.
8. Prioritise the reference's no-shadow rule over its inconsistent illustrative modal/toast exceptions. Selected tab is white on neutral track without decorative elevation.
9. Report information is primarily open typography with selected structured cards, not a grid of coloured metrics. The left column explains the incident; the right provides numbered logs and retrieved guidance. Log highlight uses neutral fill plus an ink rule.
10. Keep analysis status separate from job status. A completed investigation can report insufficient evidence or no supported incident. A failed model call preserves deterministic evidence and withholds an invalid generated report.
11. Synthetic facts establish sequence and symptoms only. Credential mismatch is a leading hypothesis; policy and configuration evidence are missing. S3 denial can have several policy causes. Upstream timeouts do not establish CPU overload. No invented confidence, traffic, impact or model metrics.
12. Progress shows only the specified job states. No fabricated stage telemetry, percentage or elapsed time. Product copy should explain the process; authoring notes belong in documentation.

## Scope change

The owner later explicitly excluded mobile implementation. Two mobile design references already exist, but the future application should implement the desktop target only. The initial mobile breakpoint token remains in Paper for reference; it does not mandate mobile code. Record desktop verification separately from unimplemented mobile references.

## Review outcome

The owner supplied seven 2x PNG exports, now saved in `docs/evidence/design/`. They confirm the desktop visual system and the corrected report/history layouts without text clipping or overlap. Paper's weekly MCP quota prevented final canvas annotations and small component/menu additions. Their behaviour is documented in `paper-handoff.md`; do not claim a functioning prototype or a fully passed Phase D checklist.

Before product implementation, treat the presented variants as alternate states, remove authoring labels, correct the paste trace wording, use real source/chunk metadata, and implement evidence selection, download menu, keyboard focus and bounded log scrolling. These are concrete handoff requirements, not authorization to start coding in this design-only task.


## Desktop implementation scope and native controls

The owner explicitly excludes mobile implementation. Desktop code keeps a 1100px minimum width and the two-column incident report; the mobile Paper references remain design evidence only. At 1440px the content width is 1200px. Inspected 1280px and 1440px layouts do not overflow the page; logs can scroll horizontally inside their pane.

Use native input/password/file controls, textarea and details menus with explicit labels and visible ink focus rings. Remove canvas-only variant labels, unused example panels and backend-implementation commentary from the product. Empty history and access errors are conditional states. Display actual upload bytes, selected evidence counts and server states rather than design-example values. Report fixture screenshots are explicitly labelled in verification evidence. Preserve timestamp timezone text from supplied logs instead of inventing UTC.

Retrieved guidance displays a short diagnostic excerpt with a keyboard-accessible native disclosure for the complete retrieved chunk. Evidence jumps expand the target. This keeps the live report close to the reviewed two-column Paper composition while preserving all source text.
