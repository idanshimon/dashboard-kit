---
name: operator-dashboard-legibility
description: "Use when building, auditing, or fixing an internal operator/admin dashboard — attention-first information hierarchy, triage grouping over flat lists, navigation grouped by user verbs, honest KPIs, data freshness and shelf life, demo-mode semantics, and design-token/DESIGN.md drift audits. Triggers on 'I don't get what I'm looking at', 'this looks like a prototype', 'nothing tells me what needs me', 'how do we know when this was last updated', or any dashboard that opens with a marketing hero."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [ui, ux, dashboard, operator, design-tokens, nextjs, legibility]
    related_skills: [design-md, google-stitch, ui-vision-qa-loop, dashboard-ux-table-not-cards]
---

# Operator dashboard legibility

Internal operator/admin surfaces (governance consoles, run dashboards, audit
tools) fail in a consistent, predictable way. This skill encodes the failure
modes and the fixes.

Audience is a tech lead / compliance owner / on-call engineer — **not** a
prospect. Every pixel does work; decoration is the enemy.

## Audit checklist — run this before touching code

1. **Read the project's own design spec first** (`DESIGN.md`, `globals.css`
   `:root`, `components/ui/*`). The violation you are about to fix is often
   already forbidden in writing. Quote it when you report.
2. **Screenshot the live/deployed surface**, not localhost. Then answer:
   *what needs a human right now, and can I click it?* If the page cannot
   answer that in the first fold, that is finding #1.
3. **Count nav items and read their names.** If they are your service /
   layer / plane names, the nav is an architecture diagram.
4. `grep -rEo "#[0-9A-Fa-f]{6}" src --include=*.tsx` — token drift. Then the
   drift a hex-grep CANNOT see: `grep -rn "var(--[a-z-]*)\]/[0-9]" src` for
   hardcoded alphas on theme-aware colours, `grep -rn "dark:text-"` for
   Tailwind colour pairs in an app that themes via a `.light` class, and
   `grep -rn 'bg-\[color:var(--color-ink)\].*text-white' src` for inverting
   tokens behind fixed text. **If the app ships a light theme, screenshot it
   too** — a dark-tuned dashboard's light mode routinely fails AA in code
   blocks and diff rows while every other surface looks fine. Better: run
   `scripts/check-contrast-tokens.ts`, which covers the last two mechanically.
5. Check every KPI for whether it can render a comfortable zero.
6. Read each chart without hovering: identify the metric, units, numeric Y-axis
   ticks, time basis and whether panels share a scale. Put these on the chart,
   not only in a tooltip or baseline annotation. When the user asks what an axis
   means, answer directly from the displayed chart and its producer; do not
   confuse a nearby risk badge with the plotted quantity. Independently scaled
   small multiples must say so, because equal heights do not mean equal values.
   On mobile, verify the rendered SVG text remains legible: shrinking a wide
   viewBox shrinks labels too; adapt chart geometry rather than merely its CSS width.

## The five failure modes

### 1. Marketing hero on an operator tool

A gradient banner with a tagline and a value-prop paragraph owns the first
fold, telling the operator something they already know. Kill it. The product
explainer belongs behind a footer link. **Fold one is "what needs me".**

### 2. Nothing surfaces what needs a human

A flat reverse-chronological table buries the rows that actually require
action. Build an **attention queue**: a pure, unit-testable projection over
existing evidence.

```
buildAttentionQueue(items, signals, { now, limit })
```

- Rank by consequence: **blocked > failed > flagged > stalled**; newest-first
  within a band.
- Keep it PURE — no React, no fetching, `now` injected — so ranking and copy
  are testable without a DOM.
- Every row must state its consequence in plain language, carry a real
  timestamp, and have a working action link. *"Who did what, and can I click
  it?"* is the acceptance bar.
- **Never fabricate a reason.** Derive it from the record (walk the event
  stream backwards for the last failure message); fall back to a neutral
  phrase and assert in a test that no literal `undefined` reaches the copy.

