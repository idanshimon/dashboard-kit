# Verifying Graph/Canvas Surfaces (Cytoscape, react-flow, d3)

Graph views fail in ways ordinary DOM surfaces do not: the canvas is opaque to
`querySelector`, layout is asynchronous, and "renders nothing" and "renders
wrong" look identical from a green test suite.

Verified 2026-08-18 on `ledger-insights-ui` (agentic-sdlc), a four-route
Cytoscape/react-flow decision-graph surface reported by the user as *"not very
clear what is going on, what belongs to what."*

---

## 1. The reported defect is almost never the real one — check for DATA first

The complaint was legibility. The actual state: **all three graph routes rendered
an empty canvas**, and the legend never mounted at all because it is gated behind
having graph data.

Root cause was one missing fallback:

```
POST /api/ledger/query  ->  401     (no live DB credentials on a demo machine)
```

`useDecisions()` called the ledger API with **no demo guard**, while the sibling
run-surface hooks (`useRuns`, `useRun`) all had one. Demo mode was enabled and
working — for every surface except this one.

**The generalizable trap: when a feature flag or fallback exists, verify EVERY
consumer honours it, not that the flag is on.** A per-hook fallback is per-hook
by construction; the flag being `1` says nothing about coverage. One `grep` for
the flag symbol answers it:

```bash
grep -rn "isDemoMode\|FEATURE_FLAG" src/lib/hooks/    # which hooks check it?
```

**Corollary — a component gated behind data is invisible, not broken.** Hours can
go into "why doesn't the legend render" when the legend is correct and the data
is absent. Before debugging any conditional UI, prove its precondition:

| Symptom | Check this first |
|---|---|
| New component never appears | Is its data precondition satisfied? |
| Canvas empty, page otherwise fine | Read the network tab / server log for 401/403 |
| Only SOME surfaces empty | Compare their data hooks against a working sibling |

The server log is the cheapest signal here. A repeating `POST /api/... 401` line
is the whole diagnosis and costs one `process(action='poll')`.

---

## 2. Prove the graph has nodes at the DATA layer before screenshotting

A screenshot round-trips through headless Chrome, layout, and a vision model.
Driving the real builders directly is seconds and gives a number instead of a
judgement. Write it as a throwaway test, run it, delete it:

```ts
// __fixcheck.test.ts — deleted after running
const e = demoLedgerEntries();
console.log("ENTRIES:", e.length);
console.log("MAP:",     buildGovernanceNetwork(e).nodes.length);
console.log("LINEAGE:", buildPrecedentLineage(e).nodes.length);
const ids = runIdsFrom(e);
console.log("RUNFLOW:", buildRunFlow(e, ids[0]).nodes.length);
```

```
ENTRIES: 6   MAP: 11 nodes/14 edges   LINEAGE: 2/1   RUNFLOW: 6/5
```

That output settles "is it empty" definitively. Only then is a screenshot worth
paying for — and now it answers a *different* question (does it read well),
rather than duplicating one arithmetic already answered.

Keep graph builders pure and DOM-free precisely so this is possible.

---

## 3. Layout is ASYNCHRONOUS — `cy.fit()` after `.run()` measures stale geometry

The highest-value technical finding, and it survived one failed fix.

Both `fcose` and `dagre` accept `fit: true`, and both still settle
asynchronously **even with `animate: false`**. A synchronous fit immediately
after `.run()` reads positions that are not final:

```ts
// WRONG — measured before the layout settles. Nodes end up clustered against
// one edge with half the canvas empty, and it LOOKS like a styling problem.
cy.layout({ name: "fcose", animate: false, fit: true }).run();
cy.fit(undefined, 48);
```

```ts
// RIGHT — fit when the final positions actually exist.
const layout = cy.layout({ name: "fcose", animate: false, fit: true, padding: 40 });
layout.one("layoutstop", () => {
  cy.fit(undefined, 48);
  if (cy.zoom() > 1.15) cy.zoom(1.15);   // cap: sparse graphs balloon otherwise
  cy.center();                            // fit() does NOT recentre after a capped zoom
});
layout.run();
```

Three details that each cost a cycle:

- **`fit: true` in the layout options is not sufficient** — it runs mid-layout.
  Its presence makes the bug harder to spot, because the code *looks* like it
  already fits.
- **Cap the zoom.** A 2-node graph on a 74vh canvas fits to an absurd
  magnification. `1.15` is a reasonable ceiling.
- **`cy.center()` is required after a capped zoom.** `fit()` alone leaves the
  graph off-centre once you override its zoom level.

