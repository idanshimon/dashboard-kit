# Pre-demo surface verification: default state is a defect surface

Verifying a UI for a **live demo or walkthrough recording** is a different job from
verifying it after a code change. The code can be correct, the data can be present,
the API can return 200 with real rows — and the surface still opens WRONG for the
audience, because what a viewer sees is `default filter state × current data`, and
nobody ever verified that product.

Worked cases below are from a governed-SDLC dashboard prepped the night before a
customer demo (2026-08-28). Both defects would have fired on stage.

---

## 1. A route that returns 200 with real data can still open EMPTY

**The API check passes and tells you nothing about the default view.**

```
curl /compliance                       -> 200
curl -X POST /api/ledger/query -d '{"limit":400}'  -> 340 real entries
```

Screenshot of `/compliance`:

> **"No decisions match this query"**
> *Adjust the filters, or run the pipeline so decisions land in the ledger.*

Cause: the view defaults to **`PHI: high` · `Last 24h`**. The data was PHI
`low`/`none` and 9 days old at newest. Both filters are individually sensible
defaults; their intersection with this dataset is the empty set.

This is *not* the empty-surface family in the main SKILL.md (wrong partition, missing
demo guard, hook without fallback, un-populated field). Every layer is healthy. The
defect is **default scope vs. actual data distribution**, and it only exists for a
viewer who lands on the page cold.

**Rules:**

- **Screenshot every tab in its DEFAULT state before a demo** — not the state you
  navigated into while testing. You arrive at views with filters already set from
  your previous query; the audience does not.
- **Check the default filter against the data's actual distribution.** Enumerate what
  the data really contains (`Counter` over the field the default filter uses) and
  compare against the default value. A default that selects a rare or absent class is
  a demo landmine.
- **The highest-risk tab is the one you close on.** The "judge us on one query"
  finale is exactly where an empty state is most expensive.
- **Fix by pre-setting, not by hoping.** Write the required filter state into the
  run-of-show as a setup step performed *before* the room sees the screen, and
  verify it returns rows during setup rather than live.
- URL params may be ignored by the filter component — do not assume `?phi=any`
  works because it looks like it should. Verify the rendered control, or set it by
  hand.

## 2. Narration must match the SCOPE on screen, not the whole dataset

A script written from an API-level aggregate will contradict the KPI strip the
audience is reading, and the contradiction is visible to them in real time.

- Full ledger (all teams, 340 entries): actors genuinely mixed — human principals,
  `autopilot:<team>`, `operator@dashboard`.
- Default UI view (`team-cardiology`, 46 entries) KPI strip:
  **`AUTONOMY SPLIT 100% agent · 0% human`** and **`AUTONOMY EARNED 0% — no
  human-taught precedent yet`**.

Drafted narration said *"some are human, some are the agent."* True of the dataset,
**false of the screen**. The app's own KPI would have called it a lie mid-sentence.

**Rules:**

- **Derive narration from the rendered surface, not from the API aggregate.**
  Screenshot first, write the script against the screenshot.
- **Read the KPI strip specifically** — summary chips are the fastest way to catch a
  script/screen contradiction, and they are what a skeptical viewer checks first.
  (Same family as the caption-vs-canvas rule in the main SKILL.md, applied to spoken
  narration instead of rendered prose.)
- **The honest version is usually the stronger pitch.** "All forty-six were the agent
  on its own, and the system says zero percent human-taught precedent on its own
  front page" is a better governance story than a vague human/agent mix.

## 3. A view can be data-correct and still unusable in a static capture

`/decisions/lineage` rendered correctly — 38 precedent chains, 38 reuse hops, all
counts accurate — but the graph packed into a narrow unreadable column with large
empty regions around it. Fine to explore interactively; useless as a video frame or
a slide.

- **Presentability is a separate axis from correctness.** Judge each captured surface
  as *a frame*, and cut the ones that do not survive it.
- **The header often carries the point without the graph.** Keep the KPI line
  ("38 precedents taught 38 later agent decisions"), drop the canvas.
- Decide this at capture time, not while editing — it changes which views you need.

## Pre-demo checklist

- [ ] Every tab screenshotted in its **default** state (fresh navigation, no
      carried-over filters)
- [ ] Default filter values compared against the data's real distribution
- [ ] The closing/hero tab explicitly confirmed to return rows
- [ ] Narration script written **against the screenshots**, and checked line-by-line
      against the KPI strip of the view it describes
- [ ] Each captured surface judged as a frame; unreadable ones cut with the reason
      recorded
- [ ] Data recency checked and stated — if the newest row is days old, the script
      says "seeded history", never "live telemetry"