**Collapse duplicates or the queue is unreadable.** Six rows reading
"A run is waiting at resolver" teach nothing. Group by `kind + title`, emit one
row with a `count` badge, pluralize the title, retarget the link to the filtered
queue, and report the **oldest** member's age so the row isn't falsely fresh.
Then fix the three knock-ons: the summary badge counts the FULL set, the
"N more" link sums `count` not `length`, and any test that built N identical
fixtures to exercise a CAP now collapses to 1 — give those distinct keys.

### 3. Flat lists where triage is needed

Group by what the user DOES about it — `Needs you / Failed / In flight /
Completed` — newest-first inside each band, terminal states collapsed by
default, anomalies badged. Offer it as a view mode alongside table/cards and
make it the default. Let a summary KPI deep-link into a band via `?view=`,
overriding the stored preference for that visit.

### 3b. Autonomous SDLC & agent-loop consoles: split human decisions from agent execution

When the operator's goal is an agent-managed pipeline where humans intervene only by exception, fold one must split the work into two side-by-side queues:

- **Needs Your Decision** (left): triage asks and gate-escalated PRs, with in-place decision controls wired to the real approval/dispatch endpoint. Never render bare generic buttons (`Option A`, `Option B`) without inline meaning — append the concise option effect (`Option A — <consequence>`, stripping trailing periods before adding `…`) and separate auxiliary inspection links (`Evidence`, `Issue ↗`) onto a secondary row so choices never crowd 6+ buttons together. Preserve open inline inputs across background SSE refreshes.
- **Agent Decisions & Loop State** (right): active coding runs, home-watcher auto-retries, and merged PRs waiting on live release verification. When merged fixes stall at verification because a downstream release gate is failing, state that causal link in a banner above the list so queued merges do not look mysterious.
- **Closed-loop circuit + hover mental-model lens**: render production pipeline stages, institutional memory (`decisions` / `lessons`), and SDLC beats on one connected board with explicit feedback bridges between bands (Failure → Retry → Triage; Memory ↔ Scoped Recall & PR Citation Gate; Owner/Verify → Precedent Minting & Live Verify). Pair every node, rule chip, bridge, and work token with a hover/focus overlay that fades in what that element does right now plus its upstream/downstream role while highlighting linked elements (`[data-dream-linked]`) — anchored strictly outside the trigger's bounding box and capped at ~230 chars so it never hides its own target or renders a wall of text.

For current-work summaries, join severity to the workflow beat before labeling ownership. An at-risk triage hand-off can be unassigned while an at-risk verification record is already merged. A closed issue may have owner replies: never compute historical autonomy as total items minus today's owner queue. Test both at-risk beats in the same render.

### 4. Navigation grouped by architecture

Group by **user verbs** (Operate / Govern / Analyze / Configure), never by your
internal decomposition. Nobody thinks "I need the Ledger Plane."

- **N views of ONE dataset are TABS, not N nav siblings.** Rendering the
  switcher inside a shared `PageHeader`, gated on the route prefix, keeps every
  route reachable and puts the control in the same place on each page.
- When you remove a grouping key, check what it was rendering — a section-level
  field often drives a colour dot or badge that silently disappears. Preserve
  the semantic as a per-item accent instead.
- Making a shared layout component a client component (`usePathname`) affects
  every page that imports it. Re-run typecheck + FULL suite + production build,
  not just the page you touched.

### 5. KPIs that tell comfortable lies

A "Failed (24h): 0" while dozens of items sat failed — every failure was >24h
old. Technically true; it hid the single most important fact on the page.

**Rule: a headline health KPI that can render 0 while the underlying problem is
large is a misleading KPI.** Windowing is for alert queues. Headline numbers
show totals, ideally with a share ("24 — 48% of all runs").

### 5b. Under-claiming is also lying — and it trains the reader to ignore you

The mirror image of an inflated KPI, and easier to ship because it feels safe.
An overview page was `force-static` over a one-time JSON seed, so it asserted:

| Claimed | Actually |
|---|---|
| "Vehicles **7,921**" | 2,512 tracked (filtered set) |
| "sweeps are **not wired up yet**" | 144 sweep jobs had run |
| "**nothing here is live**" | all of it was live |

Every statement was cautious, and every one was false. A dashboard that
under-claims is not "safely honest" — it is wrong in the other direction, and
worse, it teaches the reader that the page is stale so they stop reading it.

