---
name: attention-first-operator-ui
description: "Use when building or auditing an operator dashboard, run list, queue, monitoring surface, or analytical/intelligence console — especially when the first screen leads with a hero/marketing block, when urgent items are buried in a reverse-chronological table, when navigation mirrors internal architecture, when a KPI's time window makes it report a misleadingly reassuring number, when rows name a record but link nowhere ('I see the alerts but can't click through'), when errors render as raw stack traces or ungrouped red rows ('we need to be better at error handling and logging'), or when a surface presents derived scores without stating what it does not know."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ux, dashboards, operator-tools, information-architecture]
    related_skills: [empty-data-surface-diagnosis, dogfood, agentic-sdlc]
---

# Attention-first operator UI

## Purpose

Operator surfaces exist to answer one question on load: **what needs me right
now?** This skill encodes the recurring failures that bury that answer, and the
verification discipline that catches them.

Trigger: building/reviewing a dashboard, runs list, alert queue, or ops console;
or a user saying "I can't tell what needs attention", "why is this a landing
page", "I had to scroll to find the blocked one".

## The four recurring failures

### 1. The hero owns the fold

A gradient banner restating the product's tagline plus an architecture
explainer consumes the entire first screen. The operator already knows what the
product does — they opened it to find out what is wrong.

Fix: fold one is a ranked **"needs attention"** queue. Every row states the
consequence in plain language, carries a real timestamp, and has a working
action. Explainers move behind a link.

### 2. Urgency is invisible in reverse-chronological order

A flat newest-first table means the two runs blocked on a human sit at rows
14–15, under eleven failures. Sorting by time is not triage.

Fix: group into urgency bands (`Needs you` / `Failed` / `In flight` /
`Completed`), newest-first *within* each band, history collapsed by default.
Write a test that proves a blocked item surfaces first even when dozens of
failures dominate the set.

### 3. Navigation mirrors the architecture diagram

Grouping nav by internal planes/services/subsystems is the implementer's mental
model. Nobody thinks "I need the Ledger Plane."

Fix: group by operator **verbs** (Operate / Govern / Analyze / Configure). Four
sibling entries that are four *views of one dataset* collapse into tabs inside
that dataset's page. Keep the architectural color coding as a per-item accent —
it still says "which subsystem owns this" without dictating the menu.

### 4. A KPI's time window hides the headline

"Failed (24h): 0" while 24 runs sit failed is *technically true and materially
misleading* — every failure was 2 days old. The ~50% failure rate was the most
important fact on the page and the window erased it.

Fix: report the total plus a share ("24 · 48% of all runs"). Reserve narrow
windows for genuine alerting, and never let one render a reassuring zero over a
bad standing state.

### 5. Errors are rendered as raw exception strings

A failures panel showing twelve red rows, each reading
`Error: fetch https://example.com/inventory?model=Santa%20Fe -> 403`, is not
information. It is one unparsed log line per source, and it makes the reader do
the classification the surface should have done.

Worse, it *hides the shape of the problem*: those twelve rows were three
distinct causes repeated. The operator cannot see "eight sources block us, one
fix" because the surface never grouped them.

Fix — **classify, group, and prescribe.** See "Failure legibility" below.

## Design rules

- **Collapse duplicates into one counted row.** Six rows reading "A run is
  waiting at resolver" teach nothing; "13 runs are waiting at resolver ×13"
  does. Pluralize the title, report the **oldest** member's age (not the
  newest — the row must not look falsely fresh), and link to the filtered queue.
- **Every row is actionable.** Non-empty href + action label, asserted in tests.
- **Prove the link's target actually filters.** Adding `href={/items?id=${id}}`
  is half the work. If the destination never reads that param, the link silently
  lands on the *unfiltered* list — it looks like it works, and only a human
  clicking it finds out. Verified this session: alert rows deep-linked to
  `/listings?vin=…` while `queryListings` had no `vin` filter at all, so every
  link would have dropped the user on all 2,512 rows. **Grep the destination
  for the param name before shipping the link.**
