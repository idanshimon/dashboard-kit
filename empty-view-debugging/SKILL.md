---
name: empty-view-debugging
description: "Use when a UI view renders empty, monotonous, stale, or visually wrong against real data — empty graphs/tables/dashboards, 'this page shows nothing', 'still empty', 'what changed, I can't see it', a newly-created record missing from a list while fetchable by id, light/dark theme leaking into canvas visualizations, unreadable low-contrast text in light theme, or any surface whose data looks thinner or older than the database. Covers deriving relationships from fields the producer actually writes, list endpoints that truncate before sorting, verifying the SCREEN rather than the projection module, three-state rendering, theme-token contrast, and the local-preview-with-live-data screenshot loop."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [debugging, ui, data, verification, empty-state, theming]
    related_skills: [dogfood, agentic-sdlc]
---

# Empty View Debugging

## When to use

A view renders empty, sparse, or visually wrong while the database plainly has
data. Symptoms that route here:

- "the X tab is empty" / "still can't see anything" / "review loop is empty"
- **"what changed, I can't see it"** — a record you just created is missing from
  the list while `GET /<id>` returns it fine (root cause 4)
- a graph with no edges, a list with no rows, a dashboard reading zero
- every row looks identical — nothing to differentiate
- light theme shows black cards, or a canvas visualization ignores the theme
- **"I can't see the highlighted text, the colors are too light"** — contrast or
  tint tokens tuned for the other theme
- a metric reports `0` while the underlying table obviously isn't zero
- **a generated data file (JSON/CSV) has a current timestamp but zero rows** —
  the freshness check passes and nothing flags it (root cause 5)

## Start with the dashboard the user sees

1. When asked to show the working solution, open the deployed product in the user's browser, bring that tab forward, and read back its URL and title. Inspect the visible panel and its active filters. A pilot report, local snapshot or healthy API is supporting evidence, not the dashboard the user asked to see. Before retiring the old path, show a real item from the replacement in that same deployed view; a working dashboard still reading the old producer does not validate the replacement.
2. Replay the page's actual request with the same window and limit. Count only records the panel can display, using the same timestamp, type and content predicates. Compare the selected window with a wider one and report the newest eligible item's time separately from the last successful poll. Diagnose a blank map separately from a zero feed count; either can fail while the other works.
3. If recent eligible rows are missing, compare upstream input → accepted records → local export → served API/static fallback → rendered rows. For RSS/Atom, compare `curl --compressed` with the production parser on the same captured bytes. Honor `Content-Encoding` before decoding text and bound the decompressed size; HTTP 200 with zero parsed items can be a compressed response, not an empty feed. Count items by original publication time. With sending disabled, replay the same payload twice: first with empty temporary state, then with a copy of the producer's seen-state. Compare eligible IDs, not just totals. An ID suppressed only on the second pass was marked seen, not necessarily delivered; never clear live history to demonstrate a fix. Trace one recent applicable item by URL or ID before blaming the source or filter. Distinguish rate-limited, unavailable, reachable but quiet, filtered, and not checked. A broken static publish does not explain an equally old local export.

## Common root causes

Nearly every empty-view report is one of these. Diagnose before editing.

Note the fourth is the *stale* rather than *empty* variant — a page full of
real-looking but outdated rows. It reads as healthy, so it survives far longer
than a blank screen. The fifth is upstream of the view entirely: the generated
data file is empty while its freshness label is current, which passes every
staleness check you would normally run. The sixth is the inverse of all of them:
the view, query and data are all correct, and the surface legitimately no-ops.

### 1. The view filters on a field the producer never writes

**Count field population against real data before theorizing.** Pull the actual
rows and tally which columns are non-null. A representative real-world result:

| Field | Populated |
|---|---|
| `precedent_id` / `precedent_refs` | **0 / 229** |
| `loop_id` | **0 / 229** |
| `runtime_kind` | **null on all 229** |
| `decision_kind` | one value ×229 |
| `slot_value_hash` | **229 / 229** |
| `autonomy_ref` | **216 / 229** |

Optional provenance columns are written only when a specific code path fires.
Production data is overwhelmingly the *default* case. A view keyed to the rare
enum value ("only count it if `kind === 'swap'`") renders empty forever.

**Derive the relationship from the field that IS populated**, and keep the
explicit field as the preferred source:

```ts
// Explicit edges win when the producer writes them.
if (explicitEdges.length === 0) {
  // Derive: identical slot_value_hash across runs IS reuse.
  // Earliest human-authored entry is the precedent; every LATER
  // agent entry in that bucket reuses it.
  for (const group of buckets.values()) {
    const humans = group.filter(isHuman).sort(byTime);
    if (!humans.length) continue;
    const precedent = humans[0];
    for (const e of group) {
      if (e.id === precedent.id || !isAgent(e)) continue;
      if (at(e) < at(precedent)) continue;   // ordering is load-bearing
      edges.push({ child: e.id, parent: precedent.id });
    }
  }
}
```

Time-ordering matters: an agent decision that predates the human ruling reused
nothing. Getting this wrong invents relationships that don't exist.

Encoded strings are data too. A ref like
`autonomy/invariant/phi-classification/gate:phi-auth-hard-lock` carries
family / scope / class / outcome / rule — parse it rather than declaring the
view unsupported.

**Never derive what genuinely isn't there.** If no human has ever flagged a
record, there are no flags. Synthesizing one into an audit or governance
surface is the worst possible failure — it fabricates a record that a human
will later be held to. The honest fill is to *use the app*: perform the real
action so a real entry, with a real actor and timestamp, exists.

### 2. You fixed the wrong module

The expensive one. Codebases routinely carry two similarly-named projections:

- `lib/lineage.ts` → `buildLineageIndex()` → powers table badges
- `lib/graph/build-lineage.ts` → `buildPrecedentLineage()` → powers the page

Patching the first, verifying it in isolation against real data, and reporting
"fixed" is a false claim if the user's screen imports the second.

**Rule: grep the route for what it actually imports before claiming a fix.**

```
search_files pattern="buildX|useY|projectZ" path=src/app/<route>/page.tsx
```

Verifying a projection module proves the projection, not the page. The
acceptance artifact is a screenshot of the route, not a passing unit test.

### 3. `return null` on empty renders as broken

```ts
if (items.length === 0) return null;   // ← indistinguishable from a crash
```

During an in-flight query this renders nothing — visually identical to the
emptiness you were hired to fix. Always three states:

1. **loading** → skeleton, never blank
2. **empty** → name what's missing and when it will appear
3. **populated** → content

