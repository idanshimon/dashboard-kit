# Building a defensible signal-scoring engine on BI telemetry

Companion to the extraction skill. Once you have validated measures, this is how to turn
them into a ranked list a seller or exec will trust — and how not to.

Learned building a competitive-displacement scorer over a BI semantic model, 2026-08.

## The two-score contract

When telemetry can show *that* you are losing an account but not *who* took it, emit
**two independent scores that are never merged**:

| Score | Moved by | Never moved by |
|---|---|---|
| `displacement_risk` | your own telemetry — decay shape, structural gaps | anything |
| `named_competitor_confidence` | ONLY externally-sourced evidence (artifacts, customer-confirmed, CRM fields, public) | telemetry, ever |

The seductive error is reading a consumption collapse as "vendor X took it." A merged
score makes that error structural and invisible.

**Enforce it with a test, not a comment.** Assert the telemetry scorer cannot emit a
vendor name for any input, and that a billing-model field cannot change a score. A prose
rule in a docstring gets edited away; a failing test does not.

### The second score must actually be WIRED, not just designed

The failure mode is subtle and survives review: the contract gets documented, the
schema gets written, the field is emitted in the payload — **hardcoded to `null`**,
because nothing ever loads the evidence file. Every artifact then truthfully reports
"0 named competitors", which reads as a principled empty state rather than a
missing feature. It shipped that way here and only surfaced on a later pass.

Check for it directly: `grep -n "named_competitor" scorer.py`. If the only hits are
a literal `None`/`null` assignment, the second half of the contract does not exist.

When you do wire it, the loader is the security boundary — treat malformed input as
fatal, not as something to coerce:

- **Raise on unknown enum values and missing required fields.** The downstream harm
  is an unsupported accusation reaching a customer conversation; a silently
  downgraded record is worse than a crash.
- **Drop expired records at load.** Observations go stale — logos outlive
  deployments. Carry an `expires` date and honour it.
- **Support an explicit `contradicted_by` field.** A later observation that disproves
  an earlier one should suppress it while leaving the reversal visible in the file's
  history, rather than being silently deleted.
- **Bound corroboration.** Independent evidence *types* should add confidence; ten
  copies of the same type must not. `min(100, best + k * (len(distinct_types) - 1))`.
- **Weight by scope.** One developer on a trial is not an enterprise rollout —
  multiply by `{enterprise: 1.0, team: 0.85, pilot: 0.7, individual: 0.5}`.

Prove the separation with two assertions that must both hold: an entity with
catastrophic telemetry and no evidence scores **0** on attribution, and an entity with
clean telemetry and strong evidence scores **high** on attribution. If either fails,
the scores are coupled somewhere.

Ship a documented `evidence.example.json` template rather than an empty real file —
it makes the intended workflow obvious, and it is safe to commit. **The real
`evidence.json` is usually the most sensitive file in the project** (named
customer-attributed competitive intelligence); add it to `.gitignore` at the same
time you create the loader, not later.

## Rules that keep a ranking honest

**Materiality floors on every structural rule.** A rule like "competitor seats exceed both
our platforms" fired on an account with 1 seat vs 2 — technically true, operationally
noise. Gate on an absolute count *and* a non-zero denominator. Without both it fires on
empty accounts and poisons trust in the whole list.

**Null is not zero, and the reader must see the difference.** Treating missing data as `0`
produced "lost 2,430 seats (3240% of estate)". If the denominator's inputs are all null,
print `(estate size unknown)`. An admitted gap beats a fabricated percentage.

**Score the UNION of dimensions.** Scoring only entities with metric-A history silently
dropped 22 accounts carrying a strong metric-B signal and no A row at all — the exact
profile being hunted. Union the key sets; absence in one dimension is not absence overall.

**Separate "never had it" from "had it and lost it".** Different plays entirely — a landing
motion vs a defence motion. Distinct classifications, never one bucket.

**Learn the baseline per-entity from its own history.** Median + MAD, not mean + stdev: a
single spike month must not define "normal". A book-wide constant threshold is useless
across entities spanning three orders of magnitude.

```python
def baseline(series):
    vals = [v for v in series if v is not None]
    if len(vals) < 2:
        return (vals[0] if vals else 0.0), 0.0
    s = sorted(vals); n = len(s)
    med = s[n//2] if n % 2 else (s[n//2-1] + s[n//2]) / 2
    devs = sorted(abs(v - med) for v in vals)
    mad = devs[n//2] if n % 2 else (devs[n//2-1] + devs[n//2]) / 2
    return med, mad * 1.4826   # scaled to be sigma-comparable
```

**Floor the classification by the worst single finding.** A purely additive score buries
severity. One `critical` finding worth 40 points landed below a `high` threshold of 45,
so an entity losing 2,430 seats classified as `watch` while one that tripped two trivial
rules classified `high`. Sum for the *number*, but let the worst finding set a floor on
the *class*:

```python
worst = {x['severity'] for x in findings}
rank = ['stable', 'watch', 'high', 'critical']
if 'critical' in worst and rank.index(cls) < rank.index('high'):
    cls = 'high'
```