- **Give a row more than one exit.** An operator looking at a flagged item
  wants the record, the upstream source, and the next action. Three small links
  (`Calculate` / `Dealer page ↗` / the row itself → filtered listing) beat one
  ambiguous click target, and each answers a different question.
- **Put the raw identifier on the row.** A VIN, run ID, or order number in
  small monospace is what the operator pastes into a phone call or a support
  ticket. It costs one line and removes a click.
- **Make KPIs navigation.** Each tile links to the filtered view it summarizes;
  a `?view=` param from a tile should override the stored view preference for
  that visit — the user asked for that slice by clicking it.
- **Rank explicitly, and test the ranking.** e.g. blocked > failed > flagged >
  stalled, newest-first within band.
- **Keep demo gates out of operational views.** A selected row, nonempty draft or placeholder is not a pending decision. Use the same exported classification as the owner queue and link there for real work. Verify inspector and detail sheet independently; update both baked and cached generated views so an older demo control cannot reappear during refresh failure.
- **Never fabricate a reason.** Derive failure text from the real event stream;
  if none exists, name the stage. Assert that no rendered string contains
  `undefined`.

## Failure legibility: classify, group, prescribe

When a surface reports failures from many sources, three transformations turn a
log dump into an operator tool. Do all three — each alone is insufficient.

**1. Classify into stable codes at read time.** Parse the stored message into a
closed set of causes, and keep the raw string machine-readable at write time so
the classifier has something to match:

| Code | Means | Retryable? |
|---|---|---|
| `blocked` | 403/429 — the source refused us | yes, later |
| `not_found` | 404 — *our* URL derivation is wrong | no, needs code |
| `server_error` | 5xx — their problem | yes |
| `timeout` | network/DNS | yes |
| `parse_failure` | fetched fine, extracted nothing | no, needs a parser |
| `unknown` | unclassified | investigate |

The retryable column is the operator's actual decision. `blocked` and
`not_found` look identical as red rows but have opposite responses: one waits,
one needs a developer.

**2. Group by cause, not by source.** Render one card per code listing the
affected sources, so the panel reads *"Blocked — 8 dealers — bot protection"*
instead of eight separate mysteries. The count per group is the priority signal.

**3. Carry a remedy string.** Every class states what a human should do:

```ts
{ code: "not_found",
  summary: "No inventory page at the address we tried on example.com.",
  remedy: "URL derivation is wrong for this platform. Identify the platform "
        + "and add its inventory path.",
  retryable: false }
```

### Rules for the rendered text

- **Never render a stack trace or a raw URL in a summary.** Extract the host
  (`new URL(u).host`) for identification; keep the full URL in a debug field.
  Worth an explicit test: assert no summary matches `/https?:\/\//` or
  `/Error:/`.
- **Strip the stack at write time, keep the shape.** Store
  `e.message.replace(/\s+/g," ").trim()`, not `String(e)`. The message retains
  the `-> 403` marker the classifier needs; the stack is noise in a status
  column.
- **A single failing member must not blank the whole surface.** A
  "suppress alerts when the sweep failed" rule that reads *the last job row*
  reads the last **source of a 40-source run** — so one blocked source at the
  end of the alphabet suppressed every alert on the page while 28 sources had
  succeeded. Judge health over the whole most-recent run, and when the run is
  partial say *"newest data is partial"* rather than hiding everything.
- **Coverage belongs at the top, as a bar.** `1,460 of 2,512 (58%) · 28 of 40
  sources reporting` is what makes "no results found" interpretable. Buried in
  a notice list it reads as one more warning; at the top it frames everything
  below it.



Put the ranking/grouping logic in a plain function taking `(records, { now,
limit })` and returning ranked items — no React, no hooks, no clock reads.

This buys real unit tests for the thing that actually matters, and it forces
`now` injection, which prevents wall-clock flakes.

Then mount it. **A tested projector is not done until it is rendered on the
route and fed by the real producer** — and not until you have *looked* at it.

