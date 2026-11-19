---
name: powerbi-semantic-model-extraction
description: "Pull and validate data from a Power BI semantic model."
---

# Power BI / Fabric semantic model extraction

## When to Use

MSXI-embedded reports (Fabric 404 / search broken): see `references/msxi-embedded-export.md`.

- You need row-level data out of an internal Power BI report (MSX Insights, Fabric,
  any `app.powerbi.com` / tenant BI portal) instead of clicking Export-to-Excel.
- Someone says "can we automate pulling this dashboard" or "we only have a manual export".
- You are about to build analysis on top of BI *measure names* and have not yet checked
  what those measures actually contain.

## Step 0 — resolve the identity before probing endpoints

1. Check the current runtime's MCP configuration before delegating; a direct Fabric
   client can use Azure CLI authentication without another agent's OAuth store.
2. Inspect `az account show --query '{tenant:tenantId,user:user.name}' -o json` and
   `az account list --all -o json`. Select a cached subscription belonging to the
   report's tenant and intended user, not whichever development account is current.
3. Obtain the token with an explicit account selector:
   `az account get-access-token --subscription <verified-subscription-id> --resource https://api.fabric.microsoft.com --query accessToken -o tsv`.
   Capture it in process memory; never print or persist it.
4. Decode the token payload locally and check `tid`, `aud`, and `exp` before the
   request. This is an identity sanity check, not signature verification; the server
   verifies the signature. Token availability or a future expiry alone proves neither
   the correct identity nor access to the report.
5. Probe the actual model with `EVALUATE ROW("probe", 1)` before a wide extraction.
   On HTTP failure, inspect the service error code and request ID, without logging
   request headers. For `403 FeatureNotAvailable`, check tenant and user first rather
   than immediately changing endpoints or diagnosing an unavailable feature.

Do not repair an unattended collector with `az account set`: it mutates the global
CLI default and another workload can change it back. `--tenant` alone can still use
that default account's user identity; selecting a verified corporate subscription
with `--subscription` selects the cached corporate user without changing the default.
If that identity cannot refresh, request reauthentication explicitly rather than
falling back to another tenant. MSX Insights uses corporate tenant
`72f988bf-86f1-41af-91ab-2d7cd011db47`.

## Step 1 — talk to the endpoint directly

A stdio MCP proxy may depend on another app's OAuth cache and fail to refresh.
Going straight to the HTTP endpoint with an `az` token sidesteps that entirely.
Use `scripts/pbi_direct.py` in this skill after setting `MODEL_ID` in the starter,
plus `PBI_SUBSCRIPTION_ID` and `PBI_TENANT_ID` from Step 0. The helper requires
explicit identity inputs and checks token claims; it handles these response layers:

- **The endpoint answers in SSE.** The JSON-RPC payload arrives on a `data:` line,
  not as a bare body. Parse for it before `json.loads`.
- **Tool results are nested.** The real payload is a JSON *string* inside
  `result.content[].text`. Double-decode.

```bash
python3 scripts/pbi_direct.py schema              # every table, column, measure
python3 scripts/pbi_direct.py csv "<DAX>" out.csv # full result, no truncation
```

Always write query output to CSV/JSON. Printing to stdout truncates mid-object and
you get a `JSONDecodeError` at a byte offset that looks like a server bug and isn't.

## Step 2 — discovery: the portal GUID is not the artifact ID

The GUID in a portal URL (`/User/report/<guid>`) is often a **wrapper**, not the Power BI
artifact. Direct metadata lookup returns `ArtifactNotFound` and the URL resolver rejects
it ("expected `https://<host>/groups/<workspaceId>/reports/<reportId>`").