**Verification note:** the first attempt at this fix compiled, typechecked, and
passed 208 tests — and the screenshot came back *"❌ NOT fixed. All nodes
clustered in the RIGHT third, entire left ~55% empty."* Layout geometry is not
expressible in a unit test. It must be seen.

### An overlay panel steals canvas that `cy.center()` still counts

Even a correct `layoutstop` fit leaves the graph visually off-centre when a
legend, filter rail, or detail panel floats over the canvas. `cy.center()`
centres on the **full container**, including the strip hidden behind your
overlay, so the graph reads as pushed away from the panel with a dead gap
beside it.

```ts
cy.center();
cy.panBy({ x: -95, y: 0 });   // ≈ half the 186px legend width
```

Sign matters and is easy to invert: an overlay on the **left** requires a
**negative** x pan (shift content left, toward the panel). Getting it backwards
makes the imbalance worse while looking like a plausible fix.

Measured progression across three screenshot passes — worth knowing what "good
enough" looks like, so you stop:

| Pass | Result |
|---|---|
| Sync `cy.fit()` after `.run()` | nodes in the right third, left ~55% empty |
| Fit on `layoutstop` | centre-right, left ~30% empty |
| `+ panBy` gutter compensation | left gap ~5%, right ~0–3%, no clipping |

The residual asymmetry is the force layout's own, not a viewport bug. Stop
tuning there — further nudging trades one imbalance for another.

### The CONTAINER can be measured stale too — `cy.resize()` before `cy.fit()`

A distinct third failure, and the one most likely to be misread as "just a
sparse graph." Symptom: the graph sits **sunk toward the bottom** of its panel
with dead space above, or hugs one side, even with a correct `layoutstop` fit.

Cause: Cytoscape caches the container's dimensions at init. When the canvas sits
below a block that is still laying out — a run-picker, a filter-chip rail, a
header that wraps — the cached height/width is stale, so `fit()` and `center()`
compute against geometry that no longer exists. The layout is right; the
viewport maths is against the wrong rectangle.

```ts
layout.one("layoutstop", () => {
  cy.resize();          // re-read the container BEFORE fitting
  cy.fit(undefined, 48);
  if (cy.zoom() > 1.15) cy.zoom(1.15);
  cy.center();
});
```

Measured on the run-flow route: "sunk to bottom, huge space above" became
**~45% empty above / ~50% below, ~30% left / ~32% right** from that one call.

**Diagnostic tell:** vertical imbalance points at container measurement;
horizontal imbalance points at an overlay panel (previous section). Both can be
present at once, and they have different fixes — do not apply `panBy` to a
vertical sink.

**Order matters and is not obvious.** `cy.zoom(level)` scales about the viewport
origin, so it must come *before* `cy.center()`. `resize → fit → zoom → center`
is the sequence; any other order leaves a residual offset that looks like a
styling bug.

---

## 4. Read the BUILDER for vocabulary, never a design doc or your own memory

Two vocabulary errors in one session, both caught only by grepping the source:

| Assumed (from prose) | Actual (from builder) |
|---|---|
| `same_class`, `governed_by` | `same_slot`, `grounded_in` |
| node kinds: precedent / decision | node kinds: `bundle` ("Rule hub"), `class` ("Ambiguity class") |

Consequence if unchecked: a legend that decodes edge types **which do not exist**
while leaving the real ones unlabelled — the exact defect the legend was built to
fix, shipped inside the fix.

```bash
# The one command that settles it:
grep -o 'kind: "[a-z_]*"' src/lib/graph/build-*.ts | sort -u
```

Also note the selector attribute differs between views: one used
`edge[kind = ...]`, another `edge[relation = ...]`. A shared stylesheet keyed on
the wrong attribute matches **nothing** and fails silently — no error, no style.

---

## 5. `grep -ril <word>` under-reports UI features

Claimed "only one view has a legend" based on `grep -ril legend`. Wrong: the
other two views had legends as **unlabelled `<div>`s** — no class name, no
comment, no matching identifier.

The real defect was worse than the reported one: *three divergent hand-written
legends, none of which decoded a single edge type* — six edge kinds carried
meaning with no key anywhere.

**When grepping for the absence of a UI feature, search for its visual
signature, not its name.** Absolutely-positioned overlay containers, swatch
spans, and the token names an implementation would have to use:

```bash
grep -rn 'absolute left-3 top-3\|inline-block h-2.5' src/app/
```

A legend generated from the same module the stylesheet reads cannot drift; three
hand-written ones will.

---

## 6. Border contrast: compute the ratio, do not eyeball it

Three independent screenshot analyses each flagged "borders blend into the
background." The arithmetic confirms it and gives a target:

```
--border-default #243042  on  --surface #11161D   ≈ 1.4:1
```