## Explainability and onboarding are product requirements

For the user, a professional research/operator dashboard must teach the user how to interpret it, not merely look cleaner. Establish the primary user question and learning goals before changing the layout; organize measures by the decisions they support rather than repeating identical KPI cards.

1. Define a central glossary before adding help controls. For each non-obvious measure, explain what it counts, its denominator, what it does **not** establish, and the next useful action. Explain exact-set scoring explicitly: an extra irrelevant item can make the set incorrect even when the required information was retrieved.
2. Keep decisive labels and values visible without hover. Add reusable help that works by hover, keyboard focus and touch, with `aria-describedby`, Escape/outside dismissal and viewport-aware placement; native `title` alone is not the learning experience requested. Make opening idempotent across hover → focus → click: toggling in `onClick` can immediately close a panel that focus just opened. Test with a complete user-event click, not only an isolated click handler. Render outside clipping ancestors, clamp both axes, and recompute placement on resize/scroll.
3. Add a discoverable, replayable guided walkthrough across real routes when onboarding is requested. Each step must identify the task, actual control, expected observable change and interpretation. Provide step count, next/back/close and a bounded mobile-safe callout. If presented as modal, trap Tab within its controls and restore the initiating control's focus on close. Scroll to a target once after it mounts; subsequent scroll/resize handlers should only measure, because restarting smooth scrolling from the scroll callback creates feedback and jitter. Clear incompatible detail selections when navigating to an overview step. Tours may navigate and highlight, but must not silently approve, delete, teach or start paid work; test network writes across the entire tour, not just the displayed promise.
4. Keep the in-app tour, written hands-on guide and recorded walkthrough as distinct deliverables. Reuse the same vocabulary and one worked example across them; a guide link or storyboard does not substitute for the requested interaction or video.
5. Verify help on the actual metric and the tour on the actual empty/populated routes. Exercise focus, tap, Escape, back and completion; inspect tooltips near viewport edges so an explanation does not hide the control or outcome it explains.

## Narrow-screen comparison and metadata gates

1. Identify the measures that determine the decision before choosing the mobile layout. For the user's evaluation dashboards, show selection quality and final-answer quality together; an intermediate score must not be the only visible result.
2. At 320px and 390px, scroll to the actual comparison section, not merely the page header. If a table pushes a decisive measure offscreen, render per-model/per-mode cards from the same data. Put latency and raw usage behind expandable details. A page with no horizontal overflow can still hide its answer column inside a scroll container.
3. Assert that both decisive values are visible, then inspect a screenshot of that component. Do not diagnose the normal bottom edge of a viewport screenshot as page clipping; reproduce a component-boundary defect before changing layout.
4. Format timestamps for human scanning with `Intl.DateTimeFormat`, retaining exact values in `dateTime`/`title`. Collapse long fingerprints behind a disclosure. Preserve operational identifiers without forcing them to compete with outcomes.
5. Render permanent scope/namespace explanations neutrally, not as red errors. Give telemetry totals an explicit coverage denominator; technical caveats should explain the figures without visually impersonating a failure.

## Large account inventories: summary before names

Default large alignment/territory inventories to collapsed on Overview. Keep the exact coverage fraction, percentage and source availability visible; reveal complete names only on explicit expansion, with a bounded-height scroll area and name/identifier search. Do not render hundreds of account chips as the default first-screen content, hide unmatched records without counts, or equate alignment with actual engagement. Expansion/search must not change metric denominators or issue new CRM/model calls. Verify last-item search, collapse and reload on desktop/mobile.

## Optional AI summaries and background progress

