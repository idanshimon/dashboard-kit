# Demo fixtures: generate them FROM the seeder, never hand-copy

**Class of problem.** A demo surface needs richer data than the checked-in
fixture provides, and the live backend is unreachable (no credentials on a
laptop, 401 on every query). The instinct is to hand-write a bigger fixture.
That creates a second copy of the scenario which immediately starts drifting
from the real seeder.

Verified 2026-08-19 (ledger-insights-ui decision-graph surfaces).

## Look for an existing seeder before writing any data

Most mature projects already have one — it just writes to the live backend and
therefore looks unusable offline. Search before authoring:

```bash
find . -name '*seed*' -o -name '*extract_demo*' | grep -v node_modules | grep -v .next
ls experiments/ scripts/
```

Here `scripts/seed_graph_demo.py` already existed, already customer-neutral,
already exercised **every edge type** the graph could draw, and already had a
`--dry-run` flag. Its module docstring explained precisely why the shipped
fixture was inadequate — richer context than any amount of code-reading would
have produced. **Read the seeder's docstring first; it usually states the gap.**

Run the dry mode to inspect the scenario without any credentials:

```bash
python3 scripts/seed_graph_demo.py --dry-run
```

## The technique: swap the writer, don't copy the data

Import the seeder and replace its single write function with a recorder. The
fixture is then *generated from* the seeder, so there is exactly one source of
the scenario.

```python
import seed_graph_demo as seed          # the real seeder

seed.DRY = False                        # let main() run its full scenario
seed.write = _capture                   # record instead of POST
seed.TOKEN = "capture-mode"             # bypass the token guard

seed.main()                             # walks the whole story, zero network
```

Requirements for the recorder that make the output reviewable:

- **Deterministic ids.** `uuid.uuid5(NS, entry["decision"])` with a fixed
  namespace, so re-running produces no diff churn.
- **A fixed clock anchor**, not `datetime.now()`. Monotonic increments from a
  pinned date; otherwise every regeneration rewrites every timestamp and the
  diff is unreadable.
- **Fill the fields the consumer's normalizer expects** (`entry_type`,
  `runtime_kind`, `phi_class`, `bundle_refs`, …) or the fixture typechecks and
  still renders wrong.

This is the same discipline as "derive, don't seed" one level up: prefer a
single generating source over a second hand-maintained artifact.

## Prove the enrichment at the data layer

Before spending a screenshot, assert the builders actually got richer input.
This also tells you *which* surface is still thin:

```
ENTRIES 16
MAP     29 nodes / 44 edges
MAP edge kinds: in_run,of_class,grounded_in,reuses,teaches
LINEAGE 10 nodes / 7 edges
RUNS 3 | RUNFLOW 4 nodes
```

Before: MAP 11/14 with only two edge kinds, LINEAGE 2/1. **A legend that decodes
six edge kinds over a graph using two is a legend describing a graph that does
not exist** — the fixture, not the legend, was the defect.

## Keep both fixtures; name them for their purpose

Do not delete the original slice. Export both and say what each is for:

```ts
/** Graph-shaped scenario: exercises every edge type. */
export function demoLedgerEntries() { return GRAPH_FIXTURE as ...; }

/** The original 6-entry Phase-A slice, kept for the runs surfaces. */
export function demoVitalsLedger() { return VITALS_LEDGER as ...; }
```

## Honesty constraints carry into the fixture

- **Customer-neutral sample product**, invented name, generic domain. The
  seeder already did this ("Meridian"); do not regress it.
- **Narrate as seeded, never as live telemetry** — put that in the code comment
  and the commit message, not only in the demo script, so the next reader
  inherits it.
- The scenario may contain a *plausible* failure (an agent getting a value
  wrong, a human catching it). That is legitimate sample data. It is **not**
  license to fabricate audit history in a live ledger — see "What you may NOT
  derive" in `empty-surface-derive-dont-seed.md`.

## Pitfall: file-descriptor exhaustion mid-session

Long sessions with many tool calls can exhaust the process FD limit; a file
write fails with `[Errno 24] Too many open files` while the shell still works.
`ulimit -n` showed **256**. Raising it in the shell (`ulimit -n 4096`) does not
retroactively fix the calling process, so fall back to writing the file from
within a terminal command for the rest of the session. Not a broken tool — a
resource limit with a working alternative path.