Two mechanical causes to grep for:

- **`force-static` / `export const dynamic = "force-static"` on a page that
  reads counts.** Frozen at build time by construction.
- **A page importing a seed/fixture JSON** (`import seed from "@/data/*.json"`)
  while a real datastore exists.

Fix by making every figure a query, and let the honesty banner be
*conditional* — only warn when there is something to warn about. A caveat
banner that is always on is a banner nobody reads. Re-audit provenance copy
whenever the pipeline it describes changes; stale disclaimers outlive the
condition they described.

### 5c. Coverage without freshness is uninterpretable

"1,504 of 2,512 have a price" means nothing until the reader knows whether that
was an hour ago or a week. Freshness **qualifies** coverage, so it renders
first — above the coverage strip, not below it.

**The trap: a pipeline usually has more than one clock, and they disagree.** An
inventory pass may write a row for every record while carrying none of the
expensive field (verified 2026-08-30: one batch was 1,081 rows, **0 priced**).
A single "last updated" sourced from whichever job ran most recently reported
*8 minutes ago* while the prices were **4 hours** old.

- Track the timestamp of the EXPENSIVE field separately (`lastPriceAt`) and
  lead with it.
- Show the cheap-pass timestamp only when it DIFFERS — otherwise it is the same
  fact printed twice.
- Go amber past a staleness threshold rather than always-on.

**Measure "N updated since" against the previous RUN, not a rolling window.** A
sweep is bursty (dozens of sources over several minutes), so a fixed 24h window
splits one run across two buckets and reports half of it. Detect runs by gap —
`>30 min` between observations starts a new one — and validate the grouping
against real data before trusting the number.

```sql
case when observed_at - lag(observed_at) over (order by observed_at)
          > interval '30 minutes' then 1 else 0 end as new_run
-- then: sum(new_run) over (order by observed_at) as run_id
```

If snapshots are stored **change-only**, a second row for an entity already
means the value moved — the change count is a `having count(*) > 1`, no diffing
required. That is the payoff of the change-only write decision.

### 5d. A number is only actionable with its shelf life

A discount, quota, or entitlement shown as a bare figure reads as permanent.
When part of it expires, say so **next to the number it qualifies** — not in a
separate column, which divorces the deadline from the figure and gets scanned
past.

If every record shares one deadline (a regional promotion window), render the
date ONCE as a page-level banner and give each row only a countdown plus its own
amount. Repeating the same date on 50 rows is noise, not information.

**Scope any headline claim to what is actually on screen.** A page-level "0% APR
available" pulled from the whole catalogue is a lie the moment the reader
filters to a model financed at 3.99%. Derive such claims from the *filtered* set
and verify across filter states, not just the default view.

### 6. Rows that name an entity but go nowhere