Fix the *copy* too. An empty state naming the wrong subsystem ("No review loops
yet") when a different mechanism is at play is misinformation. Say which thing
hasn't run and why: *"No repo has been graduated past Tier C, so no loop has
executed."*

### 4. The list endpoint truncates BEFORE it sorts

First distinguish transport loss from rendering loss: if the LIST API already
contains the missing record, inspect frontend allowlists/static group arrays.
Curated card groups must have a fallback for unassigned records. Reconcile every
returned record with a rendered row and derive summary counts from the same set;
adding only the current missing slug leaves the next addition broken.

The view isn't empty — it's **stale**, which is harder to spot because a page of
real-looking rows reads as healthy. New records are simply unreachable.

Classic cause: a store that applies a row cap before any ordering.

```sql
SELECT TOP 50 * FROM c WHERE ...   -- no ORDER BY
```

then sorting client-side. **Cosmos (and `LIMIT` without `ORDER BY` generally)
applies the cap first**, so the store returns an arbitrary N — in practice the
oldest — and the in-memory sort can only reorder that arbitrary slice. Once the
container holds more than N rows, every newer row falls off permanently. The
docstring claimed `ORDER BY updated_at DESC` the whole time; a previous commit had
removed the ORDER BY (cross-partition ORDER BY needs a composite index) and left
the cap in place.

**One-shot diagnosis — compare the same query at two limits:**

```bash
curl -s "$API/items"           # 50 rows, newest is weeks old
curl -s "$API/items?limit=200" # 68 rows, INCLUDES today's record
curl -s "$API/items/<new-id>"  # 200 OK — fetchable by id, absent from the list
```

Fetchable by id **+** absent from the list **+** more rows at a higher limit =
truncation before sort. Nothing else produces that signature.

**Fix:** over-fetch a bounded window, sort, *then* trim.

```python
fetch_cap = max(limit, min(_SCAN_CAP, limit * 10))   # bounded, not unbounded
query = f"SELECT TOP {fetch_cap} * FROM c WHERE {where}"
...
out.sort(key=lambda r: r.get("updated_at") or "", reverse=True)
out = out[:limit]          # trim AFTER sorting
```

Keep the window capped by a module constant so it can't degrade into a full scan
as the table grows.

**Related tell:** a "needs attention / stalled items" panel showing everything
stuck for 30-45 days is usually not a real backlog — it's this staleness showing
through from the same query.

**Generalizes to any paginate-then-sort-in-memory path.** Either sort in the
store, or fetch a superset wide enough that the sort is meaningful.

### 5. The generated data file is EMPTY but its freshness label is CURRENT

The upstream variant: the view is fine, the renderer is fine — the JSON/CSV/
parquet feeding it has a perfectly current timestamp and **no rows**.

This defeats the standard staleness check. Everyone verifies "is this data
fresh?" by comparing a `week_of` / `generated_at` / `as_of` field against today.
That check **passes**, so nothing flags it, and a downstream consumer renders a
confident *"quiet week, nothing scheduled"* from a file with zero events in it.

Real case (2026-08-30): a weekly catalyst file carried a current `week_of` while
every category counted zero.

```python
week_of: 2026-08-31        # ← current. Freshness check passes.
by_cat:  {'macro': 0, 'fed': 0, 'earnings': 0, 'geopolitical': 0, 'ipo': 0}
hottest: None
```

Root cause was a scheduled job whose guard **exits 0 when it skips** (it refuses
to run against a dirty working tree), so the scheduler logged `ok` while the
producers never ran. The label was written by an earlier successful run; the
content never arrived.

**Gate on source coverage and eligible content, not the generation timestamp.** For a contract that requires at least one row (such as a populated weekly calendar), assert the count below. For an incident feed, zero can be legitimate: if coverage is stale or unknown, report unavailable rather than quiet; do not enforce a nonzero count or invent events.

```python
d = json.load(open(path))
assert d['summary']['total_events'] > 0, 'file is EMPTY — re-run the producer'
```

Corroborate before re-running: check a sibling artifact from the same job. Here a
companion file was frozen seven weeks stale, which confirmed "the job skipped"
over "the world was genuinely quiet."

**Generalises:** for any generated artifact, a fresh-looking *label* and non-empty
*content* are independent properties. A job that no-ops cleanly updates neither,
but a job that partially ran can update one and not the other. Assert the property
your consumer actually depends on. Same discipline as
`pipeline-run-failure-triage` mode 3 (status metadata drifting from artifacts) —
applied to the data file rather than the ledger.

**Corollary — confirm the key you are reading exists.** Reading a top-level
`events` key that the schema never had returns nothing and is
*indistinguishable* from a genuinely empty file. Before concluding "no data",
print the actual top-level keys:

```python
print({k: (f'list[{len(v)}]' if isinstance(v, list) else type(v).__name__)
       for k, v in d.items()})
```

In that same case the events lived under `categories`, keyed by category — the
first read said "0 events" purely because the key was wrong.

### 6. The action fires, the code is RIGHT, and nothing visibly happens

The inverse of every case above: no bug in the view, no bug in the query, no
stale data. The user clicks the primary button and the surface reports a
legitimate no-op — so it reads as broken while behaving exactly as written.

Real case (2026-09-10): a clinical demo's "deteriorate & evaluate" button
reported `SKIPPED` for nearly every subject. Three defects, discovered in
layers, and **only the third made it usable**:

1. **The injected value was ABSOLUTE, not relative.** Hardcoded `lactate = 4.6`.
   Any subject already past 4.6 got an *improvement* written on click — observed
   live at 4.66 → 4.6, score moved 0.0. Fix: derive every target from the
   record's own current value, clamped so it can only move in the worse
   direction.
2. **The pre-selected row could never satisfy the rule.** The rule fired on an
   upward band crossing; the top band has nothing above it. A severity-sorted
   list puts exactly that record in row 1, under the primary button.
3. 🔴 **The change moved ONE input of a WEIGHTED COMPOSITE.** Making it relative
   was necessary and *not sufficient*. That input owned **0.30** of the score, so
   turning it to 11 added ~15 points — a record starting at 11.6 could not reach
   the 40 threshold however extreme that single number got. The rule was right to
   decline every time.

**The generalisable lesson: when an injected change fails to trip a threshold on
a weighted composite, suspect the injection's SHAPE before its MAGNITUDE.**
Maxing one input cannot clear a bar that input owns a fraction of. Model the
correlated real-world scenario the score was designed to detect — in that domain,
one marker rises *because* another falls, so moving them together is both more
honest and what actually crosses the threshold. Result went from mostly-skipping
to **24/24 records crossing**.

**Two verification habits this forces:**

- **Probe the WHOLE population, not one record.** A single-record test passed at
  every stage while most of the cohort still no-opped. A cohort-wide assertion
  ("every eligible record must cross") is what catches defect 3 on the first
  pass — and it belongs in the test suite, not a scratch script.
- **When a test asserts the literal that caused the bug, fix the assertion to
  test the PROPERTY.** One test asserted `toBe(4.6)` — the exact value that broke
  the surface. It became `toBeGreaterThan(before)`. Changing a test to match a
  fix needs that justification stated in the diff, or it reads as making the
  suite green by agreeing with it.

**Say the constraint BEFORE the click, not after.** Where a no-op is legitimate
(case 2 above — a record that genuinely cannot cross), the fix is not to hide it
but to disable/de-emphasise the control and explain inline *before* the user
acts. Narrating a suppression afterwards is too late when someone is watching a
demo. A surface that explains why it declined is a better story than one that
pretends the case doesn't exist.

## Canvas visualizations and theming

Cytoscape, react-flow, D3-on-canvas and friends style to `<canvas>` and
**cannot resolve CSS custom properties**. Hard-coded hex freezes one palette, so
switching themes leaves black cards on a white page.

Resolve tokens off the live DOM and re-read on theme change:

```ts
export function useCanvasTheme(): CanvasTheme {
  const [theme, setTheme] = useState(FALLBACK);   // SSR-safe default
  useEffect(() => {
    setTheme(readCanvasTheme());                  // getComputedStyle(documentElement)
    const o = new MutationObserver(() => setTheme(readCanvasTheme()));
    o.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["class", "style", "data-theme"],
    });
    return () => o.disconnect();
  }, []);
  return theme;
}
```

Then convert the frozen constant to a function of the theme:

```ts
const cyStyle = (t: CanvasTheme) => ([ { selector: "node",
  style: { "background-color": t.elevated, color: t.text } } ]);
// ...
style: cyStyle(theme),
}, [elements, theme]);   // ← theme MUST be in deps or it never repaints
```

Also check the theme block itself. A `.light` (or `.dark`) override that only
flips *surface* tokens leaves accent colors tuned for the other mode —
`#0EA5E9` on `#FFF` is ~2.9:1, a WCAG failure. Ship a full darkened/lightened
accent ramp plus an `--on-primary` foreground that flips with it.

### Hardcoded alpha and dead `dark:` variants

Two failures survive a *correct* accent ramp, and both are invisible from the
dark theme you develop in:

**1. Hardcoded alpha in markup.** `bg-[var(--success)]/10` bakes a dark-theme
assumption into the call site. Light theme correctly darkens the accent, and a
dark colour at 10% alpha on white is almost no fill — highlighted rows vanish.
**Darkened accents need MORE alpha, not less**; the alpha must move opposite to
the hue. Put it in a token (`--tint-weak/--tint/--tint-strong`, e.g. 8/12/16% dark
→ 12/18/24% light) and consume it via
`color-mix(in srgb, var(--success) var(--tint), transparent)`.

**2. `dark:` variants that never fire.** If the app themes with `next-themes`
`attribute="class"`, it toggles a **`.light`** class and the CSS-variable
indirection does the work — so in `text-green-500 dark:text-green-300` only the
failing 500 mid-tone ever renders. Check the mechanism before trusting the prefix.

**No Tailwind mid-tone stop passes AA on white** — `green-500` is 2.28:1,
`blue-500` 3.68:1, `indigo-500` 4.47:1. Compute the ratio; don't judge by eye.

Sweep for both, since the reported component is never the only one:

```bash
grep -rn "var(--\(success\|danger\|warning\|primary\))\]/" src/ --include="*.tsx"
grep -rn "dark:text-\(blue\|purple\|green\|red\|amber\|indigo\)-[0-9]00" src/ --include="*.tsx"
```

While fixing contrast, add redundant encoding — a 2px inset rail, icon, or prefix
character. Colour alone fails red/green colour-blind readers at any ratio.

Detail, measured ratios, and the token set: `references/theme-token-contrast-failures.md`.

Verify mechanically, not by eye:

```
search_files pattern="#[0-9A-Fa-f]{6}" path=src/app/<graph-routes>   # expect 0
grep -o '\.light{[^}]*}' .next/static/chunks/*.css                   # ramp present?
```

## Identify records the way a human remembers them

A raw UUID in a picker is useless to an operator. Label records by what a person
recalls — recency, owner, size, subject — and keep the id searchable:

```
"2d ago · cardiology · 5 decisions · phi-classification — 7282…"
```

Support AND-term search across the human fields **and** the full id, so a UUID
pasted from a log still resolves.

For an intentionally excluded feed, verify the release policy before interpreting a 404 as an outage or zero records. Count page-initiated attempts in a fresh signed-out browser and abort private reads before transmission. Substitute only the repaired consumer script in that browser to verify the attempt disappears while neighboring public panels still work; report this as preview evidence, not a deployment.

## The verification loop

The trap: telling the user "wait for the deploy" while they stare at a stale
revision. Prove it locally against real data *before* claiming anything.

1. Build locally.
2. Stage standalone assets. For a Next.js monorepo the server lands at
   `.next/standalone/server.js`; copy `.next/static` →
   `.next/standalone/.next/` and `public/` → `.next/standalone/`.
3. Run it with **live** backend credentials (read the deployed secret) so real
   data hits the render path.
4. Headless screenshot:
   `--headless --disable-gpu --no-sandbox --window-size=1600,1400
   --virtual-time-budget=25000 --screenshot=/tmp/x.png <url>`
5. `vision_analyze` the image. **Then** deploy and screenshot the public URL.

Notes:

- `browser_navigate` may refuse loopback URLs ("targets a private or internal
  address") — use headless Chrome + `vision_analyze` for local verification.
- Deploy by **digest**, not tag; tag reuse won't repull. Confirm the new
  revision is sole-active at 100% traffic before screenshotting.
- A `200` from `curl` proves routing, not rendering. Screenshot or query the
  DOM.

## Pitfalls

- **Claiming "fixed" from a passing unit test on a projection.** The user is
  looking at a screen. Verify the screen.
- **Assuming deploy lag.** Check the active revision before attributing an
  empty page to propagation.
- **Deriving a value that would be an audit record.** Flags, approvals, and
  sign-offs must come from real actions.
- **Forgetting the theme in the effect deps** — the canvas silently keeps the
  first palette forever.
- **Bulk-editing source with shell heredocs.** Parser limits can block them
  mid-run; write a small script file, run it, delete it, and verify by grep +
  typecheck. Tell the user when edits were made by script rather than by hand.
- **Reporting work as visible without checking the surface the user looks at.**
  After creating a record via the API, confirm it appears in the LIST the user
  reads — not just that the write returned 200 and the record is fetchable by id.
  Real case: an entire end-to-end run was driven, verified via `GET /api/runs/<id>`,
  and reported as done; the user replied *"what changed i cant see ?"* because the
  list endpoint truncated before sorting (root cause 4) and the run was never on
  screen. A `200` on the write and a direct-fetch read both passed while the
  deliverable was invisible. The user's screenshot is the acceptance artifact.
- **Developing in one theme only.** Contrast and token bugs are invisible from
  whichever theme you have open. Toggle before calling visual work done.

## Demo/sample modes must exercise the real backend

A "demo mode" that short-circuits to canned fixtures cannot demonstrate the
product. If the pipeline's claim is "every decision hits a gate and lands in the
ledger," a demo that replays localStorage proves the opposite. Treat demo as a
**data posture** — curated synthetic inputs, real execution:

- Sample inputs go through the real submit path: real stages, gates, writes.
- Fixture replay survives only as an offline fallback in the `catch`, and
  labels itself as a recording, never as live telemetry.
- Don't disable the manual-input path in demo (`disabled={... || demo}` is how
  "the submit button is permanently greyed out" bugs are born).
- Reads hit the real store; seeded history merges as depth with live winning on
  id collision, and a read failure surfaces rather than silently rendering seed
  rows as current.

Also: `NEXT_PUBLIC_*`-style flags are **inlined at build time**. Setting them in
runtime env cannot change an already-built bundle — fix the build arg.

## Worked examples

`references/four-empty-surfaces-one-ledger-2026-07.md` — four empty operator
surfaces traced to one ledger: the field-population survey that unlocked the
diagnosis, the wrong-module mistake in full, the light-theme token diff, the
demo-posture correction, and the "is Clear demo safe?" audit (answered by
reading the function, not from memory).

`references/theme-token-contrast-failures.md` — the light-theme contrast class in
full: hardcoded alpha baking in a dark-theme assumption, `dark:` variants that
never fire under `next-themes attribute="class"`, measured WCAG ratios for every
Tailwind mid-tone stop on white (none pass), the `--tint` / `--code-*` token set
that fixes it in one place, redundant encoding via an inset rail, and the sweep
commands.
