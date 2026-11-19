---
name: operator-dashboard-information-hierarchy
description: "Use when auditing or redesigning an internal operator/admin/observability dashboard — when a user says the UI is confusing, asks to 'fix the UI' or 'improve the UX flow', or when a surface shows passive metrics but never answers 'what needs me right now'. Covers screenshot-first auditing of the deployed UI, the attention-queue pattern for fold one, making KPIs navigational, and testing the projection before wiring components."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ux, dashboard, operator-ui, information-hierarchy, design-audit, react, nextjs]
    related_skills: [ui-vision-qa-loop, google-stitch, design-md, dashboard-ux-table-not-cards, sketch]
---

# Operator dashboard information hierarchy

For internal dashboards whose readers are operators, tech leads, and compliance
owners — not prospects. The recurring failure is a surface that is technically
correct, visually fine, and answers no question the reader actually has.

## Trigger

"Fix the UI a bit", "think about how the UX flow can be better", "I don't get
what I'm looking at", "who did what?", "I can't click anything", or any
dashboard where the reader must decode internal state to find their next action.

## Rule 0 — Audit the DEPLOYED surface before reading code

Reasoning from source is the wrong first move. The gap between what the code
says and what an operator *sees* is the entire finding. Screenshot first.

```bash
H="https://<deployed-host>"
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$C" --headless --disable-gpu --no-sandbox --window-size=1600,1100 \
  --virtual-time-budget=15000 --screenshot=/tmp/ui-home.png "$H/" 2>/dev/null
```

Use an available browser/CDP session or headless Chrome to capture the actual
surface. Treat PNG byte size only as a diagnostic hint, never proof of a valid
render: a giant debug dump or malformed fixture banner can produce a large image
while obscuring the entire dashboard. Inspect the screenshot and rendered DOM.

Then `vision_analyze` each shot asking about **information hierarchy**, not
aesthetics: *"What is at the top? Does the main area show a clear 'what needs my
attention' element, or only passive metrics? How many panels compete? Does
anything look prototype-grade?"*

Shoot the top three surfaces (home, the list page, the detail page). A problem
that repeats across all three is a product problem; one that appears on one page
is a page bug. That distinction sets the size of the fix.

## Rule 1 — Fold one answers "what needs me right now?"

Everything else is context for it. Marketing copy, hero sections, architecture
explainers, and "here's our vision" content belong below the fold or behind a
link — the operator already bought the product; they are here to work.

If the dashboard has a DESIGN.md or style guide, **read its "Do's and Don'ts"
as a test suite against the screenshot**. Specs are frequently right while the
product drifted. A real instance: the spec said *"❌ Don't add a hero section,
marketing copy, gradient backgrounds — this is an operator dashboard, not a
landing page"* while the shipped dashboard opened with exactly that, consuming
the whole first fold.

## Rule 2 — The attention queue is a PURE projection

Build it as a standalone module (no React, no fetching, no side effects) so the
ranking is unit-testable without a DOM.

Shape that works:

```ts
export type AttentionKind = "blocked" | "failed" | "flagged" | "stalled";
export interface AttentionItem {
  id: string;      // stable key + deep-link anchor
  kind: AttentionKind;
  title: string;   // plain-language outcome, never a state name
  detail: string;  // derived evidence, never invented
  href: string;    // every row MUST be actionable
  action: string;  // "Open gate" / "Triage" / "Review" — an action, not a mechanism
  at: string;      // ISO, for within-bucket recency
}
```

Ranking rationale, highest first:

1. **blocked** — stopped waiting on a human; nothing proceeds
2. **failed** — work was lost; needs triage
3. **flagged** — a human marked something wrong; must not propagate
4. **stalled** — running far past expectation; probably wedged

Newest-first within a bucket. Time-box aggressively: failures older than ~24h
are history, not alerts; "running" past ~30min with no update is `stalled`.

**Never invent supporting detail.** Walk the record backwards for a real failure
message; if there is none, name the stage instead of writing prose. An empty
state must say "nothing is waiting on you", never show fabricated rows.

Export a separate `attentionCounts()` so summary chips count the **full** queue
while the fold renders a capped slice (~6). Show "N more need attention" as a
link rather than growing the list.

### Collapse identical rows — repetition destroys scannability

The first screenshot *after* a correct redesign will often show six rows of the
same sentence ("A run is waiting on your decision at resolver" ×6). Technically
correct, operationally useless: a wall of identical sentences teaches nothing
and the reader stops at row two.

