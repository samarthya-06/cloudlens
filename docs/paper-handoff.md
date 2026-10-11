# CloudLens Paper handoff

Reviewed 11 October 2026 (Asia/Kolkata). This is a design handoff, not a working application. All incident content, filenames, counts and times are synthetic.

## Source and scope

- Product behaviour: root `AGENTS.md`, read before design work.
- Visual reference: root `design.md`, all 562 lines read; contents preserved.
- Editable target: [CloudLens — Mobbin UI](https://app.paper.design/file/01M4MW38GRY3Z78ZV60Y0HKE9P/p-1-0).
- File identifier: `01M4MW38GRY3Z78ZV60Y0HKE9P`; page `p-1-0` (Page 1).
- The owner switched Paper accounts after the first quota interruption. Continue in the linked copy, not the earlier file `01M4MVJ6RMDEDMM7PKVEKGZ4H4`.
- Latest owner instruction: **do not implement the mobile layouts when turning the design into code**. Desktop screens are the implementation target. The two existing mobile artboards are reference only.
- No application code, model calls or AWS provisioning were performed. Implementation still requires the owner's instruction to proceed.

## Screens and evidence

Heights are content-driven, not prescribed viewport heights. Dimensions below came from Paper metadata and the supplied 2x exports, not measurements inferred from screenshots.

| Artboard | Identifier | Logical size | Review evidence |
| --- | --- | --- | --- |
| 00 — Foundations & components | `1-0` | 1440 × 1157 | `evidence/design/00-foundations.png` |
| 01 — Demo access | `1E-0` | 1440 × 610 | `evidence/design/01-demo-access.png` |
| 02 — Investigate | `1V-0` | 1440 × 1288 | `evidence/design/02-investigate.png` |
| 03 — Investigation in progress | `3Q-0` | 1440 × 670 | `evidence/design/03-processing.png` |
| 04 — Incident report | `4L-0` | 1440 × 2545 | `evidence/design/04-incident-report.png` |
| 05 — History | `7M-0` | 1440 × 855 | `evidence/design/05-history.png` |
| 06 — Failure and uncertainty states | `7N-0` | 1440 × 1660 | `evidence/design/06-failure-states.png` |
| 07 — Mobile Investigate | `7O-0` | 390 × 1664 | Earlier plugin screenshot; reference only |
| 08 — Mobile Incident report | `7P-0` | 390 × 4436 | Earlier plugin screenshot; reference only |

The seven desktop PNGs were exported by the owner and copied unchanged from Downloads into `docs/evidence/design/`. They are all 2880px wide. Their review verifies rendered layouts, not backend behaviour or interaction functionality.

## Tokens and dimensions

Paper has 31 named tokens. Colour, radius and spacing roles map directly to future CSS variables. Font styling was applied directly to Text nodes after the copied file initially rendered system sans; Paper metadata subsequently reported Inter and System Monospace. A later foundations paragraph uses the system fallback and needs normalising when Paper edits are available.

| Token / role | Value |
| --- | --- |
| `--color-canvas` | `#ffffff` |
| `--color-ink` | `#141414` |
| `--color-ink-soft` | `#262626` |
| `--color-muted` | `#707070` |
| `--color-soft` | `#f3f3f3` |
| `--color-field` | `#f0f0f0` |
| `--color-hairline` | `#e0e0e0` |
| `--font-sans` | Inter variable |
| `--font-mono` | `ui-monospace, monospace` (Paper resolves System Monospace) |
| `--font-weight-heading` / body | 650 / 450; actions 600 |
| `--text-32` | Page title, 32px / 40px |
| `--text-24` | Section title, 24px / 32px |
| `--text-20` | Card title, 20px / 28px |
| `--text-16`, `--leading-body` | Body, 16px / 24px |
| `--text-14` | Supporting text, 14px / 20px; logs 14px / 22px |
| `--tracking-natural` | 0em |
| `--spacing-4/8/12/16/24/32/48` | Corresponding pixel values |
| `--radius-input` / card / pill | 16px / 24px / 9999px |
| `--container-content` | 1200px |
| `--breakpoint-stack` | 840px; retained reference token, mobile implementation excluded |
| `--opacity-full` | 1 |

Desktop: 120px side padding at 1440px, 32px top/bottom padding, 32px between main groups. Shell navigation is 1200 × 64px with 8px vertical / 16px horizontal padding. Buttons are 44px high with 20px horizontal padding; segmented track padding is 4px. Fields use 12–16px vertical and 16px horizontal padding. Cards normally use 24px padding and 16px internal gaps. The access card is 480px wide with 32px padding.

Report: left column 664px, right column 504px, gap 32px. Report sections have 32px gaps; evidence groups 24px gaps. Log rows reserve a 44px line-ID lane and 12px gap; timestamp text is part of the original log text. History reserves 160px for created time, 140px for status, 120px for the open action, and 24px gaps. Fact and timeline reference actions use fixed 160px lanes after the alignment correction.

## Shared patterns

These are editable Paper patterns and cloned nodes, not linked component instances with automatic propagation.

| Pattern | Location / identifier | Behaviour specification |
| --- | --- | --- |
| Desktop navigation | Investigate `1W-0` | Wordmark, Investigate, History, Session menu; active route in ink |
| Primary, outline and evidence pills | Foundations | 44px target; keyboard focus visible |
| Input and focus example | Foundations | Neutral field, 16px corners, 2px ink focus indication |
| Upload/Paste segments | Investigate `2C-0` | One selected panel at a time; semantic tabs in implementation |
| Selected file | Investigate `2N-0` | Name, size, synthetic label when applicable, Remove action |
| Sample cards | Investigate `30-0`, `37-0`, `3E-0` | Load input only; Analyse explicitly starts investigation |
| Status badge | Foundations, report, history | Explicit label; incident marker is textual `!`, no reliance on colour |
| History row | History; cloned into Foundations | Fixed metadata/action lanes; Open current state/report |
| Numbered log line | Report `7A-0` is selected L004 | Original stable line ID; neutral highlight plus 2px ink rule |
| Retrieved guidance | Report `83-0` | Runbook ID, section, excerpt and source label |

The standalone log-line clone and flow annotation could not be added to Foundations before the second MCP quota limit. Their source pattern exists in the report, and the complete flow is specified below.

## Interaction specification

Paper tools in this session exposed node editing, screenshots and export, but no prototype-link API. No actual navigation links, scrolling prototype, downloads, password validation or polling were built. Reference pills and highlight are static design examples.

Flow: **enter demo → load sample or submit logs → queued/processing → report → evidence selection → download → history → reopen**.

1. Demo access: default state has no error text. Failed submission shows the inline password error without losing the entered value. Successful submission opens Investigate. Session menu offers logout. No registration or third-party sign-in.
2. Investigate: Upload and Paste are mutually exclusive. The artboard deliberately shows multiple variants for review; the product must not display all of them simultaneously. The dropzone has a Browse alternative. Only UTF-8 `.txt/.log`, maximum 256 KiB. Invalid or oversized input is rejected without silently truncating it. Selected filename and Remove appear after valid selection. Empty input disables Analyse with a visible reason. Sample loading does not spend an inference call.
3. Paste: use a labelled multiline textarea. Correct the illustrative trace to `psycopg.OperationalError: authentication failed` to match the report fixture; the current paste variant says `connection refused by server`, which mixes a different failure category into this example.
4. Progress: display only actual job states, queued → processing → completed/failed. The sentence explaining retrieval is a process description, not a fabricated live sub-stage. No timer or percentage. Polling and reduced-motion behaviour are implementation requirements, not verified behaviour.
5. Evidence: L001 targets deployment, L004 first failure, L007 repeated failure, L008 health-check 503. A reference reveals and highlights the existing source line; a multi-reference chip should reveal a list of its targets rather than make only one reachable. Target IDs must match actual persisted evidence, not positional indices in a filtered list.
6. Runbook references: `DB-AUTH §checks` and `DB-AUTH §recovery` are design aliases for stable authored chunk IDs to be chosen during ingestion. Reveal the matching retrieved excerpt and its source metadata. Excerpts are project-authored, not official diagnoses. The source label must become a real primary-documentation link when runbooks are authored.
7. Log pane: independently scroll a bounded area in the desktop product; keep the line-ID lane visible and long lines inside the pane. Default wrapped lines are acceptable. If a no-wrap option is added, horizontal scrolling must be confined to the pane. Paper currently expands the log card to show all nine example lines; scroll functionality was not verified.
8. Download: the report action opens a small menu offering Markdown and JSON. No PDF option. The menu is specified here; its expanded canvas variant was blocked by quota.
9. History: scope to the current demo session; labels are job status, distinct from analysis status. Failed rows open retained evidence/error. Empty-history panel replaces the populated list. The mock entries must not be seeded as if real analyses had occurred.
10. Failure variants: invalid file → choose another; oversized → smaller excerpt; timeout → explicit user retry creating a new investigation; healthy excerpt → inspect evidence, without proving global health; ambiguous → add context; unknown/missing citation → withhold report and preserve deterministic evidence.

## Accessibility and responsive rules

Future implementation is desktop-focused per the owner's latest instruction. Validate desktop layouts at 1440px and an ordinary narrower desktop width such as 1280px. Use a fluid centred max-width container; reduce outer gutters before compromising readable text or evidence lanes. Do not implement the 390px mobile screens or a mobile navigation workflow.

Existing mobile reference rules, recorded only to explain those artboards: 390px canvas, 20px gutters, 350px content, condensed wordmark/Menu shell, cards stacked, report before evidence, persistent access to an evidence-jump action, reference pills wrap. A chip row that overflowed was changed to wrap. No final mobile PNG was supplied after that correction.

Use native buttons/links/inputs with meaningful labels, visible 2px ink focus ring plus 2px offset, ≥44px interactive targets, logical tab order and semantic headings. Focus must move to the revealed evidence target and remain visibly marked. Announce processing/terminal state changes politely; errors use associated field messages. Static PNG review cannot verify keyboard operation or screen-reader behaviour. Do not communicate severity only through colour. Render logs as text; never execute generated HTML or commands.

## Visual review and remaining limitations

Reviewed earlier plugin screenshots for foundations, access, investigate, progress, report, history, states and both mobile references. Reviewed all seven owner-supplied desktop exports after Inter and lane corrections. The exported desktop views show no clipped text, overlapping controls or artboard-edge overflow. History columns align; the report's log highlight is visible; hierarchy and neutral geometry are consistent.

Corrections already applied: missing-evidence block now renders; missing L008–L009 added; explicit Inter applied to text nodes; fixed reference lanes; history headings split into matching lanes; mobile reference row changed to wrap. The supplied report export confirms the limitations footer is present and the supplied state export confirms the final action is present.

Required handoff cleanup: remove authoring notes from the actual product, including `Variant`, `Design preview`, `Selection preview` and the technical support note below progress. Preserve meaningful synthetic labels on samples/demo fixtures and the AI-assisted limitation. Present default access without the error; show error only after failure. Do not show empty upload, selected upload and paste panels at once.

Paper MCP hit its weekly limit in both accounts. The second limit blocked final canvas annotations, standalone log pattern, download-menu variant and further plugin exports. Native Paper screenshot capture also returned unavailable. The owner-supplied PNGs provided final desktop visual evidence. All working indicators were released successfully with `finish_working_on_nodes`.

Design screens exist and desktop visual review is complete. The strict Phase D checklist still has the noted canvas annotation/component gaps; interactive behaviour remains a specification. Owner review is pending. No working backend, inference, retrieval, persistence or deployment is implied.


## Implementation inspection — 11 October 2026

Owner authorized development and excluded mobile code. Desktop implementation uses Inter, the recorded monochrome tokens, 1200px centered content at 1440px, 24px cards, 16px fields and pill controls. Fixed desktop minimum width is 1100px; smaller/mobile screens are outside this implementation scope. The report uses two columns and an independently scrollable log pane. Timeline values preserve source offsets or label unknown zones.

Inspected rendered pages at 1440×1000; keyboard/input layout checked at 1280×900. Three browser checks passed. Screenshots in docs/evidence/runtime cover actual local access, investigate, history and missing-index failure, plus a explicitly labelled report rendering fixture. The report fixture is not live inference. Timeline references were moved to the third column after inspection. No full-page horizontal overflow was found at inspected desktop widths. Long log lines scroll inside the pane.

Working interactions: source chips focus/highlight matching line/chunk, Upload/Paste tabs support arrow keys, upload errors preserve prior input, samples load without starting analysis, job polls stop at terminal states, session history reopens investigations, failed retries create a new job from retained redacted lines with newly assigned IDs, downloads have separate Markdown/JSON targets. Model/backend/S3 live flow remains pending AWS role setup and real ingestion. Native details menus and visible focus rings are implementation adaptations.

Live Gemini report inspected at 1440px: all five full retrieved runbooks made the page unnecessarily tall (6475px). Adaptation: show a short diagnostic excerpt and native Read retrieved section disclosure; clicking a runbook reference automatically expands and highlights its exact source. Full context and official source links remain available. Owner desktop-only scope retained.
