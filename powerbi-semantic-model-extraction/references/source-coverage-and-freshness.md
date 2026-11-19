# Source coverage and freshness

Use when a dashboard refresh succeeds but company charts stop at different months.
This is a diagnostic and acceptance procedure, not a claim that any project's dense
collector has already been deployed.

## 1. Establish which clock is stale

Read saved capture and served payload metadata, then inspect the exact scheduled
entry point. Distinguish:

- attempted/completed collection;
- source refresh date, preserving its formatting and unknown timezone;
- period represented by a cell and whether the source marks it closed;
- latest reported period for each account and metric.

Do not diagnose upstream delay from file age or a green badge. Query the actual
source for representative affected accounts first. A refreshed dataset can contain
blank cells; its refresh date does not explain why they are blank.

When validating a claimed weekly refresh day, preserve the before-publication,
run the authorized recording entry point, and compare exact matched-ID values,
source-load timestamps and closure independently. Read back publication/health
capture identity and retain prior snapshot hashes. Compare historical values by
field family under equal query hashes/cohorts: daily credit changes do not establish
seat, pipeline or product-mix cadence. Name first-observed change dates separately
from source-reported load dates, keep unknown source timezones explicit, and do not
promote an empirical pattern into an official schedule.

## 2. Probe without suppressing evidence

After discovering the real table/column names, use a small explicit account set and
a bounded month range. A reusable DAX shape is:

```dax
EVALUATE SUMMARIZECOLUMNS(
    'Dim_Account'[TPID],
    'Dim_Calendar'[FiscalMonth],
    'Dim_Calendar'[RelativeFM],
    'Dim_Calendar'[IsClosed],
    TREATAS({<verified numeric account IDs>}, 'Dim_Account'[TPID]),
    FILTER(VALUES('Dim_Calendar'[RelativeFM]),
        NOT ISBLANK('Dim_Calendar'[RelativeFM]) &&
        'Dim_Calendar'[RelativeFM] >= -1 &&
        'Dim_Calendar'[RelativeFM] <= 0),
    FILTER(VALUES('Dim_Calendar'[FiscalMonth]),
        NOT ISBLANK('Dim_Calendar'[FiscalMonth])),
    "Present", 1,
    "Value", [<verified measure>]
)
```

Apply the report's actual population filters as well. Keep the raw response locally.
The constant prevents SUMMARIZECOLUMNS from dropping all-blank measure rows. Explicit
blank-calendar exclusion prevents an extra synthetic month because DAX comparisons
can treat blank as zero.

Classify independently of period closure:

| Source result | Meaning | Treatment |
|---|---|---|
| Finite nonzero number | Reported value | Preserve it |
| Numeric/formatted zero | Reported zero at the returned precision | Preserve zero; not proof of zero product usage |
| Null/blank measure in returned row | Source returned blank | Preserve null; do not invent the cause |
| No expected account/month row | Collection coverage failure | Investigate filters/truncation; do not relabel as source blank |
| Malformed numeric string | Parsing/schema failure | Fail validation rather than convert to null or zero |

## 3. Reconcile coverage before publication

Discover population IDs and count independently; retrieve the source period axis
with closure flags. Batch below the endpoint cap using maximum periods per account,
not observed sparse row counts. Require each expected tuple once, reject foreign
IDs/out-of-window periods, and check schemas and row widths between batches.

Report expected, returned, numeric-reported, zero and blank counts per metric/month.
Define whether zero is a subset of reported; otherwise displayed counts can double
count. Keep account populations separate until exact IDs and filters reconcile:
organizational HLS, Healthcare industry and managed-account scopes are not synonyms.

Retain historical captures. A change from sparse to dense extraction is a method
change, not business recovery; annotate or reset the comparison baseline rather
than emit apparent movement caused by the collector.

## 4. Verify the producer, not an invented fixture shape

Run the real dashboard builder on a small isolated snapshot fixture and validate its
actual output. Do not require fields merely because a hand-written fixture includes
them; derive counts from account rows and compare ID multisets so duplicates remain
visible. Stage output, validate capture identity/date/population, then atomically
publish. Read prior health and reconcile abandoned attempts only while holding the
runner lock; a competing attempt must not overwrite the active owner's state.

Exercise the actual scheduler wrapper against the source. Verify saved snapshot,
served JSON and health agree, prior capture hashes remain unchanged, and failure
paths return nonzero while retaining good data. A cron configuration readback is not
proof of a future scheduled run. Select polling cadence according to the required
latency and source behavior; do not silently equate a weekly success window with
latest available data.

## 5. Verify the chart's semantics

Use source closure flags for completed-period comparisons. Show open-period values
as provisional; blanks are gaps, not zero-height points. Do not connect a line across
unknown periods or claim consecutive decline across missing observations. Arithmetic
and baselines must exclude null without coercion, and missing current closed data
must not silently fall back to an older endpoint presented as current.

Show units, numeric axis ticks, and scale policy. Verify the same real affected
accounts in the browser after publication—not only an aggregate month union.