Group on the rendered `kind::title` (which already encodes the distinguishing
stage/class) and emit one row carrying a `count`:

- pluralize the copy — "13 runs are waiting on your decision at resolver"
- render a `×13` badge, change the action to a plural verb ("Open queue")
- repoint `href` at the **filtered list**, not one arbitrary member
- **report the OLDEST member's age** ("13 runs, oldest 4d ago") — using the
  newest makes a stale backlog read as fresh

Items that genuinely differ must NOT collapse: three stalled runs at 16d/19d/22d
on different stages are three facts, and titling by stage keeps them separate.

When the fold shows collapsed rows, the "N more" link must subtract
`sum(count)`, not `items.length`, or the arithmetic lies.

### Two follow-on hazards the collapse feature introduces

1. **Pure helpers that call `Date.now()` internally become untestable.** The
   collapse function renders relative time ("oldest 4d ago"); if it calls the
   time helper without the injected `now`, its copy is clock-dependent and
   assertions fail by one day on any skewed machine. Thread `now` through
   *every* pure helper that renders time, not just the top-level entry point.
2. **Existing tests silently change meaning.** A pre-existing "caps the fold at
   limit" test that built 12 *identical* fixtures now asserts `length 4` against
   a correctly-collapsed `1`. That is a fixture problem, not a regression —
   rebuild such fixtures with distinct discriminators before assuming the new
   code is wrong.

### Read the real signal field before writing the classifier

Grep the type definitions for the discriminator union first. Guessing a
plausible-looking field (`status: "demoted"`, `kind: "reject"`) when the actual
mechanism is a dedicated tag (`runtime_kind: "decision_flagged"`) produces a
queue that is silently always empty — the worst failure mode, because it looks
like "nothing needs attention."

When a signal row *references* another record, deep-link to the referenced
record (`references_entry_id || id`), not to the signal itself.

## Rule 3 — KPIs are navigation, not decoration

A metric that cannot be clicked is a dead end. Give the KPI component an
optional `href` and point each at the filtered view it summarizes
(`/runs?view=attention`, `/runs?view=failed`). Recolor by severity: a non-zero
"failed" count should render in the danger token, zero in a calm one.

The single most damning audit finding is a dashboard stating a ~50% failure rate
as small grey passive text.

### PITFALL — the technically-true, practically-false metric

A windowed metric can be perfectly honest and still lie. Real instance: a KPI
read **"Failed (24h): 0"** while 24 of 50 runs sat failed — every failure was
older than the window. The number was correct; the page told the operator their
system was healthy when half of it was broken.

**Before shipping any windowed, filtered, or thresholded metric, ask what it
reads as when the window is empty but the underlying condition is severe.** If
"0" would mislead, show the unqualified total and demote the window to a
qualifier: `24 · 48% of all runs`. A denominator-bearing hint ("% of all runs")
turns a raw count into a judgement the reader can act on.

This is the same discipline as never fabricating detail, applied to aggregates:
the honest-but-misleading number is worse than a missing one, because it
actively buys false confidence.

## Leadership analytics: review records, do not rank people by proxies

When the user asks to "think like an SE leader" and expose insights in a small dashboard,
replace the long static score report with a compact review workspace: Overview / People /
Records / Methodology. First-fold questions are **what needs inspection, what was recorded,
what changed, and what can be traced** — not who won a heuristic leaderboard.

- Provide composable date, cohort, person, category, lifecycle-status, review-signal and
  full-text filters. Every KPI, chart, table, drill-through and export must consume the
  same filtered projection. Show the active window and denominator; reset pagination on
  filter changes. Missing values stay unknown, not zero scores.
- Separate activity date, creation date, snapshot date and completion status. A `since`
  query supplies no upper bound. Default retrospective views end at the **snapshot date**;
  future tasks require explicit inclusion. For snapshot-based attention queues, compare
  deadline calendar days with the snapshot day in a named time zone; a same-day deadline
  is not overdue at midnight. Use injected `now` only to assess snapshot age. Suppress
  deadline flags when the snapshot timestamp is invalid, and show that limitation beside
  the counts. Past-dated open tasks are not verified delivery.
- Unique directory/CRM IDs do not verify aliases. For a team cohort, discover the verified
  manager's direct-report records first, then match exact names/emails and query by those IDs.
  Successful alias resolution, collision-free GUIDs, and repeated zero results over longer
  windows can all describe the WRONG person. Show unresolved mappings as coverage to validate,
  never employees who "do nothing." A regional pod is not a national census.
