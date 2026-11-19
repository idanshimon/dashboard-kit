---
name: derived-count-and-tier-integrity
description: "Derived numbers that lie: facet counts, latest-row picks, and parsers returning plausible-but-wrong values."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [sql, facets, data-integrity, scraping, ui, postgres]
    related_skills:
      - paged-list-count-integrity
      - empty-ui-surface-diagnosis
      - verifying-fixes-actually-executed
---

# Derived count and tier integrity

Two defect classes that share one signature: **the data is right, but a derived
number makes it look wrong**, so both user and agent go hunting for a bug that
does not exist. The wasted debugging cycle *is* the damage.

A third class inverts it and is worse: **the derived number looks right and is
wrong**. Nothing throws, nothing is empty, and the fabricated value gets ranked,
shipped, and acted on. See Defect 3.

Companion to `paged-list-count-integrity` (page-size-vs-total lies). This one
covers faceted counts and multi-tier row selection.

## When to Use

- A user says "1 result out of 7k? something in the filters is broken"
- A facet/sidebar count disagrees with what clicking it returns
- A column that had values quietly empties after a routine ingest
- **A parsed number looks impossible, suspiciously round, or too good** — a
  discount larger than any real discount, a price far below cost, a "best deal"
  that would be the deal of the decade
- **Identical derived values repeat across rows that should differ**
- **A parser returns 0 on some inputs and works on others**, or two parsers
  over the same document disagree about how many records exist
- You are writing `distinct on (key) ... order by key, updated_at desc` over
  rows from more than one source
- You are ranking or sorting by a derived field (`order by discount desc`) —
  ranking amplifies the largest error to the top of the list
- You are building faceted search over a scraped or multi-source dataset
- **You are about to report a count of "changes", "updates" or "new" items** —
  verify you are counting distinct VALUES, not rows
- **You are writing a "last updated" timestamp** over a table fed by more than
  one pipeline

## Gate observation eligibility before arithmetic

- Classify a source as an actual observation, a person's report, reference material or a derivation before assigning its numbers to a subject. A readable product/demo screen identifies what is displayed, not what happened in a real transaction or treatment.
- Keep occurrence/effective time, report time and collection/import time separate. Preserve day/month/unknown precision; a reporting timestamp must not manufacture a dated event or trend.
- Trace ambiguous numeric fields to the producer formula before comparing or narrating them. Carry the unit and measurement window through the schema, prompt and display: a single-session percent move, trailing-period percent move, index level and scaled indicator are not interchangeable. For generated summaries, forbid cross-window ranking explicitly and test the input contract; wording alone cannot repair an ambiguous field.
- Apply an explicit unit or measurement confirmation to the current record with its true source, and regenerate dependent views that still say assumed/unknown. A status-note correction alone does not repair an exported artifact. Keep user-confirmed separate from sensor-measured; changing a confirmed value with a UI control makes that edited value hypothetical again.
- For progress graphs, compare the same measure, subject, context and protocol against an explicit compatible baseline. Separate immediate response from later outcomes and measured change from reported improvement; an attractive composite is not a substitute for a defensible denominator.

See `references/dated-snapshot-provenance.md` for reference-versus-observation handling and longitudinal comparison gates.

## Derive available measurements before asking for more

- When the user asks whether dimensions or areas can be measured from captured data, calculate the supported values immediately and return them with their basis; do not substitute another disclaimer or request for manual measurements when scale and geometry already exist. Ask for physical references to calibrate accuracy, not to avoid deriving an estimate.
- Separate successful decoding from semantic interpretation: field names and low-cardinality byte histograms do not establish physical units, flags, or absence of height information. Prove the record structure first, then require source definitions or calibration for measurement claims.
- Treat a replacement sensor/device as a new evidence identity even when the product name is unchanged; do not transfer firmware, maps, scale checks or settings from the retired device.
- Keep sampled-cell area, reconstructed polygon area and bounding-box extents distinct. Verify polygon overlap before reporting a combined area; grid spacing establishes resolution, not accuracy.