Well under the 3:1 minimum for a meaningful UI boundary. The fix is a **separate
token tier**, not a global bump (which would flatten intentional hierarchy):

```css
--border-default: #243042;   /* structural, low-emphasis        — 1.44:1 */
--border-strong:  #5E7490;   /* load-bearing: panels, legends, canvas frames — 4.01:1 */
```

Add the light-theme counterpart in the same edit (`#9CA3AF`), or light mode
inherits a dark-tuned value — the frozen-accent failure documented in the parent
skill's both-themes section.

**Compute the ratio; two eyeballed bumps in a row both landed short.** Measured
against the page background `#0B0F14`:

| Value | Ratio | Review verdict |
|---|---|---|
| `#243042` (default) | 1.44:1 | "blends into the background" |
| `#3A4A61` | 2.19:1 | "helps but still subtle" |
| `#4A5D78` | **2.86:1** | still "SUBTLE, not crisp" — *under 3:1* |
| `#5E7490` | 4.01:1 | distinct, not over-corrected |

`#4A5D78` *felt* like a decisive jump and was still below threshold. Run
`scripts/contrast_ratio.py <hex> <bg-hex>` instead of guessing — it converts a
reviewer's adjective into a pass/fail number and stops the nudge-and-resubmit
loop.

### Passing the contrast bar did NOT close the complaint — width was the variable

An earlier version of this file advised: *"clear the measurable bar, then stop
and let the user call the weight."* **That advice was wrong and is retracted.**
It was written mid-session, at the moment of deferring, and the next round
disproved it.

What actually happened: at `#5E7490` (4.01:1, comfortably past the 3:1 bar) a
**fourth** independent review still answered the acceptability question **NO** —
*"visible but still a thin, low-contrast line — a distinct rectangle only on
close inspection."* Colour had been tuned four times. Line **width** had never
been touched. Tailwind `border` → `border-2` returned **CRISP on all three
surfaces** in one round, with the reviewer stating explicitly it was *not*
over-corrected and did not cage the content.

The predicted cost ("2px frames every canvas in visual noise") simply did not
materialize. It was a rationalization for stopping, not an observation.

Corrected rules:

- **Clearing the measurable bar on one dimension is evidence to look at ANOTHER
  dimension** — not evidence the complaint is now unreasonable. A border has
  colour, width, opacity, and radius; "subtle" describes all four.
- **Mine the reviewer's exact wording for the mechanism.** "Thin" is a width
  report. Independent observers name the cause more precisely than their own
  summary verdict does.
- **Don't hand back a "your call" you haven't diagnosed.** Deferring is
  legitimate when a trade-off is genuinely subjective; it is rationalization
  when you merely haven't found the cause. Ask which one you're doing.
- **Do read the whole sentence, though.** "Not over-corrected", "distinct
  rectangle", "thin and clean" are pass signals. The tell for a real defect is
  the reviewer answering the explicit accept/reject question with NO — which is
  why the verification prompt should always force that binary.

---

## 7. Sparse-but-correct reads as broken

`lineage` renders 2 nodes and 1 edge on a 74vh canvas — structurally correct, and
~70% empty. To an operator, empty means broken.

Either scope the container to the content, or **state the scope in the UI**:
"1 precedent chain in this ledger scope." A caption naming the mechanism converts
apparent failure into an honest fact — the same principle as the parent skill's
empty-state rule.

**Derive the count, never assert it** — and expect the typechecker to correct
your field names, because a "precedent" is usually not a node *kind*:

```ts
// Two rejected drafts, both caught by tsc, not by review:
n.kind === "precedent"   // ✗ no such kind — GraphNodeKind has no overlap
n.isRoot                 // ✗ lives on the Cytoscape element data, not GraphNode

// Correct: derive the property from graph STRUCTURE.
graph.nodes.filter(n => !graph.edges.some(e => e.kind === "reuses" && e.target === n.id)).length
```

A chain root is "a node nothing reuses" — an edge-topology fact, not a stored
flag. Deriving it from the edge set is both correct and immune to the vocabulary
drift in §4. Let `tsc` referee: a hardcoded "3 chains" caption cannot go stale
loudly, but a derived one cannot lie.

Cosmetic tail: `"1 precedent chain(s) in scope"` shipped and a reviewer read it
back. On a surface whose whole job is to look trustworthy, `(s)` reads as an
unfinished placeholder. Pluralise derived counts — `${n === 1 ? "chain" : "chains"}`.

---

## 8. Verifying UI that only exists inside a MODAL

Canvas node detail panels are invisible to a plain screenshot: the page loads,
you capture, and the modal was never opened. A capture of the closed state is
not evidence about the modal's contents — do not report one as if it were.