- An identity correction invalidates downstream comparisons, not just one label. Preserve the
  superseded snapshot, withdraw unsupported findings, replace the resolver, refresh every
  affected member, recompute aggregates and update verification badges from actual evidence.
  Re-run browser checks against the refreshed dataset; old hardcoded totals are not a release
  test for new data. In the HoK review, six allegedly silent SEs were six wrong identities.
- Documentation length and regex outcome words measure properties of text, not work quality,
  attendance, business impact or credit eligibility. Label scores experimental, retain
  sample sizes, and let the reader inspect full untruncated records and source IDs.
- Repeated descriptions and same-person/date/category clusters are **review candidates**,
  not proven duplicates. Before recommending more logging, check whether the work is
  already represented. Improve accurate capture, evidence and lifecycle hygiene, not counts.
- Use neutral labels such as "Empty/template" and "Limited context," not "ghost employees"
  or "nothing happened." Cohort comparisons need explicit denominators and category/status
  context; raw team totals and writing-score gaps do not establish productivity differences.
- Separate the CRM record owner from observed SE contacts and pod participation. Show the
  recorded owner, flag reason and exact source link; do not turn the first attributed SE
  into an invented next-action owner or imply that a deduplicated row lists the complete team.
- Require comparable historical evidence before adding "what changed" or trend claims.
  With one snapshot, show current recorded conditions and its as-of date instead.

### Cross-layer CRM insight contracts

- Compare rendered lifecycle KPIs with backend rollups from the same real snapshot. A frontend regex can pass fixtures yet count Hygiene/Duplicate as overdue; unknown status is not active, and blocked can also be overdue.
- Keep formatted money separate from currency codes. OData formatted amounts such as `$212,000` are display strings, not ISO currency identifiers; never concatenate them with the numeric amount again.
- Audit population and aggregation grain per metric before declaring conflicting counts a bug. From one real snapshot, enumerate all retrieved records, explicit milestone-team records, active records and terminal exclusions, then trace each headline/chart to its population. A broad opportunity-context risk count need not equal a team-credited work-review count; label the distinction and make each drilldown return its exact source IDs. A deduplicated monetary total does not prove coverage or charts are deduplicated. Test accounts shared across pods and name the unit: unique accounts versus account–pod gaps.
- Check partial scope in persistent headline cards as well as the source-health panel. With a pending director, label people counts as loaded SEs rather than totals across all directors; warnings confined to a secondary tab do not qualify the headline elsewhere.
- Verify a drill journey by clicking actual controls and comparing rendered child IDs with exact source joins. Inspect click handlers as well as `href`: a placeholder anchor may open its destination programmatically. Observe both newly created and reused named tabs; require a destination assertion, because an empty new-tab list must not let the test pass without checking anything. Direct route loads prove rendering only; array filtering followed by the same filter assertion does not prove UI isolation.
- Wait for route rendering and layout to settle before measuring. Old DOM can satisfy a selector immediately after a hash change; test filtered Back to results again after deep-page reload.
- Distinguish scroll-container cropping from an obstructing footer. Check the container boundary, scroll to the final record, and hit-test its controls before treating a partially visible intermediate row as an overlap bug.

### Filter state is part of the evidence contract

- **Inspect actual controls, not the component name.** A card styled like a button is not
  navigational unless click/keyboard activation opens the exact rows behind its metric.
  Test the resulting record count against the KPI. Link labels to inputs and make clickable
  table rows keyboard-operable.
- **Reset restores the documented default scope.** If the default excludes future tasks,
  Reset must not silently clear the upper date bound. Keep an explicitly named all-source
  preset for that broader view. Tab changes preserve filters; filter changes reset paging.
- **Search and export must share committed state.** A debounced search can leave the visible
  input ahead of the projection: an immediate Export click downloads the previous cohort.
  For small local snapshots, update synchronously and restore input focus/caret after render.
  For larger sets, flush pending search before navigation/export or disable those actions
  until the projection catches up. Test type → immediate export, not just export after a wait.
- **Label what the aggregate actually counts.** Records in a same-day cluster are not pairs;
  a category's share divides by the filtered total, not the largest category. A detector
  missing outcome words is not a finding that the note contains no result. Preserve unknown
  durations and scores; do not surface local fallback keys as real source IDs.

