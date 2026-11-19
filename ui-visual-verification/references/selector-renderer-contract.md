# A picker must only offer what the renderer can draw

A distinct empty-surface cause, separate from "no data" and from "the fallback
is missing": **the data exists, the selector lists it, and the renderer draws
nothing** — because the two disagree about what an item *is*.

Verified 2026-08-19 on `ledger-insights-ui` (agentic-sdlc). Found by visual
inspection during demo prep; every gate was green throughout.

---

## The failure

A Run Flow view rendered an empty canvas on load while its run picker
confidently displayed `meridian … 5 decisions · 1 flagged`.

Two functions, two definitions of "a run":

```ts
// buildRunOptions — what the PICKER lists
for (const e of entries) {
  if (!e.run_id) continue;              // ANY entry carrying a run_id
  byRun.set(e.run_id, [...]);
}

// buildRunFlow — what the CANVAS draws
entries.filter(e => e.run_id === runId
  && (!e.runtime_kind || e.runtime_kind === "stage_decision"))   // ONLY stage decisions
```

Teaching signals — flags, thumbs, replay requests, class pauses — also carry a
`run_id`. They collected under a `…-teaching` bucket which, being the most
**recent** activity, sorted first under the picker's newest-first default. The
default selection therefore had five entries and zero renderable ones.

Nothing failed. No error, no console warning, no failing test. The picker's
count came from one definition and the canvas from the other.

---

## Why it survives review

- **Both functions are individually correct.** Neither is a bug in isolation;
  the bug lives in the gap between them.
- **The counts look plausible.** "5 decisions" is not obviously wrong — you have
  to know that four of them are teaching signals to see the problem.
- **It only shows up with the right data.** With a fixture where the newest
  activity happens to be a real run, the default lands on something renderable
  and the bug is invisible. It appeared here only after enriching the fixture.
- **An empty canvas reads as a broken view**, not as an empty scope — so the
  instinct is to debug the renderer, which is the half that is behaving.

---

## The rule

**An option that cannot render must not be offerable.** Filter the selector by
the renderer's own predicate, not by a looser one that happens to be convenient:

```ts
// A run is offerable only if it contains what buildRunFlow() actually draws.
for (const [runId, list] of [...byRun]) {
  const renderable = list.some(
    (e) => !e.runtime_kind || e.runtime_kind === "stage_decision",
  );
  if (!renderable) byRun.delete(runId);
}
```

Prefer this over "show an empty state for empty runs." Offering a choice that
leads nowhere teaches the operator the view is unreliable, and it burns the
default slot — which is the one most users never change.

---

## Generalising

Any pair of *"what we list"* and *"what we draw"* is a contract that nothing
enforces. Same shape in:

| Lister | Renderer | Silent failure |
|---|---|---|
| run / session picker | timeline or graph builder | empty canvas, confident count |
| file tree | preview pane | "select a file" on a file you selected |
| tab bar | tab content | blank tab |
| search results | detail view | 404 on your own result |
| filter chips | filtered list | chip shows `(12)`, list shows nothing |

**Diagnostic tell:** the chrome reports a non-zero count while the content area
is empty. That combination is almost always a definition mismatch, not a data
problem — a genuine no-data case usually zeroes *both*.

**Cheapest check:** grep the two functions for their filter predicates and
diff them by eye.

```bash
grep -n "filter(\|if (!e\.\|continue;" src/lib/build-<thing>.ts src/lib/<thing>-options.ts
```

---

## Regression test shape

Test the *contract*, not either function alone. Name it so the next reader
knows what breaks if they delete it:

```ts
it("omits runs that contain no stage decisions (would render an empty canvas)", () => {
  const opts = buildRunOptions([
    e({ run_id: "real-run",      created_at: "2026-08-12T09:00:00Z" }),
    e({ run_id: "teaching-only", created_at: "2026-08-12T11:00:00Z",   // newer — would sort first
        runtime_kind: "decision_flagged", references_entry_id: "x" }),
  ]);
  expect(opts.map(o => o.runId)).toEqual(["real-run"]);
});
```

The assertion that matters is **on the newer, unrenderable item being absent** —
if it merely checked `length === 1` it would pass against a version that dropped
the wrong one.

Pitfall while adding it: match the existing file's fixture-helper name. A test
appended with `entry({...})` into a file whose helper is `e({...})` fails with a
reference error that reads like a logic failure. Read the top of the test file
before appending to it.

---

## Verification-order lesson

The claim *"run 0003 is the default selection, no picker fumbling"* was made
after checking `runIdsFrom()` — the **builder's** sort — and was wrong, because
the picker uses `buildRunOptions()`, which sorts by newest activity across a
wider entry set.

**Verify the function the UI actually calls, not a plausible sibling.** Two
functions with similar names and overlapping outputs are exactly where this
mistake lives. Trace from the component (`grep -n 'buildRun' page.tsx`) rather
than from the library.
