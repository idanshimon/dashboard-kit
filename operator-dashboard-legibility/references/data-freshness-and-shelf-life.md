# Data freshness and shelf life on a dashboard

Worked recipes for §5c (freshness qualifies coverage) and §5d (a number needs
its shelf life). Verified 2026-08-30 on a vehicle price tracker (cartrack),
2,512 tracked records across 40 sources.

---

## 1. The two-clocks trap

A pipeline usually has more than one job writing to the same table, and they
carry different payloads. Measured, one hour apart:

| Batch | Rows | With the expensive field |
|---|---|---|
| Inventory pass (11:46–11:51) | 1,081 | **0** |
| Price sweep (05:41–07:52) | 5,472 | 2,625 |

A naive `max(observed_at)` reported **8 minutes ago**. The prices the user
actually reads were **4 hours** old. The dashboard would have been technically
accurate and practically lying.

**Rule:** track the timestamp of the EXPENSIVE field separately and lead with
it. Show the cheap-pass timestamp only when it differs.

```sql
select
  (select max(observed_at) from listing_snapshot)                        as last_snapshot_at,
  (select max(observed_at) from listing_snapshot where price is not null) as last_price_at
```

In the component, suppress the second line when they agree — otherwise it is
the same fact printed twice:

```tsx
{snapRel !== priceRel && <span>Inventory {snapRel}</span>}
```

---

## 2. "N updated since" — group by RUN, not by window

A sweep is bursty: dozens of sources over several minutes. A rolling 24h window
splits one run across two buckets and reports half of it. Detect runs by gap.

```sql
with runs as (
  select observed_at,
         case when observed_at - lag(observed_at) over (order by observed_at)
                   > interval '30 minutes'
              then 1 else 0 end as new_run
    from (select distinct observed_at from listing_snapshot) t
),
grouped as (
  select observed_at, sum(new_run) over (order by observed_at) as run_id
    from runs
),
bounds as (
  select run_id, min(observed_at) started, max(observed_at) ended
    from grouped group by run_id
)
select * from bounds order by run_id desc limit 2;   -- latest + previous
```

**Validate the grouping against real data before trusting it.** On the real
table this correctly returned two runs split at a 4-hour gap:

```
run_id  started              ended                ticks
0       2026-08-30 05:41:18  2026-08-30 07:52:18  5472
1       2026-08-30 11:46:19  2026-08-30 11:51:08  1081
```

`minute` is a reserved word in Postgres — `date_trunc('minute', x)::text minute`
is a syntax error. Alias it something else (`mins`).

### Change counting is free if snapshots are change-only

If the writer only inserts when a value actually differs, a second row for an
entity *is* the change — no diffing:

```sql
select count(*) from (
  select vin from listing_snapshot
   where price is not null
   group by vin having count(*) > 1
) t
```

---

## 3. Shelf life: find the expiry the vendor renders client-side

Retailer sites publish a discount with **no date attached** — one platform
labelled every incentive row generically as `"Offers"`. The manufacturer's own
offers page has real `startDate`/`endDate`, but renders them client-side, so the
served HTML only shows the interpolation:

```
Offer ends in {{ expirationDateCountdown(offerData ...
```

That string is the tell. Grep the served HTML for `{{`/`__NEXT_DATA__`-style
interpolation before concluding the data is absent. Then find the feed from a
loaded page:

```js
performance.getEntriesByType('resource')
  .map(r => r.name)
  .filter(n => /offer|incentive|api/i.test(n))
```

Which surfaced the real endpoint, returning 78 regional programs with dates:

```
/var/hyundai/services/incentiveAws.featuredOfferByZip.service?brand=hyundai&zip=07866
```

### Normalize model/SKU names before joining, or the join silently matches nothing

The offer feed used **both** `"PALISADE HEV"` and `"Palisade Hybrid"` for the
same vehicle; the inventory feed said `"PALISADE Hybrid"`. Naive lowercasing
treats HEV as a separate model and drops half the programs — and a missing
expiry looks identical to "no program exists", so nothing surfaces the bug.

```ts
export function normalizeModel(name: string): string {
  const s = name.trim().toUpperCase().replace(/\s+/g, " ");
  if (/^PALISADE\s*(HEV|HYBRID)$/.test(s)) return "PALISADE HYBRID";
  if (/^SANTA FE\s*(HEV|HYBRID)$/.test(s)) return "SANTA FE HYBRID";
  return s;
}
```

Write a join test that FAILS on any unmatched key rather than trusting it:

```
OK   PALISADE        -> PALISADE        ends 09/08/2026 (8d) cash=3000 apr=3.99
OK   PALISADE Hybrid -> PALISADE HYBRID ends 09/08/2026 (8d) cash=1000 apr=3.99
OK   SANTA FE        -> SANTA FE        ends 09/08/2026 (8d) cash=3000 apr=0
4 matched, 0 unmatched
```

### Lookup, not row-wise join

Offers are per-model/per-region while listings are per-unit. A row-wise SQL join
multiplies 2,512 listings into ~10,000. Load one grouped `Map<model, offer>` and
apply it in the view.

---

## 4. Placement and scoping

- **Expiry goes under the number it qualifies**, inside the same cell — a
  separate column divorces the deadline from the figure and gets scanned past.
- **One shared deadline renders once.** All programs in a region ended the same
  day, so the date is a page banner; rows carry only `8d left` plus their own
  amount. Repeating the date 50 times is noise.
- **Scope headline claims to the filtered set.** A banner reading "0% APR
  available" is false the moment the reader filters to a model financed at
  3.99%. Derive from the models actually on screen and verify across filter
  states:

```
unfiltered      -> 0% APR      (from the model that has it)
?model=PALISADE -> 3.99% APR   (correctly does NOT claim 0%)
?model=SANTA+FE -> 0% APR
```

---

## 5. Verification gotcha

React splits interpolated text with HTML comments, so a rendered
`$3,000 mfr · 8d left` appears in the bytes as:

```html
$3,000 mfr · <!-- -->8<!-- -->d left
```

A regex for `\d+d left` returns **0 matches** against correctly-rendered output.
Inspect raw bytes before reporting a feature as missing.