Resolve the wrapper before querying. In an authenticated embedded report, inspect
only safe SDK fields: `window.powerbi.embeds[0].config.id`, `getPages()` and
`getFilters()`; never dump the whole config because it can contain credentials.
Use the discovered report ID with `GetReportMetadata` to obtain the semantic-model
ID. If no authenticated embed is available, search by report name when the current
API exposes discovery. Discover available tools with `tools/list` rather than
assuming a search tool exists. Record wrapper, report, model and selected-page IDs
separately. For live-state reconstruction, obtain the active SDK page's filters,
visual names/types/titles and each slicer's `getSlicerState()`. “All” does not cancel
row-level security or report exclusions; a last-closed-month pie and a fiscal-year
closed-month matrix need not match. Use actual SDK visual names for browser exports
rather than metadata placeholders such as `generated-pN-vN`. Filter CDP inventory
before printing—only relevant page IDs/titles/URLs, never unrelated tabs or favicons.
See `authenticated-m365-browser-capture` for the browser capture entry point.

When the MCP has no search tool, enumerate by name over REST with the same `az` token
(resource `https://analysis.windows.net/powerbi/api`): `GET /v1.0/myorg/groups` then
`/groups/<id>/reports` (each carries `datasetId`). This covers workspaces you belong
to only — reports shared to you as Power BI apps do not appear, so a miss means "ask
the owner for the link", not "does not exist". Say which workspaces you searched.

Run `EVALUATE ROW("probe", 1)` against each candidate model before planning on it:
`GetSemanticModelSchema` succeeds even on gateway-backed models whose queries fail
with `OnPremiseServiceException`, so a readable schema does not mean queryable data.

## Step 2b — no access to the model: have the owner's agent probe it

When the workspace search (Step 2) is empty and access is a long request, do not wait:
the skill/report will run on the owner's identity anyway. Send the owner a read-only
prompt for THEIR agent (Scout, Copilot) that returns structure only.

1. Smallest test first: table names, main fact table's columns, latest snapshot date,
   "else the exact error". It proves the owner's agent can read the model at all — the
   real gate — before spending their time on a long prompt.
2. Then the full structure prompt: tables (+hidden), columns+types, measure names (+DAX),
   relationships, snapshot column with distinct-date count/min/max, fact-table grain,
   which columns hold the business keys you need, forecast/status value lists, the ID that
   follows one entity across snapshots. Include the rules: read-only, names/structure
   only, no rows/customers/people/amounts, "could not check: <reason>" and continue.
   Suggest `EVALUATE INFO.VIEW.TABLES()/COLUMNS()/MEASURES()/RELATIONSHIPS()`.
3. Expect DAX formulas to come back "not exposed" via agent connectors — you get measure
   names, not logic; ask the owner for definitions of the few that matter (Step 3).
4. Returned files are often sensitivity-label encrypted; read per the `xlsx` skill.
   Parse into a structure JSON plus a findings doc mapping each planned pipeline step to
   what the model already provides — a snapshot fact + change measures can delete whole
   build steps.
5. Before building a mapping/join from CRM to a Finance hierarchy, ask which dataset the
   owner's official recon reads. CRM deals usually carry only the SKU; the hierarchy,
   product splits and the reporting forecast vocabulary are applied downstream. Reading the
   recon's own dataset makes totals match the recon by design and removes the bridge tables.
   To test the CRM side, list real Dataverse field names first
   (`EntityDefinitions(LogicalName='opportunity')/Attributes` via the Web API with an `az`
   token for the org URL) instead of guessing `$select` names — repeated 400s make the MSX
   MCP pause, and its fixed field set hides fields such as `msdyn_forecastcategory`.
6. Answers the owner's agent phrases as "evidence in structure" are inference from names
   (formulas hidden), not confirmation — record them as unconfirmed until a human or a
   numeric test agrees. The decisive test: do the movement buckets plus the revenue-side
   change sum to the headline change measure for one real scope?
7. Send one question/prompt at a time, and when new answers change a filter or metric,
   revise any not-yet-run prompt before the owner runs it — stale prompts waste their run.
   Check which version the owner actually ran (item numbering) before analysing results.
   Keep people's names out of prompts — they get pasted into others' agents and files.
8a. Snapshot/bridge models (Current vs Snapshot measures, Snapshot Version table) return
   absurd totals without the report's slicers: fiscal period + the exact snapshot pair.
   Tells: OU totals in tens of billions, a one-day change of the same size, a "subset"
   measure larger than its parent, change ≈ exactly 50% of current on every row, bridge
   buckets all zero. Do not analyse those numbers — ask the owner for a screenshot of
   their recon's filter pane, then re-run with those exact filters (snapshot IDs are
   yyyymmdd ints), require the agent to return the DAX it ran, and build in sanity checks
   (realistic magnitude, parent ≥ subset, buckets + revenue change ≈ headline change).
   Measure descriptions (not DAX) are often readable — ask for them to get definitions.