1. Keep an AI brief optional. Put a compact priority summary in the existing Overview rather than adding another navigation tab; distinguish deterministic dashboard priorities from the generated narrative, which belongs behind an expansion control.
2. Define visibly different space budgets before implementing expanded, compact and hidden modes. For the user, compact means a slim, content-bearing ticker strip—not a tall header with its body removed. Hidden removes the card and leaves only a small restore icon. Preserve remembered choices and measure the rendered heights; different labels alone do not establish different modes. Keep display preference separate from generation consent: load, restore, expand and hide must never start paid inference.
3. Use icon-only controls for repeated brief actions: one state-dependent expand/compact toggle, hide, Generate/Refresh, and a small settings gear. Supply accessible names, bound tooltips, visible focus and usable touch targets; remove redundant simultaneous Expanded and Collapse buttons. Keep generation, narrative expansion and speech semantically distinct even when labels are visually hidden. Put secondary preferences in the gear popover, with Escape/outside dismissal and focus restoration.
4. Visualize actual background job stages with a compact stepper or animated active-stage indicator. Drive transitions from observed server state, not elapsed-time theater; do not invent internal thoughts or completion percentages. Show optional retrieval as skipped/unavailable when appropriate, stop animation on terminal states, and respect reduced-motion preferences.
5. Keep navigation usable during generation. Hiding the panel does not cancel the job; cancellation must be a separate supported action. Show a small ready/status affordance without reopening a hidden panel. State whether completion requires the app process to remain running and whether the saved result survives restart.
6. Keep ticker summaries calm: start with static source-labeled text and manual previous/next controls. Offer optional slow discrete rotation through a remembered toggle in the small settings gear; avoid continuous marquee motion, bouncing and repeated screen-reader announcements. Pause rotation during hover/focus, background-tab or offscreen states, and reduced-motion preference. Keep rotation separate from observed job progress and generation consent.
7. Test preference persistence, restore discoverability, motion stop/pause and zero generation requests on presentation/settings changes. Assert actual browser innerWidth before breakpoint checks, scroll to the changed component, and close unrelated assistant drawers. Measure compact and hidden footprints plus badge word wrapping—not just page overflow—then inspect screenshots; a KPI-only or overlay-covered capture cannot verify the brief.

## Brief integration verification

Prove actual framework lifecycle behavior, not only helpers: async data arrival, focus across the whole panel, reduced-motion changes in both directions, viewport visibility and component teardown. Measure the entire compact panel in every job state. Follow [brief workflow verification](references/brief-workflow-verification.md) for the ordered schema, timer, interaction and release-evidence checks.

## Customizable action briefs: workflow before prompt

For the user, a personal brief must prioritize existing work and review record hygiene, not merely summarize milestones. Specify separate customer-delivery, activity-follow-through, hygiene and membership queues with observed reasons and exact record links. Keep low-value cleanup behind customer urgency unless a cleanup-focused preset is explicitly selected. A prompt mentioning cleanup is not an implemented workflow.

Treat hygiene as review-only recommendations: overdue does not prove completion, similar titles do not prove duplicates, and missing metadata does not prove missing work. Rewriting, completion, deletion and team changes require their own approval flow.

Offer meaningful presets and bounded controls for priority count, horizon, sections, account subset, detail and optional context windows behind the small gear—not arbitrary scoring weights or editable system prompts. Settings must affect the entire path—preview, initial evidence, optional context queries, follow-up tools and final prompt—not merely the controls or local projector. Test a non-default selection end to end and ensure legacy default retrieval cannot silently re-enter. Keep every path within authority and never generate from settings edits. Pin settings to each job and show saved-answer settings separately from current edits.

Record the schema, ranking, safety boundaries and acceptance scenarios in OpenSpec before implementation. Use the [verification procedure](references/brief-workflow-verification.md) to test real preference effects and distinguish local implementation from publication.

## Live-run observation gates

1. Inspect every producer of running state. Poll while either a queued job OR a direct CLI-created run is pending; a run may exist without a job row.
2. Poll open run details as well as the list. Stop only at a verified terminal state or unmount; clear timers and reject stale responses when the run ID changes.
3. Keep the latest observed status in an effect-local mutable variable or ref. Do not read captured React state from a polling error handler; a callback created while `detail` was null can stop retrying after a later network blip.
4. Test `running → transient GET failure → completed` with fake timers, plus terminal-state no-poll and unmount behavior. Reproduce the sequence even if a reviewer declares the closure sound; a successful `running → completed` test does not cover recovery.
5. Distinguish planned work, saved responses and explicit `not_run` records in types and UI. Show run-level interruption/setup errors as well as per-trial failures; never imply that every missing result represents an executed request.

