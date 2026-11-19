# Dated snapshot provenance

For values that are **only true on a date** — advertised APRs, promo lease
payments, incentive terms, shipping quotes, any "current offer". The defect
class: a figure that was correct last week renders identically to one read this
morning, so the reader cannot tell live from dead.

## The triggering artefact

A financing comparison table, shown in a video, listing `0.99% APR`. The vendor
had moved to `1.49%` days earlier. The page carried **no visible as-of date**,
so the stale number was indistinguishable from a live one.

Three separate defects in that one table, each worth guarding independently:

1. **No reading date** — staleness invisible.
2. **A derived column styled like a disclosed one** — the table had a "Lease
   APR" column beside the loan APR. The vendor publishes a loan APR and does
   **not** publish a money factor, so every lease APR there was back-solved by
   the publisher. Same font, same alignment, same implied authority.
3. **Prices with no fee basis** — `$41,990` next to another table's `$43,630`
   for the same item. One included ~$1,640 of destination and order fees. Not
   comparable, and nothing on either page said so.

## Model it as a SNAPSHOT table, not a current-state table

Append-only. A new reading is a **new row**, never an edit.

```
id, observed_at, subject_id, trim_label, market,
loan_apr_percent, loan_term_months, loan_payment_usd,
lease_apr_percent, lease_apr_basis,        -- advertised | derived | unknown
lease_term_months, lease_payment_usd, lease_due_at_signing_usd,
from_price_usd, from_price_includes_fees,  -- three-state: true|false|NULL
source_ids[], note
```

`observed_at` is **the date you READ it**, not the date it took effect. Those
are different facts and conflating them invents precision. When the effective
date is genuinely known, that belongs in a separate dated *event*, sourced.

### Gates worth failing the build over

- A lease APR **requires** its basis. Unlabelled, a back-solved number
  masquerades as a published one — the single most misleading cell on a
  financing page.
- A payment **requires** its term. `$499/mo` over 24 vs 36 months are different
  products; a payment without a term is unreadable.
- A price **requires** its fee basis, as a three-state boolean. `NULL` means
  "the source didn't say" and must render as *fee basis unknown*, never as
  "excludes".
- A snapshot sourced **only** from a lagging aggregator tier must be forced to
  `basis='derived'` for any rate it publishes that the vendor does not.

### Group readings by (date, publisher), never merge them

A rate table is meaningful only as a set of numbers observed **together on one
day from one source**. Merging two publishers into one "current" table is
exactly how a superseded `0.99%` ends up sitting beside a live `1.49%` with
nothing to distinguish them. Render each reading as its own stamped block,
best-provenance first, and badge a lagging-tier block *"do not treat as
current"*.

### Retain superseded readings

Do not delete the stale row once a newer one lands. A withdrawn rate is evidence
of **how fast the vendor moves**, which is often the actual analytical value.
Mark it superseded, keep it queryable, and let the diff between readings be the
headline: *"1.49%, read Sep 5 — up from 0.99%, read Aug 30"* beats a bare
number with no history.

See the tie-break warning in the parent SKILL.md before diffing consecutive
readings: two readings can share a date, and an untied `ORDER BY` will randomize
the direction of the change you report.

## Reference artifacts are not observations

Classify the artifact's purpose before extracting a subject-specific value:

1. Identify the object/model from reliable labels.
2. Establish whether the artifact documents the actual event or is supplied only as a reference, illustration or example.
3. Transcribe only event-relevant values into the subject's observation record. Keep reference material separate, even when its numbers are perfectly legible.
4. Record values supplied verbally as reported observations with their actual attribution. A later explicit unit confirmation resolves that field; it does not authenticate the rest of a device screen or document.
5. If a source is subsequently clarified as reference-only, remove its numbers from the current observational dataset and derived views. Preserve the correction/provenance trail rather than retaining the false observation under an uncertainty banner.
6. Read the source's field semantics before treating a counter as a result: target, remaining and delivered quantities are different facts.

A manufacturer's replacement product image is illustrative media, not new evidence of a subject's event. Changing the image must not change the recorded event parameters.

## Longitudinal comparisons need semantic compatibility

Define the comparison contract before plotting a trajectory:

- Match subject, issue, measure, unit, task and measurement protocol where relevant; similar labels alone do not establish comparability.
- Require an explicit baseline rather than repurposing procedural discomfort, a recalled percentage improvement or an unrelated earlier reading.
- Keep absolute change and percentage change distinct. Do not calculate percentage change with a missing or zero denominator, and do not back-solve undocumented starting/ending values from a reported improvement range.
- Use actual occurrence dates for the time axis. Keep month-only and undated history visibly separate instead of placing it on an invented day or at import time.
- Distinguish immediate response from follow-up. A single immediate result does not establish persistence, and repeated observations without an appropriate control do not establish causation.
- Prefer measure-specific graphs with visible formulas and missing-data states to an unexplained weighted improvement score. Keep any borrowed demonstration data or weights out of a real subject's record.

Validate these as data-model and calculation invariants before claiming a working longitudinal system; a specification alone is not implementation evidence.

## Make the update path a command, not hand-edited JSON

A snapshot table only stays honest if appending to it is cheaper than editing
the old row. Ship a CLI (`data:snapshot rate --variant X --loan-apr 1.49
--source-url ... --tier 2`) that:

- refuses a lease APR with no basis, a price with no fee flag, an unknown
  subject, and a duplicate `(date, publisher, subject)`;
- registers the source once and reuses it by URL;
- **reports the delta against the previous reading** on success — *"loan 1.49%
  — was 0.99% on 2026-09-05"*. That line is the whole point: it turns a write
  into a verification.

Exercise every guard for real after writing it. All three refusals above were
confirmed by running them and diffing the data file to prove **zero rows** were
written by a failed command. A guard that compiles is not a guard that fires.