8. Keep a project STATUS file (decisions, proven, waiting-on, how to catch up) and verify
   WorkIQ can read the owner's chat (`workiq ask -q "...last messages from <name>..."`) so
   a later session can resume without the user re-pasting screenshots.

## Step 3 — THE CORE DISCIPLINE: a measure name is not its semantics

**This is the reason this skill exists.** Field labels in a BI report are marketing for
the visual, not a contract about the data. In one session two separate measures lied:

| Label | What it looked like | What it actually was |
|---|---|---|
| `GHE Seats Met` | seats actively used | `SUM(...[GHE_Metered_Seats])` — a **billing model flag** |
| `Weekly Usage %` | the assigned-vs-active metric everyone wanted | the literal **string `"TBD"`** for all 250 rows — unimplemented |
| `GHCP Penetration` | seats / total seats | `seats / MAX(total, alt_platform)` — legitimately exceeds 100% |

The first was nearly published as "237K unused seats". The second was a placeholder that
would have been ranked as a real rate.

**Validate every measure before building on it:**

1. **Probe first, extract second.** Pull 50-250 rows of the candidate measures alone.
2. **Look at the distribution, not the mean.** Bimodal (mass at exactly 0 and exactly
   100%) means a *flag*, not a rate. A genuine rate is a smooth curve.
3. **Count non-null.** Many named measures are empty at your chosen grain. Report
   `n non-null / n rows` for each before promising anything.
4. **Check type and value together.** Text such as `"TBD"` is a placeholder, but
   formatted numeric text can still represent money or a rate. Probe representative
   cells and the format string; do not reject or trust a measure based on type alone.