Cytoscape draws to `<canvas>`, so nodes are **not DOM elements** and
`page.click('.node')` has nothing to match. Three ways in, cheapest first:

1. **A demo/deep-link hook the app already has.** `?demo=focus` on the lineage
   route auto-focused a node ~400ms after mount and opened its panel — no click,
   no coordinate maths, and it worked first try under Playwright. Grep for one
   before building anything: `grep -rn 'location.search\|searchParams' src/app/`.
2. **Click at canvas coordinates** of a node whose position you can compute or
   read off a prior screenshot.
3. **Programmatic selection** via the library's own API in `Runtime.evaluate`
   (`cy.nodes().first().emit('tap')`).

If a hook like (1) does not exist, consider adding one — a query param that
focuses a node is a few lines, is useful for demos, and makes every future
verification pass cheap.

**Report the boundary honestly.** In this session the subagent confirmed the
`data-retention` chip rendered monospace, but its report was truncated before
the "is prose still sans-serif" answer. The correct write-up is *"mono confirmed
on machine values; the sans-prose half is an inference, not an observation"* —
not a clean "verified". The untouched-element argument makes the risk low; it
does not make it observed.

---

## 9. Viewport nudges are calibrated to DATA VOLUME — they regress when it grows

Everything in §3 was tuned against an 11-node graph and verified good. The demo
fixture later grew to **29 nodes / 44 edges**, and the same three nudges became
the defect. Nothing in the code changed; only the data did.

| Nudge | Correct at 11 nodes | Wrong at 29 nodes |
|---|---|---|
| `panBy({x:-95})` legend-gutter shift | graph is narrower than the panel, so the shift centres it | `fit()` already used the full width; the pan pushed right-hand nodes out of frame |
| `h-[70vh]` panel height | panel fits above the fold | panel's bottom edge fell **below the viewport**, so `fit()` was fitting a container the presenter could not see |
| `if (zoom > 1.15) zoom(1.15)` | stops a 2-node graph ballooning | safe here — the `>` guard only ever reduces. Had it been `=`, it would have zoomed a dense graph back IN past the fit |

Fixes, both of which gate the nudge on measured geometry rather than on the
assumption it was tuned for:

```ts
// Only compensate for the overlay when there is actually slack to give.
const bb = cy.elements().renderedBoundingBox();
if (bb.w < cy.width() - 240) cy.panBy({ x: -95, y: 0 });
```

```
/* Anchor the canvas panel to the space that REMAINS below the page chrome,
   not to a vh fraction that silently assumes a chrome height. */
h-[calc(100vh-460px)] min-h-[380px]
```

**The diagnostic that shortcuts all of it: is the panel's bottom border visible
in the screenshot?** If it is not, the container extends past the fold and every
`fit`/`center`/`pan` computation inside it is operating on a rectangle the user
cannot fully see. Two rounds were spent adjusting graph maths before checking
this — the container was the bug both times.

Rules:

- **A fixture swap is a UI change.** Re-run the visual pass when the data grows,
  not only when the code changes. Proving 29 nodes at the data layer (§2) says
  nothing about whether 29 nodes are legible.
- **Any constant tuned by eye carries an implicit data-volume assumption.**
  `-95px`, `70vh`, `1.15` all encode "at roughly the density I was looking at."
  Gate them on a measurement, or re-verify at the new density.
- **Zoom caps must only ever reduce.** Write `if (zoom > CAP) zoom(CAP)`, never
  an unconditional `zoom(CAP)` — on a dense graph `fit()` legitimately chooses a
  zoom below the cap, and re-applying it undoes the fit.
- Same failure shape as the semantic-typography and border-width cases in the
  parent skill: a value tuned against one sample, generalised without recheck.

---

## 10. Async delegation results arrive STALE — check the dispatch timestamp

A screenshot-verification loop driven by background subagents will deliver
completed batches **after** you have already fixed what they were sent to check.
Six such batches landed in this session, every one describing a state that no
longer existed. Acting on them would have re-opened closed defects, and one
report's "border is SUBTLE" would have been re-fixed twice.

Before acting on any delivered batch:

1. **Compare its dispatch time against your commit log.** A report dispatched at
   16:29 is describing pre-16:29 code.
2. **Ask what changed since.** If the fix it demands is already committed, say
   so explicitly and move on — do not silently ignore it either, since a stale
   report can still contain a *complaint you never addressed*.
3. **Mine it for the un-actioned item.** The 16:36 batch was stale on the fit
   defect but carried the border verdict that was still live. Stale on one axis
   ≠ stale on all.

The verification loop is worth it regardless — but treat each result as a
timestamped observation, never as current state.
