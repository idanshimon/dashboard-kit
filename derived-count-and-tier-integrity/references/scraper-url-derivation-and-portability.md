# Scraper URL derivation, facet encoding, and DB-driver portability

Field notes from a multi-platform inventory scraper (40 sources, 3 site
platforms) and its move from an embedded local Postgres to a hosted one.
Everything here was verified against live responses, not inferred.

---

## 1. A 404 across most sources means ONE wrong assumption, not many blocks

Symptom: 36 of 40 sources "blocked or missing". Cause: the URL path was
hardcoded to one platform's convention. The sources on other platforms were
answering fine — they were being asked for a page that does not exist on them.

**Derive the platform from the record you already hold.** A per-record detail
URL fingerprints the platform:

| Detail-URL shape | Platform | Inventory path |
|---|---|---|
| `/catcher.esl?vehicleId=…` | Dealer.com (DDC) | `/new-inventory/index.htm` |
| `/viewdetails/new/<id>` | Team Velocity | `/inventory/new/<make>?instock=true` |
| `/auto/…`, `/new-<City>-<Year>-…` | other | not yet mapped |

Pattern: build a **candidate list** ordered by the implied platform and try
each until one responds. That makes a new platform a one-line addition rather
than a rewrite, and it self-heals when a fingerprint is ambiguous.

```ts
function inventoryUrls(detailUrl: string, page: number, facet?: string) {
  const u = new URL(detailUrl);
  const base = `${u.protocol}//${u.host}`;
  const ddc = `${base}/new-inventory/index.htm?...`;
  const tv  = `${base}/inventory/new/hyundai?instock=true&...`;
  return u.pathname.includes("catcher.esl") ? [ddc, tv] : [tv, ddc];
}
```

Census first: group your records by detail-URL shape and count. Knowing "21 of
40 are platform X" tells you which adapter buys the most coverage.

---

## 2. Facet parameters are case- and encoding-sensitive

Same page, same model, four spellings — only one works:

```
?model=SANTA+FE       ->  0 vehicles
?model=Santa+Fe       ->  0 vehicles
?model=Santa%20Fe     -> 17 vehicles   <- correct
<unfiltered>          -> 24 vehicles
```

Two independent failures:

1. **Casing.** Upstream API values were uppercase (`SANTA FE`); the site's facet
   wants title case. Normalize when crossing systems — never assume one
   system's spelling is another's.
2. **Space encoding.** `URLSearchParams` serializes a space as `+`; this facet
   requires `%20`. When a platform needs `%20`, build the query by hand with
   `encodeURIComponent` rather than reaching for `URLSearchParams`.

Probe before coding the adapter: fetch each spelling, count records, pick the
winner. Three minutes of curl beats an afternoon of "the site is blocking us".

**Filter server-side or the crawl cannot match.** Paging an unfiltered lot in
site order returned 24 records and matched **zero** — every one was a model no
longer ingested. The pages fetched were structurally incapable of containing a
tracked record. Push the filter into the URL.

---

## 3. Regex window sizes must be derived from the data, not guessed

A parser anchored `"pricingBlock" … "id"` with a bounded window
`[\s\S]{0,2600}?` worked on a 162 KB page and returned **zero** on a 675 KB one
— while a sibling parser over the same document found 17 records.

The gap between the two anchors was ~1,700 chars on the small page and ~7,650
on the large one, because the larger page carries more per-record detail.

**Measure the real distance before choosing a bound:**

```ts
const a = [...html.matchAll(/"trackingPricing"/g)].map(m => m.index!);
const b = [...html.matchAll(/"vin"\s*:/g)].map(m => m.index!);
for (const x of a.slice(0,4)) {
  const next = b.find(v => v > x);
  console.log(`anchor@${x} next@${next} dist=${next! - x}`);
}
```

Choose a bound comfortably above the observed max but below the **per-record
spacing** (~9,800 here), so the window cannot spill into the neighbouring
record. Record both numbers in a comment — the next person needs to know why
12,000 and not 2,600.

Also check anchor **order**. Here the pricing block precedes the record's own
id; the original regex assumed the opposite and paired every record with the
*next* one's prices, producing uniformly plausible garbage.

---

## 4. Two DB drivers, one schema, one silent divergence

Running embedded Postgres (PGlite/WASM) locally and hosted Postgres in
production keeps the SQL dialect identical — the whole point of choosing it
over SQLite. But the **result shape differs**:

```
PGlite       ->  { rows: [ ... ] }
postgres-js  ->  [ ... ]
```

Code reading `res.rows` typechecks and works locally, then yields `undefined`
against the hosted driver. The symptom is **an empty dashboard**, not an error —
indistinguishable from a scraper outage.

Centralize once and route every raw query through it:

```ts
function unwrap<T>(res: unknown): T[] {
  const r = (res as { rows?: unknown[] })?.rows ?? res;
  return (Array.isArray(r) ? r : []) as T[];
}
```

Other portability notes from the same migration:

- **`.returning()` does not typecheck across a driver union.** Insert, then read
  the id back with an explicit `select ... order by id desc limit 1`.
- **Pooled connections reject prepared statements.** Set `prepare: false` and a
  small `max` when connecting through a transaction pooler, or serverless bursts
  exhaust the connection limit.
- **A `server-only` data module cannot be imported by CLI scripts** — it throws
  outside a request context. Keep a parallel factory for scripts that mirrors
  the same driver selection.

---

## 5. Shell trap: quote env values containing `&`

A hosted connection string ending `…&channel_binding=require`, written unquoted
to a dotenv file, causes `. ./.env.local` to **background the assignment**. The
variable arrives empty and the next command fails for a reason that has nothing
to do with the database.

```bash
printf 'DATABASE_URL="%s"\n' "$CS" > .env.local   # quoted
chmod 600 .env.local
```

Verify with `od -c` when a sourced value mysteriously reads as empty.
