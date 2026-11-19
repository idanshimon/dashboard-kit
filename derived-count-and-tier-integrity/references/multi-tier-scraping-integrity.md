# Multi-tier scraping: field notes

Extended detail behind `SKILL.md`. Written from building a live vehicle
inventory tracker over one OEM API plus ~40 dealer sites (Aug 2026).

## Why tiers exist at all

The manufacturer API was authoritative for **discovery** (every vehicle in a
radius, dealer identity, specs) but unusable for **price**. Measured across
7,921 records from its own feed:

```
missing / zero      2,555
ABOVE msrp            879
usable              4,487  (57%)
```

**43% of the OEM's own price field was unusable.** A 30-record sample predicted
this exactly, so a small sample is enough to establish the pattern — but state
it as a measured number, not an impression.

Design consequence: the API tier writes snapshots with `price` and `discount`
explicitly **NULL**, and only richer tiers may populate them. Enforce that in
the ingest code, not just in a comment.

## The vendor "discount" field is often a lie

A dealer platform's own JSON reported `"discount": 0.0` on every vehicle while
`msrp - price` was a real **$3,825**. Reading the vendor field reports zero
deals on a lot full of them.

**Always derive the discount yourself.** Never read a field named `discount`,
`savings`, or `total_off` and trust it.

Related: a dealer asking **above** MSRP is real (market adjustment). Record it
as a *negative* discount rather than clamping to zero — hiding it is the same
sin as the feed reporting 0.0.

## Tier design that worked

1. **API tier** — discovery, identity, specs. Cheap, complete, no price.
2. **Listing-page tier** — platform-specific inline JSON (e.g. a
   `vehiclesData = [...]` array). Gives real selling price.
3. **Detail-page tier** — the richest, and the only source for some data.

Adapters are written per **PLATFORM**, not per dealer. Dealer sites are
white-labeled instances of a handful of platforms, so one parser serves many
dealers. Detect the platform from a page fingerprint and cache it on the dealer
row.

## URL discovery beats URL guessing

First attempt derived each dealer's inventory root by guessing a path
convention observed at one dealer. Result: 15 of 40 dealers 404'd, because that
path was a single platform's convention, not a standard.

The API already returned a **per-vehicle detail URL**. Deriving the site root
from a URL you were *given* is strictly better than pattern-guessing. Where a
per-item URL exists, prefer it and skip root discovery entirely.

## Legal disclaimer prose is a first-class data source

The richest pricing data was not in any JSON — it was in the regulated
advertisement text:

> MSRP $49,910.00 ... Selling price $43,660.00 ... $7,803.90 due at signing ...
> Option to purchase vehicle at lease end is $31,743.30 ... $0.20/mile over
> 7500 miles/year ... Must finance through [captive lender].

Two prices for the same car — the difference is captive-lender incentive money,
conditional on financing through the manufacturer's own bank. **No single API
price field can express "one number if you lease, another if you finance"**,
which is why it exists only as prose.

Parser pitfalls found by testing, not by reasoning:

- A fixed-width capture window (`{0,1200}`) **overruns into the next offer
  block**, so a lease disclaimer inherits the finance APR. Cut the window at
  the start of the next block.
- Cut at the *other* offer type, not the first repeat — the same disclaimer is
  duplicated verbatim in mobile and desktop markup, so cutting at the first
  repeat truncates before the prices.
- A lease has **no APR at all** (money factor + residual). Refuse to report one
  rather than publish a wrong rate inherited from a neighbouring block.

## The itemized ladder variant

A different platform family publishes a structured breakdown instead of prose:

```
MSRP               $50,060
Dealer Discount     -$1,500
Doc Fee                $175
<Dealer> Price      $48,735
Retail Bonus Cash   -$3,000
Price               $45,735
```

This is **richer than a single price**: it separates the dealer's own discount
from manufacturer rebate money — the distinction that decides what is
negotiable. Parse the ladder as a distinct tier; take the LAST `Price $x` as
final.

## Normalizing offers so they are comparable

Advertised payments are not comparable across dealers: different cash down,
term, and allowance. The fix is arithmetic, not judgement.

```
effective_monthly = (due_at_signing + payments) / term
```

`due_at_signing` **already includes the first payment**, so charging all `term`
payments on top double-counts it. Use `pmt * (term - 1)` when it is present.

Worked example, same vehicle, two structures:

```
advertised  $318/mo + $7,804 up front  ->  $18,934 total  ->  $526/mo effective
negotiated  $551/mo +   $551 up front  ->  $19,836 total  ->  $551/mo effective
```

A $233/mo headline gap is really ~$25/mo. Add a common mileage basis (price the
shortfall at the published overage rate) and the cheaper-looking offer can
invert entirely.

## Politeness and fan-out

- ~2s between requests, per dealer.
- **One dealer per invocation.** A 40-dealer sweep at that spacing cannot fit
  in a serverless function timeout; one dealer runs in 10–40s, and a slow
  dealer cannot poison the whole sweep.
- Record per-dealer sweep outcome (`success` / `parse_failure` / `blocked`) so
  coverage gaps are visible rather than implicit.

## Snapshots must be append-only

Price history *is* the product. Never update a price row in place — insert a
new snapshot. Keep `first_seen_at` immutable across re-ingests (backfill other
columns via upsert, but never that one); it is what makes "days on lot" a real
negotiating datum no listing exposes.