## Visual bar for the user's ops consoles

the user rejects functional-but-plain dashboards as amateur. For any monitoring/mission-control page, load `claude-design` first and design, don't just wire data:

1. Lift the product's own tokens (bg/surface/accent/mono font) from its CSS before writing styles.
2. Fold one = a one-sentence verdict ("Site is frozen — 1 blocker, 2 warnings") + blocker cards with impact and a `next →` action + 4 KPI cards that each carry a chart (sparkline or stacked proportion bar), not bare numbers.
3. Show the system as stage columns (inputs → triggers → execution → jobs → data → release) with clickable steps opening an evidence drawer; avoid free-form node-and-edge spaghetti.
4. Lead with an insight chart that answers the operator's real question — e.g. scheduled slots vs actual runs over 48h (ticks for slots, shapes by trigger, late lines, clustered ×N badges) — computed from expected-vs-actual matching, not raw run lists.
5. Hand-rolled SVG in separate `charts.js`/`app.js` files served by the service (no CDN), with a `?static=1` mode that skips SSE so headless screenshots finish.
6. Iterate screenshot → vision critique → fix for at least two rounds; preserve the rejected version (e.g. `/v1`).
7. Theme + controls: light/dark/auto via `[data-theme]` CSS tokens, and have SVG charts read colors from `getComputedStyle` (`pal()`) at render — SVG attributes cannot use `var()`, so hardcoded hex leaves dark-theme leftovers. Toolbar = range (24h/48h/7d), theme, density, live/pause, refresh-now (rate-limited POST that wakes the collector), lane filters; persist in localStorage; apply `?theme=&range=` overrides BEFORE initializing segmented controls or the selected state renders wrong. Fetch the longest offered range server-side and filter client-side.
8. Dense series (e.g. 15-min slots over 7 days): when spacing < ~14px, draw only the misses; full tick rows merge into a heavy block.
9. When asked how a monitor stays current, state the chain: collection interval + sources, push transport + reconnect, staleness self-check (`/healthz`), what is host-persistent (restart-policy container) vs session-bound (a background process dies with the session), and how code updates reach the host.
10. the user checks ops consoles from his phone first. Ship a phone layout in the same pass (compact toolbar, one-column pipeline, summary list above any wide chart, wide charts/tables in their own swipe scroller) and prove it at real 390px in both themes per `ui-visual-verification` → `references/phone-viewport-capture.md`. Status text must read as plain facts: no raw dicts, `?` placeholders or `$-1,930`; host-absent sources say "not on this host" as unknown, not warn.
11. For autonomous-SDLC / mission-control cockpits, split fold one's work deck into `Needs Your Decision` (inline option buttons showing `Option A — <concise effect>` + in-place approval composer preserved across SSE ticks) beside `Agent Decisions & Loop State` (coding, watcher auto-reruns, and merged fixes queued at live verify with a causal banner when a failing release stage blocks verification). Connect pipeline, memory, and SDLC tracks with explicit feedback bridge rails and a bounded hover/focus mental-model overlay anchored outside the hovered box that cross-highlights linked upstream/downstream elements (`[data-dream-linked]`). Full layout and parser/denominator rules: `operator-dashboard-legibility` → `references/system-mission-control-page.md`.

## Verification: screenshots catch what tests cannot

Passing tests and a clean type-check are necessary, not sufficient. In one
session, 175 green tests plus a clean production build still shipped:

- six identical repeated rows (unscannable)
- a KPI reporting `0` over a 48% failure rate
- a demo-mode badge contradicting the runtime env var

None were detectable from assertions; all three were obvious in one screenshot.