The audit bar is *"who did what, and can I click it?"* — and the second half is
the one that gets skipped. A queue that names a vehicle, run, or customer and
then dead-ends forces the reader to go find it by hand, which is the work the
dashboard exists to remove. Verified 2026-08-30: an alerts page listed price
drops per VIN with no link anywhere (*"i see the alerts but cant click to get
to the listing"*).

Give every entity row the destinations the reader actually wants — typically
the record in-app, the external source of truth, and the next action.

**Then verify the link's filter EXISTS.** Adding `?vin=…` links was useless
until the query layer learned a `vin` filter; before that the param was
silently ignored and every link landed on the unfiltered list — a link that
looks like it works. Grep the query builder for the param you just linked to
before claiming the row is clickable.

**Beware the conditional link — it breaks only SOME rows.** A title wrapped in
`{x.url ? <a href={x.url}>…</a> : <div>…</div>}` renders identically either way
(same weight, same size) but is inert whenever the field is null. Measured
2026-08-30: **271 of 2,512 rows (10.8%)** had no clickable target at all, which
the user reported precisely as *"on some rows"*. Always link to an in-app
fallback destination that is guaranteed to exist, and treat the external URL as
an ADDITIONAL action rather than the only one. When a user says a feature fails
"sometimes", look for a nullable field driving a conditional render before
looking anywhere else.

### 7. Raw exception strings shown as operator status

`Error: fetch https://host/path?model=X -> 403` repeated twelve times is not
information; it is the same three problems printed twelve times, and it makes
the reader decode a stack trace before it means anything (*"most of the alerts
on top has some errors we need to be better at error handling and logging"*).

Classify at READ time into a stable code + human summary + **remedy**, then
group by cause:

| Raw | Rendered |
|---|---|
| `Error: fetch https://a.com/... -> 403` | **Blocked** · "a.com refused the request (403)." · *Fix: bot protection…* · retryable |
| `Error: fetch https://b.com/... -> 404` | **Wrong URL** · "No inventory page at the address we tried." · *needs a code change* |

Rules that made it work:

- Store the machine-readable shape (`... -> 403`) but strip the stack; classify
  on read so old rows re-render correctly when the classifier improves.
- Group by code — "8 dealers block us, one fix" beats eight separate mysteries.
- Say whether it is **retryable** or **needs a code change**; that is the only
  bit that changes what the operator does next.
- Assert in a test that no rendered summary contains `http` or `Error:`.
- **Rank which error you surface.** When several candidates fail, the LAST error
  is usually the least informative. A 404 means *we* guessed the URL wrong and
  will mask a 403 on a URL that exists — the user caught exactly this
  (*"fred does have inventory page"*). Rank bot-challenge/403/5xx above 404.

### 8. Saved views must store the URL and show LIVE counts

Once a list has facets, search, and sort, the reader will want to keep a view.
Two decisions determine whether the feature is useful or decorative.

**Store the QUERY STRING, not a parsed filter object.** In a URL-driven list the
querystring is already the canonical representation of a search — facets, sort,
free-text and toggles all live there. Serialising a second shape means two
formats to keep in sync, and the parsed one silently rots the next time a filter
is added.

```ts
await db.insert(savedSearch).values({ name, filters: params.toString() });
// restore: <Link href={`/listings?${s.filters}`}>
```

**Re-run each saved view on page load and show its CURRENT count.** A saved
search frozen at the number from the day it was saved is decoration; noticing
that *"Calligraphy under 40 miles"* went 12 → 19 is the entire point. Decode the
stored querystring back into readable criteria (`SANTA FE · Calligraphy · priced
only`) so the row is legible without clicking, and say plainly that counts are
live.

Only offer the Save control when something is actually filtered — saving "all
2,512 vehicles" is just the list's own nav link.

**A schema table is not a feature.** `saved_search` had existed since the first
migration, unread and unwritten — dead schema that looked like shipped
capability. Grep for the type before building storage for it; and never let the
presence of a table imply the surface exists.

### 9. Live-streamed boards must refresh SILENTLY

A board that re-renders `innerHTML` on every stream tick replays its entry
animation, resets bars to zero and jumps the scroll. That is fine on an overview
and maddening while someone reads ONE record. Treat it like a market ticker:

- Rebuild (with entry animation) ONLY when the viewer's key changes: persona,
  selected record. On a tick, diff the new markup into the existing DOM and
  touch only changed text/attributes.
- A changed number gets a faint direction tint that fades in ~1.5 s: no motion,
  no layout shift. None under `prefers-reduced-motion`.
- `font-variant-numeric: tabular-nums` on every live number, and a fixed height
  on trend slots ("trend building…" vs SVG), so nothing below them moves.
- Prove it in real Chrome, don't eyeball it: keep a reference to a board node,
  wait several ticks, then assert the SAME node is still there, text changed
  more than 0 times, and a mid-board element's `getBoundingClientRect().top`
  moved 0 px. Assert on visible shift, not `scrollTop`, which drifts a few px
  when the content height changes.

Recipe (morph function, SVG `className` trap, test harness):
`references/live-boards-and-persona-views.md`.

**Spatial boards (3D ring, bed map): position by a stable key, heat by metric.**
Place each entity by sorted id, never by the stream's score-sorted order, or
entities swap seats whenever scores cross. Encode urgency as a continuous
cool→hot ramp + height, eased per frame, with a per-persona legend. Centre the
scene in the free area between panels via the camera viewport, recomputed on
panel open/close. Ship entity search (`/`, id/initials/attributes, dim
non-matches) with the first version. Recipes and numeric checks: same file.

### 10. One dataset, several personas: same computation, different question

When the brief is "a dashboard for the doctor / nurse / finance", build ONE
surface with a persona switch, not three apps. Each persona board opens with
its question ("Is this patient getting worse, and why?" / "Who needs me next?"
/ "Where is cost risk building?") and renders values the server computed.
Add optional read-only fields to the API rather than recomputing in the
client. The action gate is identical in every persona. Persona in the URL.
Depth (what each persona needs, provenance rules for cost figures, ranking the
nurse queue): same reference file.

When asked "does it show REAL steps?", answer from the code path, not the UI:
a per-step table of what executes and whether it is real, a stand-in (offline
model, stub sink), or forced demo input, plus the profile that would make it
real. Put the same statuses on screen (a component strip) and in any launcher's
notes, so the demo never out-claims the backend.

## Demo mode is a DATA posture, not a fake backend

Recurring drift: "demo mode" degenerates into a simulated pipeline — canned
fixtures replayed from local storage, real submission paths disabled, backend
never touched. Such a demo can never show the product's actual claim
(a gate opening, a record landing in the database).

Correct semantics:

- Demo mode constrains **inputs** (curated synthetic data, no real
  PII/PHI) and keeps guardrails on. It does **not** stub the backend.
- Submissions go through the real API → real stages → real gates → real
  persistence.
- Fixture replay survives ONLY as an **offline fallback**, inside the `catch`,
  and it must announce itself: *"Backend unreachable — replaying a recorded
  run · this is a fixture, not live telemetry."* Never narrate a replay as live.
- Reads hit the real datastore. Seeded history may merge in as DEPTH
  (de-dupe by id, live wins, newest-first) but must never mask a read failure —
  surface an explicit `unreachable` state instead of silently rendering seed
  rows as current.
- Label it `DEMO DATA`, not `DEMO MODE`.

## Design-token drift

Any hex hand-typed in more than one file wants a token (e.g. a repeated
foreground literal on filled accent surfaces → `--on-primary`). Grep the old
literal to zero after introducing it.

When an app serves multiple screens from different renderers (hand-authored
cockpit + vendored chart/pipeline/story generators + same-origin iframes),
match every screen's palette and typography to the host's Dark and Light design
tokens (never leave a sub-route on a generator's default brand preset), inject
one synchronous pre-paint `<head>` theme resolver (`?theme=` → shared
`localStorage` key → `prefers-color-scheme`) plus a single `Dark / Light / Auto`
segmented control in the shared nav, broadcast theme changes via a window
`CustomEvent` (forwarded to child iframes so SVG/canvas views re-render live),
and hide per-template theme buttons when the shared nav is present (`body:has(>
.shared-nav) #page-theme-btn { display: none }`) so hosted routes never render
duplicate toggles while offline exports stay self-contained.

**Document sanctioned exceptions in the design spec**, or the next agent reads
forced hard-coding as sloppiness and "fixes" it into a broken theme. Canvas
libraries (Cytoscape.js, react-flow) style via JS stylesheets drawn to
`<canvas>`, which cannot resolve CSS custom properties — those files MUST
hard-code. State that values mirror `:root` verbatim, that a value with no token
counterpart is still drift, and that palette changes update those files in the
same commit.

### An INVERTING token behind fixed text is invisible in one theme

The nastiest drift class, because it *looks* like correct token usage:

```html
<!-- WRONG: white-on-white in dark mode -->
<a class="bg-[color:var(--color-ink)] text-white">Calculate</a>
```

`--color-ink` **inverts** with the theme (`#171a20` light → `#f4f4f5` dark).
The author wrote it meaning "ink = dark", which is true in exactly one theme.
The fill flips to near-white while `text-white` stays put. Measured on a live
page 2026-08-30: **1.10:1** — not low contrast, *no* contrast. Reported by the
user as "hard to see"; it was unreadable.

Rule: **a filled control must use a token that is stable BY INTENT.** An accent
token qualifies — it may shift hue across themes (`#3e6ae1` → `#3368ff`) but
never crosses the light/dark boundary, so fixed white text stays legible.
Semantic ink / canvas / surface tokens do NOT qualify.

Once you find one, grep the pattern — the same author instinct repeats. One
report on an alerts page led to **six** instances (save button, filter chips,
active facet pills, pagination). A companion bug rode along: hard-coded palette
pairs like `text-blue-600 dark:text-blue-400` bypass the token system entirely
and measured **1.29:1** on a black canvas.

**Guard it with a SOURCE LINT, not a unit test** — this failure is invisible to
any DOM-free assertion, and a screenshot only proves the theme you happened to
render. Bundled: `scripts/check-contrast-tokens.ts` walks `.tsx`, parses every
`className`, and fails on (a) an inverting token behind fixed
`text-white`/`text-black`, (b) hard-coded palette colours. It earned its place
immediately by catching a `stone-500` in a file a scripted colour migration had
skipped because that file wasn't in the sweep list.

One false positive to expect: a translucent fill (`rgba(255,255,255,0.04)`) over
a dark canvas can't be resolved by naive ratio math, which reads the alpha
colour literally and reports ~1.1:1 while the composited result is ~18:1. Say so
rather than silently filtering it out.

### Tokenize tint STRENGTH, not just hue — the light-theme trap

A theme-aware `var()` with a **hardcoded alpha** (`bg-[var(--success)]/10`) is
drift that a hex-grep cannot find. A light theme correctly *darkens* its accents,
so 10% of an already-dark green on white is almost no fill — the theme does the
right thing and the baked alpha undoes it. Counter-intuitive rule:
**darkened accents need MORE alpha on light surfaces, not less** (8/12/16% dark →
12/18/24% light). Put the strength in the theme as `--tint-weak/--tint/--tint-strong`
and consume it via `color-mix()` in a real class.

Two companions to check in the same pass:

- **Tailwind mid-tone stops fail AA on white** — `green-500` measures **2.28:1**,
  `blue-500` 3.68:1, `indigo-500` 4.47:1. None pass.
- **A `dark:` variant may never fire.** With `next-themes`
  `attribute="class"` the app toggles `.light` and re-themes through CSS
  variables, so `text-blue-500 dark:text-blue-300` defends the side that was
  never broken. Confirm how the app themes before trusting any `dark:` prefix.

Compute the real contrast ratio rather than eyeballing it, and sweep the whole
app (21 files / 52 occurrences in the real case) with a scripted migration, not
by hand. Ratios, the sweep script, the colour-blind-safe inset rail, and the
port-squatter screenshot trap:
`references/light-theme-contrast-and-tint-tokens.md`.

## Verification

1. Typecheck → **full** unit suite → **production build**. The production build
   is the gate that catches `useSearchParams` outside `Suspense`; typecheck and
   unit tests both pass while prerender fails.
2. Serve the built artifact against LIVE backends with real credentials.
   Monorepo-root Next.js builds put the entrypoint at
   `.next/standalone/server.js`, not under `apps/<app>/` — `find` it rather
   than guessing. Copy `.next/static` and `public` INTO `.next/standalone/` or
   every asset 404s and the page renders unstyled.
3. Headless screenshot → vision-analyze. Byte size is a fast triage proxy:
   tiny (~17KB) = error screen, large (>150KB) = real content.
4. **Re-screenshot the PUBLIC URL after deploying.** A 200 is not proof the new
   bundle rendered.

## Pitfalls

- **Your verification script is a suspect too — check it before reporting a
  regression.** Three false alarms in one session, all my tooling, none the app:
  a `sed` pipeline ate the HTML and I twice called a working page "empty"; a
  regex counted **0** rendered badges because React splits interpolated text
  with `<!-- -->` comments (`$3,000 mfr · <!-- -->8<!-- -->d left`), so `8` and
  `d left` were never adjacent; and a grep for design tokens ran against the
  page HTML when Next.js had emitted them into a linked stylesheet. Before
  reporting "the feature didn't ship", run the checker against known-good input
  and inspect the RAW bytes. Announcing a false regression costs more trust than
  the bug would have.

  Standing rule for HTML assertions: **strip `<!-- -->` comments BEFORE
  stripping tags**, or every interpolated number is severed from its label.
  When a check says a feature is missing but the page renders, `grep -oE
  '<target>.{0,80}'` the raw bytes and look at what is actually there.

- **When a check DISAGREES with a sibling surface, the check is the lead
  suspect — and so is the number.** A freshness bar reported "1,151 price
  changes" while the alerts page listed 2. Both read the same table. The
  disagreement was the entire tell: the count used "entities with >1 row",
  justified by a belief that writes were change-only. That belief was **false in
  practice** — re-running a sweep writes a fresh row at an unchanged value, so
  1,151 rows were duplicates at identical prices. `count(distinct value) > 1` is
  the honest predicate; it returned 2, matching the sibling page.

  Two generalisations worth carrying:
  - A design invariant you *implemented* ("we only write on change") is not the
    same as one that *holds* — retries, backfills and `--retry-failing` reruns
    all violate it. Verify the invariant against the data before deriving a
    headline number from it.
  - Guard such a number by asserting the strict count **cannot exceed** the
    loose one, and by printing every claimed instance with its actual value
    sequence. A wrong count should be *visible*, not merely large.

- **A scripted colour migration can erase an affordance while passing every
  check.** A `perl` rule mapping `decoration-stone-300` AND
  `hover:decoration-stone-900` onto the same hairline token produced
  hairline-on-hairline: the underline was invisible at rest *and* on hover, so
  2,241 working links looked broken (*"i lost the links on the listing"*).
  Typecheck, build and a hex-grep all passed — the colours were "correct
  tokens". After any sweep, diff the CLASS PAIRS that encode a state change
  (rest vs hover, default vs active) and confirm they still resolve to
  different values. A migration that collapses two states into one is a
  regression no colour lint will catch.

- **A sortable column that renders, links, and silently does nothing.** Adding
  clickable headers is half the job; the ORDER BY branch for each column has to
  exist. Five of eight columns had no sort implementation at all, so those
  headers would have been decorative. Test the property that catches it:
  **asc and desc must return a DIFFERENT first row** — "the page still loads"
  proves nothing. Also give each column its own sensible first direction
  (alphabetical opens A→Z, money and discount open BIGGEST-first; defaulting
  everything to ascending puts a $0 discount at the top of the column the user
  clicked precisely to find the largest one), and drop `?page` on sort change
  so the reader doesn't land on page 7 of a freshly reordered list.
- **Sorting is a data-quality instrument — run it before shipping.** Making
  columns sortable surfaced two real corruptions instantly: `msrp-asc` led with
  a $895 luxury SUV (a doc fee parsed into the MSRP field) and `discount-asc`
  led with −$2,389 (190 stale rows from before a parser fix). Both were
  invisible in the default view. After adding any sort, click every column's
  extremes and ask whether the top row is *possible*.
- **Search must route on the SHAPE of the query, and the facets must follow
  it.** An identifier fragment (the last 6 of a VIN off a sticker) and a word
  need different predicates — one LIKE across a concatenation of every column
  matches trims and colours containing those digits and returns confident junk.
  And the sidebar keeps its own WHERE clause, so searching a dealer name still
  advertises `Towne Hyundai (333)` unless you add the predicate there too.
  Regression bar, routing assertions, and the correlated-subquery trick for a
  facet query that lacks your join:
  `references/list-search-and-facet-integrity.md`.
- **`position: sticky` resolves against the nearest SCROLL CONTAINER, not the
  viewport.** A `th { position: sticky; top: 60px }` written to clear a 60px page
  nav parks the header 60px *down inside* any `overflow-y:auto` wrapper, where it
  sits visibly detached while rows scroll past — the symptom a user reports as
  "the header is stuck when scrolling". Scope the rule to the container
  (`.scroll thead th { top: 0 }`) and answer *"sticky inside what?"* before
  writing any `top:` value. The follow-on bug lands immediately after the fix:
  `border-collapse: collapse` strips a sticky header's own border, so rows bleed
  through it. See `references/self-contained-html-dashboard.md`.
- **Green tests are necessary, not sufficient, for any surface a human reads.**
  In one pass, 179 passing tests missed both a wall of six identical rows and a
  KPI reporting 0 against a 48% failure rate. Vision caught both. Budget a
  screenshot pass on every UI change.
- **A pure function that calls `Date.now()` internally is clock-dependent and
  untestable.** Thread an injected `now` through every formatter and comparison.
  A test failing on relative-time copy is usually a real design defect, not a
  bad assertion.
- Build-time-inlined env vars (`NEXT_PUBLIC_*`) are set by Dockerfile `ARG`
  defaults, **not** by runtime container env. A flag that looks right in the
  container config can still be wrong in the bundle. Pass it as `--build-arg`,
  and match the prior image's value unless deliberately switching — say so
  when you do, since it can change security posture.
- Deploy by image **digest**; tag reuse won't repull. Confirm the new revision
  is `Running` at 100% traffic before claiming a deploy.
- Ignore LSP diagnostics emitted immediately after an edit that deleted the
  offending lines — they can reference the pre-edit buffer. Re-run typecheck.
- Removing a variable used in a conditional? Grep for it. A leftover reference
  in a distant JSX branch compiles fine in tests and fails typecheck.

## Worked example

`references/agentic-sdlc-ledger-insights-ui-overhaul.md` — the full 2026-07-26
pass on `agentic-sdlc/apps/ledger-insights-ui`: diagnosis, the four commits,
exact ledger field mappings, the `NEXT_PUBLIC_DEMO_MODE` Dockerfile-ARG trap
with working build/deploy commands, the local live-data preview recipe, and the
three test-design corrections.

`references/self-contained-html-dashboard.md` — the **single-file, zero-dependency**
variant, for dashboards over confidential data that must open anywhere with no
build step: skeleton-then-patch authoring (a rich one-shot `write_file` times
out), the sticky-header-inside-a-scroll-container bug and its `border-collapse`
follow-on, structural verification when you cannot open a browser, and
hand-rolled SVG charts including a learned-baseline band.

`references/system-mission-control-page.md` — full recipe for a live pipeline + autonomous agentic-SDLC mission-control cockpit: verdict hero, split human-decision vs agent-execution console, dual-loop pipeline↔memory↔SDLC circuit with hover mental-model lens, scheduled-vs-actual swimlanes, CSS-variable themes read into SVG, real 390px phone verification, parser/denominator/volume-cache pitfalls, and LAN/Cloudflare-tunnel ops.

`references/data-freshness-and-shelf-life.md` — worked recipes for §5c and §5d:
the two-clocks trap (a cheap pass reporting "8 minutes ago" while the expensive
field was 4 hours stale), the gap-based run-detection SQL for "N updated since"
plus the `minute`-is-reserved gotcha, free change-counting when snapshots are
change-only, finding an expiry a vendor renders client-side (grep the served
HTML for the `{{ interpolation }}` tell, then read
`performance.getEntriesByType('resource')`), the model-name normalization that
stops a join from silently matching nothing, lookup-not-row-wise-join, scoping
a headline claim to the filtered set, and the React `<!-- -->` text-node split
that makes a working feature grep as broken.

`references/list-search-and-facet-integrity.md` — adding free-text search to a
list that already has facets, sorting, and deep links. Why identifier fragments
and words need DIFFERENT predicates (and how a single shared LIKE returns
confident junk), the concatenate-then-AND pattern that lets one query span
model/trim/dealer, asserting the ROUTING and not just row counts, the
nonsense-query-returns-0 test that catches a predicate degrading to no-op, and
the two traps in making facet counts honour the search.

`references/reading-a-blocked-sites-design-system.md` — when the brief is
"make it look like <famous site>". **Do not design from memory** — measure the
real tokens over CDP through the user's own already-running Chrome, which is
not automation-flagged even when `curl`, headless Chrome and headed Playwright
all get "Access Denied". Includes the `font-family: Times` tell for a challenge
page, the one-call dump that recovers a site's entire spacing/type/radius/grey
scale from its CSS custom properties, the `__name is not defined` trap when
passing a function to `page.evaluate` under `tsx`, and the scripted-sweep
recipe for migrating an app onto the measured tokens (83 `stone-*` refs → 0).