Symptom to watch for: the item with the largest absolute magnitude is not near the top.

**Rank on percentage when the denominator is known, magnitude when it is not.** A rule
gated only on \"≥10% of estate\" goes silent exactly where the estate is unmeasurable —
which is often the largest entities. Carry both paths explicitly.

**Carry the reasons, not just the number.** Every score should ship the list of findings
that produced it. A seller who cannot see *why* an account ranked 93 will not act on it.

## Enumerate the benign explanations in the artifact

A signal is not a conclusion. For any consumption decline, list what else it could be
and say plainly which you have excluded:

- **Partial reporting period** — the current month may be truncated
- **Allocation top-up** — an *overage* metric goes to zero when the customer buys MORE
- **Promo / pricing change expiry** — a scheduled step-change unrelated to competition
- **Migration to another of your own products** — spend leaving one meter is not spend
  leaving you

Until each is excluded, every score carries an unexcluded alternative explanation.
Put that in the deliverable's limits rather than burying it. Display open periods as
provisional and exclude them from closed-period decline comparisons by default;
use the source calendar's closure flag, not chart position. Only apply a partial-period
normalization or discount if the implemented method has been tested and is identified
in the output. Do not describe a legacy engine's discount as present in the live scorer.
Require observed comparable endpoints; a source blank must not become zero, an older
endpoint must not masquerade as current, and gaps must break consecutive-decline claims.

### Better: MEASURE the confound instead of disclaiming it

Listing a benign explanation is the floor, not the ceiling. Before writing "we cannot
distinguish X", grep the measure inventory for X — the model often already carries it.

Worked example: the standing caveat was *"declining spend on meter A may simply be
migrating to product B, and the engine cannot tell."* A grep of the schema found
`AI Foundry ACR ($)` populated across 105 of 255 accounts. The caveat was answerable all
along; it had been re-published in three artifacts as a permanent limitation.

Once measured, encode it as a **benign finding** — a first-class severity that carries
its own evidence:

```python
if c_drop > 0 and f_gain >= c_drop * 0.5:
    found.append({
        'kind': 'alt_product_offset', 'severity': 'benign',
        'detail': f'meter A fell ${c_drop:,.0f} while product B rose '
                  f'${f_gain:,.0f} — spend likely MOVED, not lost',
        'metric': 'B ACR ($)', 'value': f_last, 'baseline': f_first,
    })
```

Three properties that make this work, each of which was wrong on the first pass:

- **Annotate, never suppress.** The decline stays in the findings list. A seller needs
  to see *both* facts; deleting the decline replaces one distortion with another.
- **A benign finding must actively DISCOUNT the score, not merely add zero.** Weighting
  it `0` leaves the account ranked identically to one with no explanation at all —
  which is the entire distinction you just built. Apply a multiplier
  (`s = int(s * 0.4)`), and prove it: identical consumption data scored **10 with the
  offset vs 25 without**.
- **Exclude `benign` from the worst-finding class floor.** The floor exists to stop a
  lone `critical` being under-ranked; if `benign` can trip it, the mechanism inverts and
  a *good* explanation escalates the account.

Guard the absent case too: no data for product B must not read as "B did not absorb it."
Missing is unknown, not zero — assert it in a test.

**Distinguish "we cannot detect this" from "we looked and it is not happening."** After
wiring the rule it fired on zero real accounts. That is a much stronger answer to the
person who raised the confound — but only if you check *why* before reporting it, since
"no accounts match" and "the two inputs cover different periods" look identical from the
outside.

That check was worth running: **zero matches was a bug, twice over.**

1. **The time axes did not overlap.** Meter A's series ran a month ahead of product B's,
   so first-vs-last compared a partial current month against a complete prior one.
   Intersect the period keys and compare only shared months — then name the window in
   the finding (`over 2026-06..2026-07`) so the basis is auditable.
2. **Every value in both series was zero** because currency arrived as pre-formatted
   strings and the coercion helper returned `None` on failure into a `0.0` default. See
   Step 3b of the parent skill.

With both fixed the rule fired, and the answer inverted completely: the two flagship
accounts showed the alternative product *absorbing* the decline — one had meter A fall
$7.7K while product B grew **$1.75M**. The headline went from "spend is collapsing" to
"spend moved, and it did not leave us."

**The generalisable rule: a rule that matches nothing is a finding to investigate, not a
result to report.** Zero matches is the single most under-scrutinised output in any
scoring engine — it produces no rows to eyeball, triggers no alert, and reads as a clean
negative. Before publishing "we looked and it isn't happening", run the rule against a
synthetic fixture that *should* trip it. If the fixture does not fire, the rule is broken,
not the world.

## Reporting shape

State, in the artifact itself:

- what it **delivers** and what it **does not** — as two adjacent columns, not a footnote
- which claims are established vs **not yet established**
- the source, filter state, and as-of date
- the confidentiality classification if the inputs are account-level actuals

An analysis that advertises its own limits gets used. One that oversells gets discovered.