Parent verification is still required after delegated UI work. Exercise the built artifact,
including empty intersections, full-record text, filtered export contents, safe reset and
mobile table/dialog geometry. See `references/leadership-activity-review.md` for the completed
review and the defects that passed the first implementation.

## Rule 4 — Navigate by verbs, not by your architecture

Sidebars grouped by internal planes/layers/services encode the *implementer's*
mental model. Operators think in tasks: "why did that fail", "what's waiting on
me". Watch for several sibling nav entries that are really **views of one
dataset** — those belong as tabs inside one destination, not as peers competing
in the nav. A 15-item nav where no item says "what needs you" is a symptom.

For imported cockpit or template menus, enumerate the actual surface catalog and
count implemented views, handoffs, partial capabilities, and unavailable entries
programmatically. Click representative entries to verify those classifications;
a selectable label is not an implemented feature. Recommend moving unavailable
concepts and implementation labels such as "ZIP Surface Index" into a capability
status view, not the leader's daily navigation. Check whether persistent KPIs plus
a second summary row push the actionable owner/evidence list below the fold.

## Rule 5 — Test the projection before wiring any component

Start with pure behavior contracts: ranking, within-bucket recency, time boundaries,
real destination links, missing fields and rows without source IDs. Run them through
the repository's actual test command; tests requiring undeclared framework globals
are not a green gate.

Then wire the REAL projection into the UI test harness, not a separately invented
stand-in. Check object-valued exclusions render as readable counts, reason enums get
human labels, and search finds every field its placeholder promises. A stub returning
a string where production returns an object can conceal `[object Object]` output;
a more capable stub search can conceal missing owner/contact search.

Test absent payload, absent record collection, unknown member counts, partial scope,
and a genuinely complete empty population separately. Reject null before numeric
coercion or currency formatting, because `Number(null)` and display helpers can turn
unavailable data into a convincing zero. Keep unavailable/partial states visible in
both the headline and the empty-state copy.

**PITFALL — pin `now` in every time-sensitive test.** A test that omits an
explicit `now` uses the wall clock, and any machine with clock skew (or a
fixture authored relative to a different day) silently drops the
time-thresholded item. Symptom: exactly one test fails while the rest pass, and
the missing element is always the stalled/expired one. Thread an explicit `now`
through every call and derive all fixture timestamps from it.

## Sequencing a "fix the UI" request

1. Screenshot the deployed top-3 surfaces; `vision_analyze` for hierarchy.
2. Diff findings against the project's own design spec; quote the violated line.
3. **Enumerate the fixes and their blast radius before coding.** Identity-level
   changes (nav restructure) are a different risk class from additive ones
   (a new fold-one panel) — say so and let the user choose scope.
4. Build the pure projection + tests first.
5. Wire components only once tests are green.
6. Verify with `tsc --noEmit`, the full test suite, and a fresh screenshot of a
   local build — before spending a cloud build/deploy cycle.
7. **Re-screenshot after the redesign and `vision_analyze` again.** This is not
   a formality: the first post-fix screenshot is where duplicate-row noise and
   misleading-metric bugs surface. In a real session, `tsc` was clean, 175 unit
   tests were green, and the production build succeeded — while two serious
   legibility defects were plainly visible on screen. **Green gates are
   necessary and never sufficient for a legibility claim.** Loop
   screenshot → fix → screenshot until the fold is scannable.
8. Report status split into verified-live / verified-locally / implemented-but-
   unproven / not-started. Never collapse those into "done."

## Related judgement — when the ask is "should we re-architect?"

A UI/product frustration ("devs can't use my UI", "can we make this an engine")
often arrives as an architecture question. Separate the two problems before
answering: reach (who can consume this) is usually solved by a headless/API/MCP
lane, while generality is an abstraction question that needs a **second real
consumer** to justify it. An extraction with one consumer is speculative
infrastructure no matter how clean the seam looks. When the user asks "should we
do it, is there real value?", they are inviting a genuine no — give the
recommendation and the cheaper alternative (reposition first; spike the second
consumer hardcoded and ugly), not a menu of options.

## Support files

- `references/attention-queue-worked-example.md` — the full audit transcript:
  exact spec-violation quotes, the wrong-field classifier bug, the clock-skew
  test failure, and the shipped-vs-unproven split.
- `references/local-standalone-repro-and-token-drift.md` — running a monorepo
  standalone build locally against live backends (path trap, asset staging,
  headless-Chrome screenshots, build-time-inlined env vars), plus the
  design-token drift audit and its linter false-positive class.