5. **Reverse-engineer the formula and test it.** Hypothesise the arithmetic, compute it
   from the raw columns, and compare row by row. State the fit ("265 of 267 exact,
   2 rounding"), not a vibe.

**The authored DAX is usually NOT retrievable.** `GetSemanticModelSchema` omits
`Expression`; `INFO.VIEW.MEASURES()` returns `Expression = null`; the dependency DMV
errors. So what you establish is a **behavioural equivalence**, not the source. Label it
that way, and note it must be re-verified if the report changes. Getting the literal
expression needs XMLA/Build access or the PBIX from the owner.

## Step 3b — a measure VALUE is not a number either

Distinct from Step 3 and, if anything, more dangerous: even after you have validated what
a measure *means*, the endpoint may hand you its value as a **pre-formatted string**.

```
'$146'   '$1,365,204'   '45.8%'   '(1,200)'
```

`float('$146')` raises. If your coercion helper returns `None` on failure and the caller
defaults to `0.0`, **every currency value in every extract silently becomes zero** — no
exception, no warning, no log line. A real $133,253 figure reads as `0`, the ranking built
on it is completely wrong, and it looks entirely plausible because zeros are a legitimate
value in that column.

When an expected rule produces no findings, inspect raw cell types and parsed distributions before concluding the phenomenon is absent; parser defaults can make valid currency look like legitimate zeros.

```python
def num(v):
    """Coerce a BI cell to float. Currency arrives pre-formatted as a STRING."""
    if v is None or v == '':
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace('$', '').replace(',', '').replace('%', '')
    if s.startswith('(') and s.endswith(')'):        # accounting negative
        s = '-' + s[1:-1]
    try:
        return float(s)
    except (TypeError, ValueError):
        raise ValueError('non-numeric BI cell') from None
```

Reject booleans and non-finite numeric results at the validation boundary as well.
Only actual source null/empty cells may return `None`; parser failures must not
become indistinguishable from source blanks.

**The detection heuristic, and it generalises well beyond BI:**

> When a numeric column comes back **all zero**, suspect the parser before you conclude
> the source is empty.

"No data" and "data I failed to parse" are indistinguishable downstream and have opposite
remedies. Assert non-zero mass on at least one known-good key — pick an entity you *know*
has activity and check its value survived the round trip. Type-check the raw cell too:
`ExecuteQuery` reports column types, and a `String` type on a money column is the tell
before you have parsed a single row.

## Step 3c — two series rarely share a calendar

When you correlate two measures over time, check their **period axes actually overlap**
before comparing. In one model AI-credits data ran a month ahead of the companion spend
measure, so a naive first-vs-last comparison pitted a *partial current month* on one
series against a *complete prior month* on the other. The comparison never matched, and
the failure was silent — the rule simply produced no findings, which reads identically to
"the phenomenon does not occur".

```python
shared = sorted(set(series_a) & set(series_b))
if len(shared) >= 2:
    first, last = shared[0], shared[-1]
    # ... and name the window in the output: f'over {first}..{last}'
```

Report the comparison window in the finding itself. A conclusion whose time basis is
invisible cannot be audited, and "no results" is the one output that never prompts anyone
to look closer.

## Step 3d — investigate freshness before reassuring the user

When the user says dates are not advancing, query the source for the named companies
and newest periods before explaining it as reporting lag. Separate four facts:
collection attempt time, source refresh time, source period closure, and each
account/metric's observed coverage. A successful recent pull proves only the first.
Use source `IsClosed`/`RelativeFM` and visual filters to explain closed-month views;
do not infer closure by dropping the last plotted point. Source blank means its cause
is unknown, not proven inactivity or delayed ingestion. Label the UI “collection
checked” separately from source coverage; show per-metric last reported month and
current-period state. Do not use a union of two metrics' month ranges as proof both
are current. Put explicit units and numeric ticks on charts and disclose independent
per-account scales.

For the live-probe recipe and collection acceptance checks, read
`references/source-coverage-and-freshness.md`. Do not claim an end-to-end repair from
probe results or synthetic tests: exercise the actual scheduled entry point and read
back the published capture/health identity.

## Step 4 — inventory the whole surface before choosing a slice

A single report tab's visible columns are a tiny fraction of the model. One model that
looked like "about 37 fields" had **415 measures**; an extractor built from the visible
tab was pulling **6 of them**. The user caught this, not the agent.

Run `schema` and grep the measure list by *function* before deciding what to extract:
churn/`MoM`/`Change`, pipeline/`QP`/`CP`/`No pipe`, forecast/`Outlook`, usage/`active`.
Then probe those candidates per Step 3 — many will be empty.

### Completeness and corrective questions

- State the inspected numerator, denominator and boundary unprompted: captured pages versus inventoried pages, consumed measures versus live schema, populated rows versus scoped population. A successful subset is not complete coverage.
- Check your own configured clients and current identity before routing extraction to another agent or manual export; an already available read path may eliminate the handoff.
- Treat terse questions about completeness, access or certainty as verification requests. Recheck source semantics, effective filters, implementation wiring and privacy boundaries before replying; do not defend the earlier claim.

## Pitfalls

- **Silent row-cap truncation — the cap is a round number, and that is the tell.**
  A `SUMMARIZECOLUMNS` over accounts × months quietly returned ~30 of 255 accounts with
  no error. On a later pull the same endpoint returned **exactly 250 rows** covering 59
  of 250 keys. Symptom: a plausible-looking result that is simply short; a result whose
  length is exactly 250 / 500 / 1000 is a cap, not a coincidence.

  Narrowing the window and dropping all-zero rows buys headroom but does not remove the
  ceiling. Any pull wider than a few hundred rows must **batch by explicit key groups**,
  and the batcher must raise if a batch *still* comes back at the cap — otherwise you
  have rebuilt the same silent truncation one level up:

  ```python
  ROW_CAP = 250   # observed hard cap, enforced with no error and no flag

  def run_dax_paged(template, keys, batch=30):
      """Choose batch so keys × maximum periods stays BELOW the row cap."""
      if '{key_filter}' not in template:
          raise ValueError('missing {key_filter}: batching would repeat the full query')
      headers, rows = None, []
      for i in range(0, len(keys), batch):
          chunk = keys[i:i + batch]
          vals = ', '.join(f'"{k}"' for k in chunk)
          h, r = run_dax(template.replace(
              '{key_filter}', f"TREATAS({{{vals}}}, 'Dim_Account'[TPID])"))
          if headers is not None and h != headers:
              raise RuntimeError('batch schema changed')
          headers = h
          rows.extend(r)
          if len(r) >= ROW_CAP:                     # never assume it fit
              raise RuntimeError(f'batch of {len(chunk)} still hit the cap')
      return headers, rows
  ```

  **Discover and count the population independently before batching every dimension.**
  Under the exact report filters, a one-row `CONCATENATEX` TPID list plus
  `COUNTROWS` avoids truncating the population lookup itself; validate distinct IDs
  against that count. Do not derive the population from an already-capped seat or
  credits result. Batch account rows as well as each time series. An inclusive
  relative-month range from -6 through 0 contains seven periods, so size batches
  against seven, not six.

  For account/month coverage, add `"Present", 1` to `SUMMARIZECOLUMNS` so blank
  measures retain rows, and validate the complete expected account × period grid—not
  just distinct accounts. Do not filter `[Measure] <> 0`: that removes both blanks
  and zeros and makes an updated company look stale. Exclude blank calendar members
  explicitly with `NOT ISBLANK`; DAX blank relative-month values can satisfy a
  numeric range containing zero. Preserve source blank, reported zero and reported
  nonzero separately; an absent expected row is a collection defect, not a source
  blank. Persist period closure, source refresh fields, observed coverage, filters
  and query fingerprints. Keep legacy sparse captures unchanged and label their
  coverage unknown. A changed extraction population is not adoption growth.
- **Report-context filters are load-bearing.** Point-in-time measures (`LCM ...`) can
  return NULL unless the report's own filter is reproduced, e.g.
  `TREATAS({-1}, 'Dim_Calendar'[RelativeFM])`. Read the export's "Applied filters"
  footer and replicate it, or you get nulls that look like missing accounts.
- **Validate time-filter sensitivity before plotting history.** A latest-closed-month measure can repeat the current value for every grouped historical month; returned calendar rows do not prove historical observations. Probe a month-sensitive counterpart, cross-check its closed-month variant and reconcile its latest endpoint to the point-in-time measure. In the developer-services model, use `[GHCP Seats]` / `[GHCP Seats (Closed Mths)]` for the monthly axis rather than `[LCM GHCP Seats]`.
- **Null is not zero, and an unparsed string is not zero either.** Treating missing seat
  data as `0` produced "lost 2,430 seats (3240% of estate)". Separately, currency values
  arrive as formatted strings and a failed coercion defaulting to `0.0` zeroed an entire
  extract silently — see Step 3b. If a denominator's inputs are all null, emit
  `"(estate size unknown)"` — never a fabricated percentage.
- **A rule that fires on nothing is a finding, not a result.** Zero matches reads as
  "the phenomenon does not occur" and is indistinguishable from a broken comparison,
  a zeroed column, or misaligned time axes. Before reporting "we looked and it isn't
  happening", verify the rule fires on a synthetic fixture that *should* trip it.
- **Two populations rarely reconcile.** An aggregate export (280 accounts, one filter
  set) and a per-key extract (277, another) are different populations. Do not compute
  ratios across them; re-pull under one filter state.
- **Don't quote a derived headline number until Step 3 passes.** Especially one that
  would go in front of a customer or leadership.
- **A designed-but-unwired second score reads as a principled empty state.** If the
  artifact reports "0 attributed" because nothing ever loads the evidence file, that
  looks identical to "we correctly refuse to guess". Grep the field for a hardcoded
  `None` before believing the contract is implemented — see
  `references/signal-scoring-engine-design.md`.

## Protecting the extract: a .gitignore in a non-repo protects nothing

Account-level BI actuals usually carry an explicit confidentiality banner
("must not be shared with individuals lacking appropriate permissions"). Writing
a `.gitignore` feels like discharging that obligation. It does not — **if `git
init` has not run, the file is inert decoration.**

Caught live: a project had a correct-looking `.gitignore` listing `data/`, and
every confidential extract was still unprotected because the directory was not a
repo. `git check-ignore` silently returns nothing outside a repo, so a casual
check *appears* to pass.

Verify by asking git what it would actually commit, inside an initialised repo:

```bash
git init -q && git add -A
git status --porcelain | awk '{print $2}' | sort     # what WOULD be committed
for f in <each confidential path>; do
  git check-ignore -q "$f" && echo "PROTECTED $f" || echo "EXPOSED  $f"
done
```

Patterns worth having, because extracts land in more places than one directory:

```gitignore
data/
dashboard/data.json
snapshot_*.json
*-tpid_*.csv          # any per-key extract, wherever it lands
*_20??-*.csv          # dated exports
evidence.json         # hand-maintained attribution notes, if the project has them
```

Do this **before** the first extract lands, not after — and treat "did anything
confidential become committable?" as a verification step in its own right, at
the same level as row counts.

Note that a hand-maintained annotation file (customer-attributed competitive
intelligence, analyst notes) is often *more* sensitive than the machine extract,
and is easy to miss because it wasn't produced by the pipeline. Enumerate inputs
as well as outputs when writing the ignore rules.

- Row count vs expected population, stated explicitly.
- **Non-zero mass on a known-good key.** Pick an entity you *know* has activity and
  confirm its value survived parsing. An all-zero numeric column is a parser failure
  until proven otherwise — see Step 3b.
- **Distinct key count vs expected population** — 250 rows can be 59 keys × 4
  months. A result length that is exactly 250/500/1000 is a cap, not data.
- Non-null count per measure, stated explicitly.
- One reverse-engineered formula checked row-by-row with the fit ratio quoted.
- Which filters were applied, verbatim.
- What you could NOT retrieve and why (a clean negative is a real result).
- **What fraction of the surface you covered** — "16 of 415 measures", "1 of 9
  tabs". If you cannot name the denominator, you have not finished Step 4.
- **For every caveat you are about to publish as a permanent limitation, whether
  the model already carries the measure that answers it.** Grep the schema before
  writing "we cannot distinguish X" — see the confound section in
  `references/signal-scoring-engine-design.md`.
- **Whether any confidential extract is git-committable**, checked inside an
  initialised repo (see above) rather than assumed from a `.gitignore`.

## Extending a report-backed dashboard

1. Inspect the existing collector queries, snapshot fields and rendered detail before proposing new acquisition; a source field discovered in the browser may already refresh through the thin existing lane.
2. Separate export-label visibility, metadata references, populated values, validated semantics and scheduled producer support. Report each denominator independently; overlapping export labels and metadata targets are not additive unique measures.
3. Map every observed field occurrence to exact provenance and a feature dependency, with readiness and a checkable gate. Preserve duplicate CSV headers by column position, exact Unicode/trailing spaces and populated anonymous columns; display normalization must not change identity.
4. Deliver a schema-only catalog and field-to-feature guide, with observed samples/coverage profiles kept in verified ignored storage. Distinguish opportunities already supportable by approved queries from source-only extensions and blocked derived claims.
5. Audit data refresh separately from source-contract maintenance: verify the registered script, enabled field coverage, publication identity, retry/deadline behavior and actual owner notification delivery. Browser reload is not collection; a recent capture is not new source data; a script-only job is not competitor research or self-maintaining analysis.

For the SDK capture and positional-catalog recipe, read `references/browser-report-surface-audit.md`.

## Support files

- `scripts/pbi_direct.py` — minimal direct client: SSE unwrap, schema dump, DAX→CSV.
- `scripts/probe_measures.py` — **run this on every extract before building on it.**
  Automates Steps 3 and 3b: flags string-typed placeholders (`"TBD"`), measures empty at
  your grain, bimodal distributions that are flags rather than rates, boolean-as-count,
  percentages exceeding 100, and **pre-formatted currency strings whose consumer will
  either raise or silently zero the column**. Exits 1 so it can gate a pipeline.
  `python3 probe_measures.py extract.csv --key-cols 2`
- `references/signal-scoring-engine-design.md` — turning validated measures into a ranked
  list that holds up: the two-score contract, materiality floors, null-is-not-zero,
  per-entity baselines (median+MAD), and enumerating benign explanations before you
  present a signal as a conclusion.
