# Field notes: parsers that return plausible, wrong numbers

Extended detail for the "plausible-wrong" section of the parent skill. All
cases verified against live dealer-inventory scraping, 2026-08-30.

The through-line: **every one of these produced output that passed a glance.**
None threw. None returned empty. Each was caught only by an assertion about
what the numbers had to mean.

---

## Case 1 — fee in a price field, ranked as the best deal

```
Liberty Hyundai · Palisade Hybrid Calligraphy
  msrp   62,675
  price     799        <- the doc fee
  discount 61,876      <- ranked #1 in the territory
```

Koeppel produced the same shape with `175`. The sweep did nothing wrong
mechanically: it read a number from a price field and subtracted.

Gate:

```ts
// A NEW car never sells at half of MSRP. Below that, the "price" is a fee.
const plausible = price != null && msrp != null && price > msrp * 0.5;
const usePrice = msrp == null || plausible ? price : null;
```

Record the rejected row as `price: null` (**not measured**), keeping MSRP,
which is still true. Do not drop the listing.

**Why this ranks worst of all the bugs here:** best-deals lists sort by
discount descending, so the largest fabrication is guaranteed to be the first
thing the user sees. A ranking query is an amplifier for exactly this defect.
21 fabricated deals were sitting at the top of the list.

## Case 2 — two derived numbers disagreeing

Freehold's price ladder carried no dealer-discount row, so the ladder's own
`totalOffMsrp` collapsed onto the **$895 doc fee**:

```
msrp 48,280 · price 48,175        -> msrp - price = +105   (correct)
ladder.totalOffMsrp                = -895                  (the doc fee)
reported                           = -895, pct +0.22       <- signs disagree!
```

105 vehicles at one dealer read "above MSRP" from this single disagreement.
The tell was internal: a **negative discount with a positive percentage**.
Two fields derived from the same pair cannot disagree in sign.

Rule: when a structured source and a simple derivation both yield the same
quantity, **prefer the derivation from the columns you display**, and accept
the richer source only when it corroborates:

```ts
const coherent = raw != null && derived != null && Math.abs(raw - derived) < 1;
const reported = coherent ? raw : derived;
```

A richer parse tier does not outrank arithmetic the user can check by eye.

## Case 3 — uniform output as an association bug

First Dealer.com parser returned, for 24 different VINs:

```
msrp 38,990 · price 39,685 · discount -695   (x24, identical)
```

Assumed `vin` preceded `trackingPricing`; the real payload has pricing
**first**. Every car was paired with the *next* car's prices.

Proof was offset arithmetic, not inspection: 25 pricing blocks, 25 VINs, and
the first pricing block had **no preceding VIN at all**.

> Identical derived values across rows that should differ is an association
> bug until proven otherwise. Uniformity is the signature — a mispairing is
> usually *more* uniform than real data, which is why it reads as clean.

## Case 4 — regex window sized against one sample

```
Towne   162 KB page  -> gap ~1,700 chars   parser works
Ciocca  675 KB page  -> gap ~7,650 chars   parser silently returns 0
```

Window capped at 2,600. The diagnostic that isolated it: a *sibling* parser on
the same page returned **17 ladders while the VIN parser returned 0**. Two
parsers over one document disagreeing about how many vehicles exist localizes
the fault immediately.

When a bounded window separates two anchors, measure the real distance across
the **largest** sample, not the first, and leave headroom below the per-record
spacing (~9,800 here) so the bound still selects the right record.

## Case 5 — case- and encoding-sensitive query params

```
?model=SANTA+FE     ->  0      (our upstream spelling)
?model=Santa+Fe     ->  0      (title case, '+' encoding)
?model=Santa%20Fe   -> 17      <- only working form
<unfiltered>        -> 24
```

Two independent variables — casing *and* space encoding. Probing only one
would have concluded the facet was broken. `URLSearchParams` emits `+`; this
platform needs `%20`, so the query string had to be built by hand with
`encodeURIComponent`.

Identifiers crossing a system boundary get **normalized at the boundary**;
upstream spelling is not a contract.

## Case 6 — empty facet reported as parse failure

`?model=Palisade` → 0 while `?model=Palisade%20Hybrid` → 8. The dealer
genuinely stocks none of the base trim. Flagging that as `parse_failure`
marked a healthy dealer broken.

Scope the failure assertion to the widest thing that must be non-empty:

```ts
// per-facet zero is inventory; zero across EVERY facet is a broken parser
if (parsedAcrossAllModels === 0 && weHoldListingsForThisDealer)
  failure = "parse_failure";
```

## Case 7 — sticky status outliving its cause

`status = 'failing'` was set on parse failure but never cleared on success, and
the sweep skipped non-active dealers. After the parser was fixed the dealer
stayed excluded **forever**, and coverage silently stopped recovering.

- Clear the flag on success in the same write that sets it on failure.
- Provide `--retry-failing` (and always retry an explicitly named target).
- A health flag with a set path and no clear path is a latch, not a status.

---

## Coercion and measurement-contract regression recipe

1. Reproduce the rendered or ranked defect with a missing source value, not only a unit test of the parser. A missing days-to-event field must not become an event today or incur a near-event penalty.
2. Put a type gate at the shared numeric boundary before arithmetic:

```js
function finiteNumber(value) {
  if (typeof value !== 'number' && typeof value !== 'string') return null;
  if (typeof value === 'string' && value.trim() === '') return null;
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}
```

Use this only where numeric strings are permitted; keep exact monetary strings out of floating-point accounting. Currency-formatted strings need an explicit format-aware parser, not a zero fallback.

3. Test rejection of `null`, `undefined`, `''`, whitespace, booleans, arrays, objects, `NaN` and infinities; separately assert preservation of `0`, `'0'` and valid numeric strings. Test consumers too: no invented event labels, no missing-indicator score contribution, and no fabricated priced rows.
4. Follow generic fields such as `change` and `rs` into the producer formula. Rename narrative-context fields to encode the verified contract, for example `change_1d_pct`, `change_30d_pct`, `vix_index_level`, and `fear_greed_index_0_100`. Do not infer the window from a neighboring dataset with the same key.
5. Add context-schema and prompt tests: suppress ambiguous bare keys and unlabeled scaled proxies; require units/windows and forbid comparing daily and trailing-period returns as peers. Regenerate the summary after the fix and inspect the rendered result; changing a prompt does not repair the previously generated artifact.

## Two-driver result-shape divergence (same schema, different client)

PGlite returns `{ rows: [...] }`; `postgres-js` returns the array itself. Code
reading `.rows` typechecks and works locally, then yields **empty** against the
hosted database — presenting as an empty dashboard, i.e. indistinguishable from
a scraper outage.

```ts
function unwrap<T>(res: unknown): T[] {
  const r = (res as { rows?: unknown[] })?.rows ?? res;
  return (Array.isArray(r) ? r : []) as T[];
}
```

Centralize at the single point every raw query passes through. The dual-driver
pattern (WASM Postgres locally, hosted in prod) is genuinely good — identical
SQL dialect, no query rewrites — but result *shape* is not part of that
guarantee.

Related: `.returning()` does not typecheck across a `PGlite | postgres-js`
union type. Insert, then read the id back explicitly.

## `.env.local` values containing `&`

Hosted Postgres URLs end `...&channel_binding=require`. Unquoted, a shell
`. ./.env.local` **backgrounds the assignment** and the variable arrives empty
— then the migration fails for a reason that has nothing to do with the
database. Always `printf 'KEY="%s"\n'`.
