# Empty operator surface: derive from real fields, don't seed fakes

> **Before any of this: confirm the surface is ACTUALLY empty.** A naive
> `curl | sed` text extraction returns an empty string from a fully-rendered
> Next.js page, because script-stripping with line-oriented `sed` eats the whole
> single-line RSC payload. Check `size_download` first — 201 KB is not an empty
> page. See `references/verify-the-harness-before-reporting-empty.md`. Telling
> the user their working app is broken costs more than the bug you were hunting.

**Class of problem.** A dashboard tab renders empty and the instinct is "the data
is missing, let's seed some." Usually wrong. The relationships are almost always
ALREADY in the rows — the view is just querying a field nobody populates.

When offered the choice between deriving and seeding, the right answer is
usually **both, in that order**: derive everything derivable (safe, zero writes,
fixes existing data retroactively), then generate only the genuinely-missing
signals through the REAL app path rather than writing synthetic history.

## Step 0 — profile the actual data before touching any UI code

Do NOT reason from the TypeScript interface; it lies about what live rows carry.
Pull the real payload and count field population.

```bash
TOK=$(az containerapp secret show -n <ui-app> -g <rg> \
      --secret-name <token-secret> --query value -o tsv)
curl -s -X POST "$BACKEND/tools/<query.endpoint>" \
  -H "authorization: Bearer $TOK" -H 'content-type: application/json' \
  -d '{"limit":300}' -o /tmp/data.json
wc -c /tmp/data.json
```

Confirm the endpoint name from the proxy route source (e.g.
`src/app/api/<x>/route.ts`) rather than guessing — a dot-vs-underscore
difference (`ledger.query` vs `ledger_query`) is a silent 404.

Then write a throwaway `/tmp/analyze.py` and run it with `python3`. Do **not**
use a `python3 - <<'PY'` heredoc; the command parser blocks that payload shape.
Count `collections.Counter(e.get(field) or '(none)')` for every field the empty
view depends on.

### The profile that explained four "bugs" at once (229 live rows)

| Field | Population | Consequence |
|---|---|---|
| `precedent_id` / `precedent_refs` | **0 / 229** | Lineage view empty |
| `loop_id` | **0 / 229** | Review-loop view empty |
| `runtime_kind` | **null × 229** | No flags/pauses anywhere; attention queue never fires |
| `decision_kind` | `accept` × 229 | Lineage's precedent test never true |
| `status` | `suggest` × 229 | — |
| `slot_value_hash` | **229 / 229** | ← the real signal |
| `autonomy_ref` | **216 / 229** | ← the real signal |

Four separate "the UI is broken" reports, one root cause: **every view was
keyed on a field that is never written, while two fully-populated fields carried
the same information.**

## Derivation win #1 — a human "accept" IS a ruling

The lineage index marked a value-bucket precedent-bearing only when some entry
had `decision_kind === "swap"` (an explicit override). Real ledgers are
overwhelmingly `accept` — a human read the recommendation and signed off. So
zero taught buckets → empty page forever.

Fix:

- Add `isHumanAuthored()` — human by `confidence_source` **or** `actor.kind`,
  regardless of swap-vs-accept.
- Require **time ordering**: an agent decision only counts as reuse if it lands
  at or after the first human ruling in that bucket. An agent decision that
  predates every human ruling reused nothing.

Result on the untouched live ledger: 18 buckets → **7 precedent-bearing, 65
taught / 93 reused, 41% autonomy earned.** Zero writes. That percentage was the
product's central claim and it was invisible because of one `=== "swap"`.

## Derivation win #2 — read the field that exists

The durable review-loop store genuinely returned `{"items":[],"count":0}` — that
mechanism had truly never run, and faking it was not an option. But 216 rows
carried `autonomy_ref`, a structured path:

```
autonomy/mode/bootstrap/scope-resolution/autopilot:autopilot-mode
autonomy/invariant/phi-classification/gate:phi-auth-hard-lock
└ family ┘└ scope ┘└─ ambiguity class ─┘└ outcome ┘└─ rule id ─┘
```

Ten distinct rules across `invariant` (hard locks) and `mode` families. Parsing
that answers exactly the question the page exists to answer — where is the agent
trusted alone, where is it stopped, and by which rule — rendered as plain
language: *"Hard lock. `phi-classification` can never be auto-resolved — a human
must rule on it every time. Enforced 37 times."*

Write the parser tolerant of unknown shapes (`family: "other"`), and test the
degradation path, not just the happy one.

## The other root cause: the fetch never succeeded (partial demo/offline fallback)

Everything above assumes the rows arrived and the *field* was empty. Check the
cheaper cause first: **the request failed and the view has no fallback, while its
siblings do.** The tell is in the dev-server log, not the component.

Verified 2026-08-18 (ledger-insights-ui). Three decision-graph routes rendered
empty-state text, so the legend component — gated behind having graph data —
never mounted at all. A whole visual redesign was verified as "builds clean, 200
OK, 208 tests green" against three blank canvases.

The log said it in one line, repeated:

```
POST /api/ledger/query 401 in 563ms
```

`NEXT_PUBLIC_DEMO_MODE=1` *was* set. The demo layer covered the **runs**
surfaces (`listRuns`, `getRun`, the stream) and the ledger query had simply never
been wired into it — so on any machine without live backend credentials, those
three routes were structurally incapable of showing anything.

**Diagnostic order for an empty surface:**