Loop: build → serve the production bundle against **real data** → headless
screenshot → view the image → fix → re-screenshot. Then repeat against the
deployed URL after release, because build-time inlined env vars can differ from
what you ran locally.

## Pitfalls

- **Build-time env inlining.** A `NEXT_PUBLIC_*`-style flag set at runtime does
  nothing if the Dockerfile's `ARG` default baked the opposite value into the
  bundle. Check the Dockerfile default, not just the container's env.
- **Deploy by digest.** Reusing a tag will not repull; resolve the digest and
  update with it, then confirm the new revision is sole-active at 100% traffic.
- **Converting a shared layout component to a client component** (adding
  `usePathname` etc.) touches every page that imports it. Re-run the full type
  check and test suite, and screenshot at least one page, before trusting it.
- **Report status in buckets** — verified live / verified locally / implemented
  but unproven / blocked. Never collapse them into "done".

## Derived surfaces: never render a metric you cannot ground

When a dashboard's numbers are *derived* from a system rather than entered by a
human, two extra rules apply.

**1. A field that exists but is always zero is not a metric — it is an absence.**
A session store exposed `actual_cost_usd` / `estimated_cost_usd` on every row,
and every row was `0` because subscription billing emits no per-call cost.
Rendering a "$0.00 spend" tile would have been a confident lie in the most
prominent position on the page. Correct handling: **omit the panel**, record
`cost_tracked: false` in the data, and leave one line of prose saying *why* it
is absent and what replaces it. Check whether a column is *populated* before
giving it a tile.

**2. Weak attribution must be labelled at the panel, not in a doc.** A "where
did the work happen" rollup that keys off each session's `cwd` silently
under-counts, because gateway- and cron-originated sessions carry no working
directory. One row reading `ai — 1` looks like a finding; it is a coverage
artifact. Put the caveat directly under the panel it qualifies.

Corollary for auditability: when a surface **filters** its input, show the
rejected count ("157 host/browser processes rejected") and state the rule. A
filter the operator cannot inspect is indistinguishable from a bug — and in this
case there *had* been one: a name-substring match that counted 138 browser
renderers as agents until it was anchored to the executable path.

Also distinguish **absent** from **zero** in row rendering: a repo with no
commits should show `–` and its own `empty` state pill, never `0d old`.

See `local-agent-telemetry-inventory` for the collector-side discipline.

## In-app assistant, version skew, and post-action deep links

- **Close the loop after a user action.** A success toast should deep-link to the view that explains the action's effect, using stable keys. The target pins the record past any render cap and handles write lag with explicit waiting and not-found states.
- **Assistant panels are docked, grounded, and transparent:** no blocking overlay, server-side retrieval scoped to the view, a sensitive-data guard that withholds on failure, and per-reply "What I looked at" with clickable citations. Fallback replies are labelled.
- **UI ahead of backend:** check the live API schema before debugging. On 404, rebuild from older endpoints with a label, and never show a missing section as empty-and-ok.
- **About/version:** low prominence, with the SHA baked in through a build arg because container contexts have no `.git`.

Recipes: `references/grounded-assistant-and-action-deep-links.md`.

For additive outcome telemetry, replay both the last legacy artifact and the producer’s exact versioned export through the consumer. Verify the cohort denominator comes from the producer rather than visible rows. Record which artifact actually reached production: a successful local replay is not a live-ingestion receipt.

## Analytical surfaces (the sibling case)

The rules above assume a **triage** surface: *what needs me now?* An
**analytical / intelligence** surface — a ranked book, risk register, or signal
console — answers *what is happening, and how much should I believe it?* The
attention-first rules still hold, but such a surface must additionally carry its
own epistemics: what it does not know, which measures are unimplemented, which
benign explanations remain unexcluded.

See `references/analytical-dashboard-authoring.md` for that case: zero-dependency
single-file HTML with hand-rolled SVG charts, the skeleton+patch authoring
pattern for large artifacts, dual-theme via tokens, showing a learned baseline
rather than just applying it, honest empty states, and the Method-tab discipline.