For the geometry workflow and format-validation gates, read `references/sensor-map-measurements.md`.

## Rule 0 — verify in SQL before touching filter code

When a result looks impossibly small, **run the filter chain as a query first**
and watch where the number collapses:

```
2026                          7330
+ SANTA FE Hybrid              656
+ Limited                       31
+ 7 seats                        1   <- collapse is HERE
```

In the case this is written from, the answer was a real-world fact (that trim
ships with 6 captain's chairs, not 7 seats), not a bug. Confirming the truth of
the result before debugging the filter saves the whole cycle. State the
real-world explanation to the user — it is usually more useful than the code.

## Defect 1 — facet counts that ignore the active filters

The sidebar reads `7 seats — 1,590` while `Model + Trim` are already selected.
Click it, get 1 row. The filter was correct; the **count** advertised an
intersection that does not exist.

**A count that ignores the active selection is worse than no count at all.**

Fix — standard faceted-search semantics: count each facet with every *other*
facet's filters applied, but **not its own**. Own-facet exclusion is what keeps
multi-select usable, since it still shows what each extra option would add.

```sql
-- per facet, skipping only that facet's own predicate
select col::text as code, count(*)::int as n
  from listing l
 where <all OTHER active predicates>
   and col is not null
 group by 1
 order by n desc
```

Two traps while implementing:

- **`is not null` goes in WHERE, not HAVING.** Once `GROUP BY 1` groups on the
  cast expression, `HAVING col is not null` references an ungrouped column and
  Postgres throws `42803 errorMissingColumn`.
- **Facets come in two kinds and both are correct.** *Partition* facets sum to
  the grand total (year, model, dealer). *Multi-label* facets exceed it — one
  vehicle is both "SUV" and "Hybrid and EV". Do not assert that facet counts
  sum to the total; a multi-label facet legitimately overshoots, and flagging
  it as a failure burns a cycle on correct behaviour.

## Defect 2 — the "latest row per key" ordering trap

```sql
select distinct on (vin) ... from snapshot order by vin, observed_at desc
```

Looks obviously right. It silently destroys data whenever the **cheap** source
runs more often than the **rich** one:

```
price_ladder  discount=4325  23:31   <- the real price, scraped
bsi_api       discount=null  19:55
bsi_api       discount=null  19:40   <- next routine ingest writes another
```

The cheap API tier writes on every ingest and never carries a price. Ordering by
recency alone means the next ingest **buries every scraped price under a newer
priceless row**. No error, no warning — the column just empties itself.

```sql
-- rank COMPLETENESS first, recency second
order by vin, (discount is not null) desc, observed_at desc
```

Generalize: when rows for one key arrive from tiers of differing richness, the
"latest" row is almost never the one you want. Rank by *usefulness*, then
recency.

### The tie variant: equal timestamps make direction NON-DETERMINISTIC

The same trap fires with no richness difference at all, whenever two rows for
one key share the ordering value. `ORDER BY observed_at` over a tie leaves the
row order **undefined**, and the engine may return it either way on any given
run. If you then diff consecutive rows to report a change, you are not reporting
a wrong number — you are reporting a **randomly-signed** one.

Measured case: two readings of a finance rate recorded the same day — an undated
aggregator screenshot at `0.99%` and the vendor's own page at `1.49%`. Ordered
by date alone they tie, so the page could render *"1.49% -> 0.99%"* and announce
a rate **cut** when rates had **risen**. Nothing throws; the arrow just points
the wrong way, sometimes.

```sql
-- ties break on provenance WORST-FIRST: a lagging tier-4 source is, by
-- definition, describing the older state of the world.
ORDER BY key, observed_at ASC, best_tier DESC, id ASC   -- id = determinism
```

Three rules whenever you diff consecutive rows to derive a direction:

- **Every `ORDER BY` feeding a diff needs a total order.** Add a unique
  tiebreaker (`id`) as the last key, always. Without it the output is not
  reproducible and no test over it is trustworthy.
- **Choose the semantic tiebreaker deliberately**, before the syntactic one.
  "Which of these two readings describes the earlier world?" is a real question
  with a real answer; leaving it to the engine is how a rise becomes a cut.
- **Propagate the ambiguity to the UI.** If both readings share a date, you know
  the change happened but not *when* — surface `sameDate` and label it
  "change date not established" rather than printing two dates that imply
  precision you do not have.

This surfaced from a smoke test that wrote one throwaway row and read it back,
not from review — the code looked obviously correct. Diff-over-ordered-rows is
worth an explicit "do two rows tie here?" check every time.

**Corollary:** if you add such a predicate to the row query, the **count query
must use the same joins**. Otherwise it throws on the snapshot column, or worse
silently returns a total that disagrees with the rows shown — reintroducing the
page-size-lie defect through the back door.

## Defect 3 — parsers that return plausible, wrong numbers

The most dangerous output is not an error or an empty set. It is a number that
**looks like data**. A parse that throws gets fixed in minutes; a parse that
returns `discount = 61,876` gets shipped, ranked first, and acted on.

Real cases, all from one scraping session:

| Symptom | Actual cause |
|---|---|
| `$61,876 off` a $62,675 car, ranked #1 | `$799` doc **fee** read from a price field |
| 105 cars at one dealer "above MSRP" | ladder total collapsed onto the doc fee; disagreed with `msrp - price` |
| 24 different VINs, identical `-$695` | pricing block paired with the **next** record |
| Parser returns 0 on a big page, fine on a small one | bounded regex window sized against the smaller sample |

**Assert what the numbers must MEAN, not merely that they parsed.** Three
cheap, high-yield checks:

```ts
// 1. Plausibility — a NEW car never sells at half of MSRP.
//    Below that, the "price" is a fee. Record null (= not measured), keep MSRP.
const plausible = price != null && msrp != null && price > msrp * 0.5;

// 2. Coherence — two derivations of one quantity must agree.
//    Prefer the derivation from the columns you DISPLAY; accept the richer
//    structured source only when it corroborates.
const coherent = Math.abs(ladderTotal - (msrp - price)) < 1;

// 3. Arithmetic reconciliation — make the ladder prove itself.
//    msrp - dealerDiscount + fees == subtotal;  subtotal - rebates == final
```

Reconciliation is what upgrades "24 rows parsed" into "24 rows parsed, **0
mismatches**". A mislabelled row still produces numbers; only the arithmetic
catches it.

### Uniformity is an association bug until proven otherwise

Identical derived values across rows that should differ means fields from
adjacent records got paired. Mispaired data is often *more* uniform than real
data, which is exactly why it reads as clean. Prove pairing by **offset
arithmetic** (do the anchors interleave as assumed?), not by eyeballing output.

### Cross-check two parsers over one document

The fastest localizer available: if parser A finds 17 records and parser B
finds 0 on the same page, the fault is in B, not the fetch, not the site. Keep
a probe script that prints per-tier counts side by side.

### Scope a failure assertion to the widest thing that must be non-empty

A per-facet zero is usually **inventory** (this dealer stocks none of that
trim). Zero across *every* facet is a broken parser. Raising `parse_failure` on
the narrow case marks healthy sources dead.

### A health flag needs a clear path, not just a set path

`status='failing'` set on error but never cleared on success is a **latch**, not
a status: once a source trips it, a later fix can never bring it back and
coverage silently stops recovering. Clear it in the same write that sets it, and
provide an explicit retry override.

## Classify failures; never surface raw exception strings

A stack trace in a status column is not information. Twelve rows of
`Error: fetch https://... -> 403` is the same three problems repeated twelve
times, and the reader has to decode each one. Store the message (drop the
stack), then classify at **read** time into a stable code + human summary +
**remedy**:

| Code | Signal | Remedy | Retryable |
|---|---|---|---|
| `blocked` | 403/429 | Bot protection; needs a different route | yes |
| `bot_challenge` | **HTTP 200** + tiny interstitial body | Different lane entirely; see the browser reference | no |
| `not_found` | 404 | URL derivation wrong for this platform | no |
| `server_error` | 5xx | Theirs; retry next run | yes |
| `parse_failure` | fetched a known platform, extracted nothing | Adapter work | no |

Group the UI by cause, so it reads *"8 sources block us — one fix"* instead of
twelve separate mysteries. Assert in tests that **no summary leaks a URL or the
word `Error:`**.

### Report the most DIAGNOSTIC error, not the last one tried

When you try candidate paths in sequence and all fail, keeping the *last*
exception is actively misleading. A platform-A `404` masked the real platform-B
`403`, so the UI said *"wrong URL — fix URL derivation"* and pointed at code
that was already correct. Rank instead:

```
bot_challenge  >  403/429  >  5xx  >  timeout  >  404
```

The user caught this one by knowing the URL existed. Trust that signal.



A fetch that returns 403 must not report as "no offers found". In this session
three dealers were reported as publishing nothing; they were rejecting the
request. The distinction must survive into the log line and the UI:

```
BLOCKED/FAILED <reason>                    <- could not read
page loaded (900kb), no advertised offer   <- read fine, genuinely nothing
```

Same rule at the UI layer: an unmeasured cell reads **"not measured"**, never a
blank or a `0`. Show real coverage — `83 of 7,921 have a real price` — rather
than a vague caveat, and offer a "show priced only" toggle so the user can see
the measured subset directly.

## HTTP 403 is often YOUR headers

Before concluding a site blocks scraping, send a **full browser header set**.
Several platforms fingerprint the whole set, not just `User-Agent`. Verified:
identical URL, 403 with UA alone, 200 with these added:

```
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Upgrade-Insecure-Requests: 1
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
```

Also: rejection status varies by agent string (curl default → 406, urllib →
403). **Never branch on the specific code** — just always send browser headers.

## Sampling a nullable column

`select x from t where key=$1 limit 1` with no null predicate returns an
*arbitrary* row. If the column is null on a fraction of rows, you will report
"no value known" for keys that have plenty. Filter explicitly:

```sql
where key = $1 and url is not null limit 1
```

This produced a false "22 dealers have no URL" report when the URLs were
present all along.

## Sortable column headers — the no-op header, and sorting as a bug detector

Adding click-to-sort headers has one dominant failure: the header **renders,
links, and changes nothing**. Same family as a filter that silently matches
everything — it looks authoritative and is inert. Cause is almost always a
missing `ORDER BY` branch. In one table, 5 of 8 columns had headers but **no
server-side sort implementation at all**; the UI was complete, the query
ignored them.

The assertion that catches it is not "does the page load" but *does the result
actually change*:

```ts
// For every sortable column, asc and desc must return a DIFFERENT first row.
const a = await query({ sort: `${col}-asc`,  limit: 5 });
const d = await query({ sort: `${col}-desc`, limit: 5 });
assert(a.rows[0].id !== d.rows[0].id, `${col}: asc/desc identical -> no-op`);
// ...and the column must be monotonic across the returned page.
```

Whitelist sort keys server-side (`switch` over known values, `default` to a
safe order); never interpolate a user-supplied column into SQL.

**The same defect hits deep-link FILTER params.** A cross-page link such as
`/listings?vin=ABC` is silently ignored when the query builder has no clause
for that key — the user lands on the *unfiltered* list and reasonably believes
that is the filtered result. Adding the link and adding the predicate are two
edits; shipping only the first produces a link that looks like it works. Verify
the parameter is **consumed**, not merely that the URL is well-formed.

**Sorting is the cheapest bad-data detector you will ever write**, because it
surfaces the extremes nobody looks at. Adding sort tests immediately exposed
two defects invisible in the default view: `msrp-asc` led with an **$895 MSRP**
on a $40k vehicle (a doc fee parsed into the MSRP field), and `discount-asc`
led with **−$2,389** (stale rows from a since-fixed parser bug). Expect to find
data bugs when you add sorting; check the head of *both* directions.

UX details that matter: give each column its **own** sensible first direction
(alphabetical opens A→Z, money/discount opens **biggest first** — defaulting
everything to `asc` puts a `$0` discount atop the column clicked to find the
largest); **drop `page`** on any sort change; set `aria-sort`; and use `NULLS
LAST` so unmeasured rows never occupy the "cheapest" slot. If a column's
backing data is entirely unpopulated, say so rather than shipping a header that
does nothing.

## Verification order

1. Run the filter chain in SQL and find where the number collapses
2. Confirm whether the collapse is a **real-world fact** before editing code
3. Re-check facet counts *with filters applied*
4. Assert plausibility, coherence and arithmetic on parsed numbers — a clean
   parse count is not a clean parse
5. Only then look at query/UI code

## Never count ROWS as a proxy for CHANGE

A freshness bar shipped reading *"1,151 price changes recorded"*. The market had
moved **twice**.

The count was `VINs having count(*) > 1` over priced rows, justified by a
write-time invariant: *snapshots are change-only, so a second row implies
movement*. The invariant was real in the ingest path — and false in the
database. Re-running a sweep writes a fresh row at the **same** price, and a
`--retry-failing` pass re-observes a source wholesale. A day of adapter
debugging left 1,151 VINs with duplicate rows at identical values.

```sql
-- WRONG: row count is observation count, not movement
having count(*) > 1                  -- 1,151
-- RIGHT: distinct values is movement
having count(distinct price) > 1     --     2
```

**The general rule: never let a write-time guarantee become a read-time
shortcut.** Ingest-side dedup is best-effort — reruns, backfills and retries all
violate it — so measure the property you are actually claiming. If you claim
"changed", count distinct values.

Two things make this class of bug catchable:

- **Cross-page disagreement is the tell.** The alerts page already listed
  exactly 2 price drops from its own `lag()` query. Two surfaces over one
  dataset disagreeing by three orders of magnitude localizes the bug instantly —
  when two views of the same fact disagree, one is lying and neither should be
  trusted until you know which.
- **Print the claimed items, not just the count.** A guard that asserts the
  strict count ≤ the loose one, then *renders every claimed change with its
  actual value sequence*, turns a wrong number from merely large into visibly
  absurd.

Label accordingly: "N vehicles repriced since tracking began" states the
population and window. "N price changes recorded" invites reading it as
events-per-run.

## An AGGREGATE SCORE is a derived number, and it hides the field that matters

The same defect class in evaluation harnesses, quality gates and scorecards.
Measured 2026-09-10 on the first run of a new eval suite:

```
MERGE ALLOWED — 94.4%          <- composite, above the declared 0.9
  recommendedAction    66.7%  FAIL   <- the only field that decides anything
  draft.noContactClaim 100.0% PASS
  draft.noPrescription 100.0% PASS
  draft.noDiagnosis    100.0% PASS
  draft.identifiesSubj 100.0% PASS
  draft.bedsideLength  100.0% PASS
```

The gate said **ship it** while the system chose the wrong action on a third of
cases. Five cheap string predicates outvoted the one hard check.

**Assertion count is an implicit weighting.** Adding easy checks to a suite
silently dilutes the hard ones — so a suite gets *less* trustworthy as it grows,
which is the opposite of what everyone assumes. Nothing throws; the mean simply
absorbs the failure.

Worse, that codebase already carried the comment *"an aggregate hides the one
field that regressed"* — and then gated on the aggregate anyway. It **printed**
per-field scores and **enforced** the mean. A number nobody enforces is
decoration, and a correct principle in a comment is not a control.

Gate in three tiers, not one number:

| Tier | Rule |
|---|---|
| **Safety / must-never** | Fails the run at ANY score. Never averaged. |
| **Decision fields** | Must each independently clear the operating point. |
| **Quality signals** | May be averaged into a composite. |

```ts
const allowed = composite >= operatingPoint
  && safetyFailures(run).length === 0        // tier 1: never tradeable
  && underperformingFields(run).length === 0 // tier 2: per-field, enforced
```

Generalises past evals to any weighted composite: a health score, an SLO
rollup, a readiness percentage. **Ask which single component, at zero, should
fail the whole thing — then check that it actually does.** If the answer is
"the mean would still pass," the composite is not measuring what it claims.

Related trap when the thing under test is free text (a generated message, a
summary): there is no correct string, so assertions become **predicates** —
things that must never appear and must always appear. Passing them means *not
dangerous*, not *good*. Keep the regexes narrow; a predicate that fires on a
correct output teaches everyone to ignore the suite. Make an unknown predicate
name fail rather than silently pass, or a fixture typo quietly reduces coverage.

### Verify the harness is asking the right question before reading the score

The same run initially failed **every** text predicate. The cause was not the
system under test: an offline stub branched on `req.context.startsWith("eval.")`,
so a newly-added `eval.runtime-triage` context matched the older `eval.extraction`
branch and returned the wrong response shape entirely.

**A first run that fails is not evidence the thing under test is broken.**
Prefix-matching on context/route strings is the specific hazard — adding a
sibling key silently reroutes it into an existing branch. Match exactly.

And: **scores from a stub/offline profile are plumbing proof, never a baseline.**
A deterministic fake that pattern-matches its input can neither pass nor fail in
the way a real model does. Label such numbers as harness verification and re-run
against the real dependency before quoting anything.

## A stale disclaimer is a lie in the safe direction

Honesty banners rot. A dashboard shipped with *"Seed data captured 2026-08-29.
Scheduled sweeps and price history are **not wired up yet**, so nothing here is
live"* — correct on day one, false by day two once 144 sweep jobs had run. It
also read `Vehicles 7,921` from the frozen seed while the tracked set was
`2,512`.

The cause is structural, not editorial: the page was `force-static` over a JSON
snapshot, so **every number and every caveat was pinned to first capture**.

**Under-claiming is not the safe side of honesty.** It is wrong in the other
direction, and it trains the reader to discount everything the surface says —
including the warnings that *are* true. Treat a stale "this isn't real yet"
banner with the same seriousness as an inflated metric.

Two habits:

- **Derive caveats, don't hard-code them.** Render the sweep warning only when a
  sweep actually failed; render coverage from a live count. A banner that is
  always on is a banner nobody reads.
- **Audit static/seed-backed pages whenever the pipeline behind them changes.**
  `force-static` + a checked-in fixture is the shape that guarantees this bug.
  Grep for the fixture import when the real feed goes live.

## Data freshness: there is usually more than one clock
A "last updated" timestamp is a derived number too, and the naive version lies
by conflating pipelines of different richness — the same shape as Defect 2.

Two feeds wrote to one table: a cheap inventory pass (a row for every record,
**no price**) and an expensive scrape (the actual prices). Measured: one
inventory batch was 1,081 records / **0 priced**. A single `max(observed_at)`
would have reported *"updated 8 minutes ago"* while every price on screen was
**4 hours** old.

- Track `lastPriceAt` separately from `lastSnapshotAt`, and **lead with the one
  the user is actually reading**. Show the cheap clock only when it *differs* —
  otherwise it is the same fact printed twice.
- Measure "updated since" against the **end of the previous run**, not a rolling
  24h window. Runs are bursty (dozens of sources over minutes), so a fixed
  window splits one run across two buckets and reports half of it. Detect runs
  by gap — `> 30 min` between observations starts a new one — and validate the
  grouping against real timestamps before trusting it.
- **Set the staleness threshold above one full cycle.** With a daily job, a
  healthy system is routinely ~24h stale right before the next run; warning at
  24h leaves the badge amber most of the day and trains the reader to ignore it.
  36h means a run was genuinely *missed*.

## Purge fabricated rows, don't just stop writing them

Fixing the parser does not fix the database. Rows written under the old bug
persist, and a `distinct on (key) ... order by discount desc` ranking will
**always prefer the biggest lie**. Delete by the same predicate the new gate
enforces:

```sql
delete from snapshot where price is not null and msrp is not null
                       and price <= msrp * 0.5;   -- implausible
delete from snapshot where discount < 0;          -- incoherent
```

Then re-run the collection and re-verify. See
`verifying-fixes-actually-executed` — a fix that ran is not the same as a fix
whose *effects* are gone.

## Parsers that silently DROP records

Defect 3 covers parsers that return a wrong *value*. The sibling defect returns
the right values for a **fraction** of the records and no error at all.

The tell is a field that reads as "never filled in" across most rows. A persona
index showed a role column blank on 94% of rows; the real bug was a block
splitter using `re.split` on `---` separators and then taking **one match per
chunk**, in a corpus where separators were optional. 579 source records became
55. Nothing threw.

**Split on the marker that DEFINES a record, never on the one that visually
separates them.** Separators are optional human decoration; the record marker is
structural. Any `re.split(...)` followed by a single `.search()` per chunk is
this bug in waiting.

The gate is cheap and belongs in `make check`: count the record marker in the
**source** and compare against rows landed, with a ratio threshold (75%), not
equality — legitimate filtering removes some. Equality yields a permanently red
gate that everyone ignores.

Expect a parser fix that multiplies row count to **expose downstream bugs that
held only on the subset** — placeholder values, and name-cleanup steps whose
*order* mattered. See `references/silent-record-loss-and-retrieval-ranking.md`.

- **Cross-record graph metrics and peer-comparison tables must be computed over the cohort before applying a single-person view filter.** Filtering the input rows to one person before building a team scorecard or cross-person reuse/citation graph drops peer rows and zeroes out incoming edges ("reused by peers" = 0) because the citing records belong to other authors; compute over the date/scope-filtered cohort and use the person selector only to highlight their row or filter individual-item lists.
- **Exclude structurally ineligible record types from compliance/binding denominators.** When a corpus mixes customer records with internal/enablement records that can never carry a CRM opportunity or milestone, divide only by eligible customer records and disclose the excluded internal count alongside (`29c + 18i`) rather than deflating the rate.

See `references/multi-tier-scraping-integrity.md` for extended field notes, and
`references/plausible-wrong-parser-output.md` for the seven plausible-wrong
parser cases (fee-as-price, ladder incoherence, record mispairing, window
sizing, param encoding, empty-facet-vs-failure, sticky status) plus the
two-driver `{rows}`-vs-array divergence and the `.env` `&`-quoting trap.

See `references/scraper-url-derivation-and-portability.md` when a scrape spans
several site platforms or a datastore is moving between drivers: platform
fingerprinting from a detail URL, candidate-URL fallback lists, facet
case/`%20`-encoding probes, **measuring** a regex window instead of guessing it,
and the `unwrap<T>()` shim for the `{rows}`-vs-array split.

See `references/dated-snapshot-provenance.md` when the value you are recording
is only true *on a date* — advertised rates, promo pricing, incentive terms.
Covers append-only snapshot tables, why an undated screenshot must never enter a
current-state table, and the disclosed-vs-derived distinction that keeps a
back-solved number from rendering like a published one.

See `references/browser-tier-and-bot-challenges.md` before escalating to a
headless browser: when the browser tier genuinely helps (client-side rendering)
versus when it cannot (bot management), the **HTTP-200 bot challenge** that
masquerades as a parser failure, per-site rather than per-platform enforcement,
Playwright operational traps (`networkidle` never settling, lazy-loaded rows,
the unclosed-singleton "hang", `__name is not defined` under `tsx`), and — the
rung most agents miss — **reading the page through the USER'S already-running
Chrome over CDP**, which defeats bot management that rejects every automated
browser, and yields exact CSS custom properties when the goal is design
reconnaissance.

For the **vehicle/dealer** instance of all this — the Dealer.com / DealerOn /
Team Velocity platform taxonomy, the itemized `dprice` ladder format, and the
conditional-incentive trap — see the sibling skill
`vehicle-lease-and-dealer-negotiation`, file
`references/dealer-inventory-scraping-platforms.md`. The app those notes were
built from is documented in that skill's `references/cartrack-app.md`
(`~/projects/cartrack`, `cartrack-app.vercel.app`) — identity, coverage, the
manufacturer-offer feed, and open items. (That skill's SKILL.md is at its 100k
size cap and cannot carry new body pointers, so this cross-link is the
discovery path.)

## Split a discount into who can actually move it

A single "total off" number conflates two kinds of money and misleads the
person negotiating with it. When a source publishes an itemized ladder, keep
the parts:

```
MSRP                $58,815
Dealer Discount      $1,847   <- the seller's own margin: NEGOTIABLE
Documentation Fee      $490   <- an ADDITION; never net it into the discount
Discounted Price    $57,458
Offers               $3,000   <- manufacturer/3rd-party: CONDITIONAL, fixed
Final Price         $54,458
```

Reporting `$4,357 off` sends the buyer to argue against $3,000 they cannot move
and to assume rebates they may not qualify for. Persist the components
(`dealer_discount`, `doc_fee`, `incentive_total`, plus the itemized offers as
JSON) so the UI can say which part is negotiable.

## Extracting JSON from a CLI, and ranking what you retrieved

`references/silent-record-loss-and-retrieval-ranking.md` also carries three
non-scraping cases of the same "plausible but wrong" family:

- **CLI `--json` output wrapped in chrome on BOTH sides** — a banner before and
  a timing footer after, so slicing from the first bracket to end-of-string
  still fails. Walk inward from both ends, filter `-1` before `min()`, and
  always print the decode error rather than returning `None` (a swallowed
  framing bug reads as an auth or connectivity failure).
- **Currency as a formatted string** (`"$30,000"`) beside a numeric twin;
  `float()` raises and a bare `except` silently zeroes real revenue. Verify the
  total against an independent API path before believing it.
- **Hybrid-search RRF left at textbook defaults** — `k=60` over 40 candidates
  flattens the whole ranking, plain summation gives no credit for two
  retrievers agreeing, and with no similarity floor boilerplate (`CHANGELOG`,
  `README`, `_moc`) outranks real documents on topic alone. Evaluate on a fixed
  query set per mode, and return `matched: both|fts|sem` so ranking is
  inspectable.
- **A retrieval layer that is never actually wired to its LLM consumer.** Plausible
  answers from an agent that can read the filesystem are not evidence the
  context was passed — read the request handler and confirm.

**Trust structural `type` fields over human labels.** Ladder rows carried
`type=MIDDLE|-|+|TOTAL|SICI|SIF` with vendor-branded labels ("Ciocca Price",
"Koeppel Price"). The types are matchable across vendors; the labels are not.

**Gate numeric types before coercion; missing is not zero.** Accept finite numbers and, only when the input contract permits, nonblank numeric strings. Reject null, undefined, blanks, booleans, arrays and objects before calling JavaScript `Number()`; several coerce to zero and manufacture dates, prices or scoring penalties. Preserve actual zero. Test both the helper's rejection matrix and its downstream ranking/display behavior. See `references/plausible-wrong-parser-output.md` for the concrete regression recipe.

A source without a published value must record `null`, not `0`; zero asserts a measured absence, not missing evidence.

## Attribution: crediting records to an entity

Per-entity rollups (decisions per agent, spend per team) fail like Defect 2: the obvious key field is absent on the real producer shape, so every entity reads idle while the data is there. Before building the rollup, histogram the candidate keys over a REAL sample (not fixtures): which fields are populated, on how many rows. Fall back only to a field the producer itself wrote (e.g. a stage recorded inside a provenance/trace string), never to an inferred one; count anything still unmapped as an explicit `unattributed` total shown in the UI. Prefer an explicit "who decided" field over a normalizer default that fills a missing actor with a plausible value. Track how many rows actually carried a summed metric so an all-missing sum renders "not recorded", not 0. Size time buckets to the observed data age: a 14-day sparkline over weeks-old data is an empty chart that reads as "inactive".