1. **Read the dev-server request log before reading component code.** A `401`,
   `403`, or `404` on the data endpoint ends the investigation immediately.
2. **Grep for the feature flag's guards and list which call sites have one.** A
   demo/offline/fixture mode is almost never applied uniformly; the surfaces
   added *after* it was introduced are the ones that silently lack it. `grep -rn
   "isDemoMode()" src/` and compare against the hooks the empty views call.
3. Only then profile field population (Step 0 above).

**Fixing it honestly:**

- Fall back to a **real fixture** the rest of the demo path already replays, not
  to synthetic filler. Same rule as "what you may NOT derive" — a governance
  surface must not invent history.
- **Fall back only on genuine failure or a genuinely empty result**, never
  unconditionally, or the fixture masks a live backend regression:
  ```ts
  try {
    res = await api.query(args);
    if (isDemoMode() && (res.entries ?? []).length === 0) res = { ...res, entries: fixture() };
  } catch (err) {
    if (!isDemoMode()) throw err;      // real failure stays loud in production
    res = { entries: fixture() } as typeof res;
  }
  ```
- **Keep fixture knowledge inside the demo module**, exported as one function.
  The demo subsystem usually documents its own rip-out procedure; importing a
  fixture array directly into a hook defeats it.

**Prove the fix at the data layer, without a browser.** Faster and more precise
than a screenshot, and it tells you *which* surface is still thin:

```ts
// throwaway test — delete after reading
const e = demoLedgerEntries();
console.log("MAP", buildGovernanceNetwork(e).nodes.length);
console.log("LINEAGE", buildPrecedentLineage(e).nodes.length);
console.log("RUNFLOW", buildRunFlow(e, runIdsFrom(e)[0]).nodes.length);
// -> MAP 11, LINEAGE 2, RUNFLOW 6
```

That output is also the honest caveat to report: `LINEAGE 2` renders correctly
and still **looks** broken on a 74vh canvas. Structurally-correct-but-sparse is a
real finding — either enrich the fixture or state the scope in the UI, but do not
report it as verified-good because the builder returned non-zero.

## A design doc's vocabulary is NOT the code's vocabulary

The same "read the producer, not the description" discipline, applied to naming.
When you implement from an audit, findings doc, or someone else's teardown, the
prose names things in *its* terms. A shared module written from those names — a
legend, a style map, a filter list — decodes categories that do not exist while
leaving the real ones unlabelled. It compiles, it renders, it is wrong.

Verified 2026-08-18 (ledger-insights-ui), invented **twice** in one session:

| Written from prose | Actually emitted by the builder |
|---|---|
| `same_class`, `governed_by` | `same_slot`, `grounded_in` |
| nodes `precedent`, `decision` | map emits `bundle` ("Rule hub"), `class` ("Ambiguity class") |

Both caught only by grepping the builders — precisely the drift a generated
legend exists to prevent.

```bash
# what kinds does the producer actually emit?
grep -rn 'kind:' src/lib/graph/build-*.ts | grep -o 'kind: "[a-z_]*"' | sort -u

# and what does the renderer select on? (they can differ)
grep -n 'selector:' src/lib/graph/cy-*.ts
```

That second command matters on its own: one view's stylesheet selected on
`edge[relation = "..."]` while the new shared module emitted `edge[kind = "..."]`.
Both are valid selectors, neither errors, and the rules simply never match.
**A selector that matches nothing is silent** — confirm the attribute name, not
just the value.

- **Enumerate the producer's outputs before writing any consumer that maps over
  them.** One grep replaces a class of invisible defect.
- **Key style/legend maps on a union type** (`Record<Kind, Style>`), so a renamed
  or invented kind fails type-check instead of rendering a blank row. Narrowing
  the union is what surfaced both mistakes here.
- **When doc and code disagree, the code wins and the doc is stale** — report the
  correction, or the next reader inherits it.

## What you may NOT derive

If the field is null everywhere, the event never happened. **Do not invent it.**
Fabricating a teaching signal, a flag, or a pause in a governance/audit ledger is
fabricating an audit record — the worst possible lie in that class of product.

The honest path for a genuinely-missing signal is to *use the app*: click the
Flag button on one real decision, pause one class. That produces a real entry
with a real actor and a real timestamp, and everything downstream populates
truthfully. Offer this to the user rather than seeding — and note that it writes
to production, so it needs their approval.

## Empty states must name the mechanism, not imply breakage

"No review loops yet" reads like a broken feature. Replace with which mechanism
has not run and why:

> "This tracks a different mechanism from the autonomy rules above… No repo has
> been graduated past Tier C (advisory), so no loop has executed."

## Pitfalls

- **The interface is not the schema.** A field can exist in live JSON and not on
  the TS type (`resolution_text` → `tsc` error). Use a typed field or widen the
  type deliberately; don't cast the problem away.
- **Deriving changes counts everywhere.** After collapsing or grouping, any
  "N more" affordance must sum `count ?? 1`, not `items.length`, or it lies.
- **Fix tests that encoded the old wrong behaviour.** Correcting the derivation
  broke a cap test (12 identical items now collapse to 1) and an ordering test
  (two same-key items now merge). Those tests were asserting the bug — rewrite
  the fixtures with distinct keys; never weaken the code to keep them green.
- **Inject `now`.** Any derived human-readable relative time ("oldest 3d ago")
  must take an injected clock or it is untestable and flaky against machine skew.
