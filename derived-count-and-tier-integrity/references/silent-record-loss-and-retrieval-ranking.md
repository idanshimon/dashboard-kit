# Silent record loss, CLI JSON extraction, and retrieval ranking

Field notes from building a local index over a markdown knowledge vault plus a
live CRM CLI. Three defect families, all sharing the Defect-3 signature: **the
output looked plausible, nothing threw, and the number was wrong.**

---

## 1. The block splitter that dropped 90% of records

A persona directory showed a `Role` column that was blank for 94% of rows. The
instinct is to add a column or backfill the field. The actual bug was upstream
and far larger.

```python
# WRONG - splits on separators, then takes ONE record per chunk
blocks = re.split(r"\n---+\n", text)
for b in blocks:
    m = NAME_RE.search(b)      # <- finds only the FIRST person in the chunk
    if not m:
        continue
```

The corpus did not use separators consistently:

```
one source file:   69  "**Name:**" lines
                   19  "---" separators
```

Every record after the first in each chunk was **silently discarded**. Corpus
wide: 579 source blocks produced 55 parsed records. No exception, no empty
result, no warning — just a directory that was quietly missing nine of every
ten people, and a column that read as "this data was never filled in".

```python
# RIGHT - split on the RECORD MARKER itself; separators are decoration
marks = [m.start() for m in re.finditer(r"^\*\*Name:\*\*", text, re.M)]
bounds = marks + [len(text)]
blocks = [text[bounds[i]:bounds[i+1]] for i in range(len(marks))]
```

**Rule: split on the thing that defines a record, never on the thing that
visually separates them.** Separators are authored by humans and are optional;
the record marker is structural. Any `re.split(...)` followed by a `.search()`
that takes one match per chunk is this bug waiting to happen.

### The gate that catches it

Count the record marker in the SOURCE and compare to rows landed. This is cheap
and it would have fired immediately on 55/579:

```python
src = sum(len(re.findall(r'^\*\*Name:\*\*', open(f).read(), re.M))
          for f in glob.glob(SOURCE_GLOB))
got = con.execute('select count(*) from persona').fetchone()[0]
print('OK  personas %d/%d' % (got, src) if got >= src * 0.75
      else 'FAIL only %d of %d blocks parsed - the splitter is dropping records'
           % (got, src))
```

Use a ratio (75%), not equality — legitimate filtering (placeholders, malformed
rows) removes some. Equality produces a gate that is always red and therefore
ignored.

### Two follow-on defects the recovery exposed

Recovering the dropped records surfaced bugs that had been hidden by the small
sample. **Expect this**: a parser fix that multiplies your row count will
expose every downstream assumption that happened to hold on the subset.

**Placeholder values counted as data.** Unfilled template rows (`*To be
documented*`, `(TBD)`, `(TBD - App side)`) parsed as real values. But a
substring search for `TBD` is too aggressive — `Senior executive (title TBD)`
carries genuine signal. Match the WHOLE string:

```python
if role and (PLACEHOLDER.match(role)
             or re.fullmatch(r"[\(\[]?\s*(tbd|to be documented|unknown|n/?a)"
                             r"\s*[-\u2014:]?[^)\]]*[\)\]]?\.?", role, re.I)):
    role = None
```

**Order of cleanup steps changes the result.** Source form was
`**Name:** Erik Golden \u2b50 Account Lead`. Stripping the star FIRST welded the
role label onto the surname, producing entries like `Tianna Umann Contact`.
Split AT the marker instead and treat the remainder as a label:

```python
clean = re.split(r"[\u2b50\U0001f525]", clean)[0].strip()
clean = re.sub(r"\s+(Key\s+Contact|Account\s+Lead|Contact)\s*$", "",
               clean, flags=re.I).strip()
```

The merge is the proof: two rows for one person collapsed to one with the
correct meeting count. **Verify a de-duplicating fix against a name you know
well** rather than trusting the aggregate count moved in the right direction.

---

## 2. Two entity tables that never joined

An index carried both `person` (415 rows, derived from meeting attendance) and
`persona` (89 rows, derived from documented profiles). Only 15 names appeared in
both. Every UI surface picked one table and therefore showed half a human: the
directory listed attendees with no role; the detail page listed profiles with no
meeting history.

**When two tables describe the same real-world entity, the low overlap is the
bug report.** Merge on a normalised key into one table, and keep a `sources`
column recording which feeds contributed.

One genuine finding hid inside it, worth separating from the defect: low overlap
was *partly real*, because the two feeds describe different populations (one
recorded the customer side, the other recorded who attended internal meetings).
**Confirm which part of a discrepancy is a bug and which is a fact about the
domain before rewriting the join** — same discipline as Rule 0 in the parent
skill.

A `LEFT JOIN`-style rollup guarded on a nullable field silently zeroes counts:

```python
# WRONG - attendees at records with no customer attribution lose their count
if row["customer"]:
    c["n_meetings"] += 1

# RIGHT - count the event; attribute it only when attribution exists
c["n_meetings"] += 1
if row["customer"]:
    c["by_customer"][row["customer"]] += 1
```

Symptom was 95 contacts showing `0 meetings` while attendance rows plainly
existed for them. Gate on it: `count(*) where n_meetings = 0 and documented = 0`
should be zero.

---

## 3. Extracting JSON from a CLI that wraps it in chrome

A `--json` flag does not mean the process emits only JSON. Observed real output:

```
Fetching deal team opportunities...

On deal team for 20 opportunities:

[ { ... } ]

─ 3 CRM queries in 2.0s (avg 670ms/req) ─
```

Chrome on **both** sides. The common fix — slice from the first bracket to the
end of the string — still fails to parse because of the trailing footer. Walk
inward from both ends:

```python
starts = [i for i in (out.find("{"), out.find("[")) if i >= 0]
ends   = [i for i in (out.rfind("}"), out.rfind("]")) if i >= 0]
if not starts or not ends:
    return None
body = out[min(starts):max(ends) + 1]
```

Also: `min()` over the raw `find()` results is wrong when one delimiter is
absent, because `find` returns `-1` and `-1` wins the `min`. Filter the `-1`s
before reducing.

**Always print the parse failure.** A bare `except json.JSONDecodeError: return
None` turned a fixable framing problem into "no data returned", which reads as
an auth or connectivity issue and sends you debugging the wrong subsystem.

### Verify the subcommand surface before writing the collector

A collector was written against a `pipeline` subcommand inferred from a sibling
API's shape. **No such subcommand existed** — the real surface was `my-opps` and
`my-milestones` with a completely different record schema. Cost: a full rewrite.
Run `<tool> --help` and dump one real record's keys before designing the table.

### Currency arrives as a formatted string

Same source returned both shapes for money: a numeric field and
`"_acrFormatted": "$30,000"`. `float("$30,000")` raises, and a bare
`try/except` around it **silently zeroes real revenue** — the collector reported
`$0` total while the upstream API reported millions.

```python
def money(v):
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^0-9.\-]", "", str(v))
    return float(s) if s not in ("", "-", ".", "-.") else 0.0
```

**Cross-check the total against an independent path.** The collector's
`$3,739,645` was confirmed by a separate API surface reporting the same figure.
Two independent derivations agreeing is what upgrades "it parsed" into "it is
right" — the coherence check from the parent skill, applied to a whole pipeline.

### Field names in enterprise CRM payloads are not the friendly ones

Raw OData exposes `_msp_opportunityid_value`, not `oppId`, and pairs every field
with a `@OData.Community.Display.V1.FormattedValue` twin. Read the raw value,
fall back to the formatted one:

```python
def ms_field(m, *names):
    for n in names:
        if m.get(n) not in (None, ""):
            return m[n]
        fmt = f"{n}@OData.Community.Display.V1.FormattedValue"
        if m.get(fmt) not in (None, ""):
            return m[fmt]
    return None
```

---

## 4. Hybrid search ranking: RRF defaults that silently do nothing

Reciprocal-rank fusion over keyword + vector results was returning `CHANGELOG`
and `copilot-instructions` as the top hits for *"who is blocking the rollout"*.
Three defects, none of which raise:

**`k` was sized for a different corpus.** The textbook `k=60` over only 40
candidates compresses every score into `[1/60, 1/99]` — a 1.6x spread across
the entire ranking. Rank position stops mattering. Use `k` on the order of the
candidate pool (`k=10` for 40 candidates), and sanity-check the score spread
between rank 1 and rank N.

**No consensus bonus.** Plain RRF sums, so a document found twice deep in ONE
list scores the same as one found near the top of BOTH. Agreement between two
independent retrievers is the strongest signal available — reward it:

```python
if len(seen_in[rid]) == 2:      # found by keyword AND vector
    score[rid] *= 1.6
```

**No quality floor, and no boilerplate damping.** Vector search always returns
`limit` results, however bad. Below a similarity floor a "hit" is topic drift,
not a match. Separately, files like `CHANGELOG`, `README`, `index`, `_moc`,
`copilot-instructions` match almost any query on topic alone and must be damped
or they dominate:

```python
SEM_FLOOR = 0.42
s = [r for r in s if (r.get("score") or 0) >= SEM_FLOOR]
if BOILERPLATE.search(ident.rsplit("/", 1)[-1]):
    score[rid] *= 0.35
```

**Return WHY a result ranked.** Emitting `matched: "both" | "fts" | "sem"` on
each hit makes fusion behaviour inspectable instead of a black box, and turns
"the search feels wrong" into a diagnosable claim.

### Evaluate retrieval on real queries, per mode, before and after

The only way to know a ranking change helped is a fixed query set run against
each mode. Keyword and vector fail on *opposite* query shapes:

```
"where are customers worried about compliance"
  fts       0 hits          <- keyword finds NOTHING
  semantic  30 hits         <- correct documents, zero shared keywords

"who is blocking the rollout"
  semantic  CHANGELOG       <- topic match, useless
  fts       real meeting    <- better
```

This is the case FOR hybrid, and also the reason its fusion needs tuning rather
than defaults. Keep the query set in the repo and re-run it on every ranking
change.

---

## 5. Retrieval that exists but is not wired to the consumer

The sharpest finding of the session, surfaced by a user question rather than a
test: the app had a working semantic index **and** an embedded assistant, and
they were never connected. The assistant received only a working-directory
path — no embeddings, no retrieved documents, no derived facts.

It still produced good answers, because the agent re-read the files itself. So
nothing looked broken. But it was slow (~30s), and it structurally could not
surface anything **derived** — facts computed by the index that exist in no
file.

**When an app contains both a retrieval layer and an LLM consumer, verify the
call path actually carries context.** Read the request handler and confirm
retrieved documents are in the payload. Plausible answers from an agent with
filesystem access are not evidence that your RAG is wired up.
