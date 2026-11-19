---
name: paged-list-count-integrity
description: "Pagination, search, and list counts that lie."
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [pagination, ui, api, testing, data-integrity]
    related_skills: [empty-view-diagnosis, ui-visual-verification, verifying-fixes-actually-executed]
---

# Paged list count integrity

A list view that shows `Showing 50 runs` is making a claim it usually cannot
support. This skill covers the three bugs that hide there, in the order they
bite, and the specific reason a green test suite misses two of them.

## When to Use

- A list, table, feed, or dashboard shows a suspiciously round count (50, 100, 1,000)
- The user says "why am I only seeing N" or "didn't we fix pagination"
- You are adding `offset`/`cursor`/`search` to an existing list endpoint
- You are reviewing a list endpoint that returns a bare array instead of an envelope


## The three bugs

### 1. The ceiling — items beyond page one are unreachable

The endpoint takes `limit` but no `offset`. Everything past the first page is
unreachable by any means: not scrolling, not filtering, not a URL parameter.

Check: does the API accept an offset/cursor at all? Does the UI ever send one?

### 2. The uninterpretable count — page size masquerading as a total

The footer renders `items.length`, which is the length of the **fetched page**.
With 214 records it says "50". With exactly 50 records it also says "50". The
operator cannot distinguish *a slice* from *everything*, which is the same
defect class as an empty view that renders as healthy.

**Fix:** return `total` alongside `count`, and render a range: `Showing 1–50 of 214`.

**Corollary — audit EVERY count on the page.** After fixing the footer, other
surfaces still derive from the page array: KPI tiles, filter-bar summaries,
sidebar badges, chart headlines. The page then contradicts itself, and the
original complaint is often still on screen a few pixels away. Grep the whole
view for `.length` on the items array.

### 3. Page-local search — a confident empty result

If search filters the already-fetched page, a record at position 173 returns
nothing. Worse, it returns nothing *authoritatively*, so the user concludes the
record does not exist. An empty result that looks correct is worse than an
error.

**Search must be server-side, applied over the full scanned window before
paging.** This is not an optimization; page-local search is simply wrong.

## Honesty when the scan is bounded

If you scan a bounded window rather than the whole table, `total` is a **floor**,
not a count. Return a `truncated` flag and render it: `214+`, plus "the archive
holds more". Never present a bounded scan as a complete census.

## The bug unit tests structurally cannot catch

**`total` must not depend on `limit`.**

Sizing the scan window relative to the page (`min(CAP, limit * 10)`) makes a
small page scan a small window, so `total` measures the *window* rather than the
*data* — and `truncated` fires spuriously on every small page.

Observed live: `limit=5` → `total=50, truncated=true`; `limit=200` → `total=69,
truncated=false`. Same corpus, two totals.

**Why 13 passing tests missed it:** every test used a single `limit`. The
invariant only breaks when the page size *varies*. Any single-limit test suite is
blind to it, no matter how thorough.

```python
# The regression that catches it
async def test_total_is_independent_of_page_size():
    docs = _docs(69)
    small = await query(docs, limit=5)
    large = await query(docs, limit=200)
    assert small["total"] == large["total"] == 69
```

**Generalize:** for any derived value, ask which *parameters it should be
independent of*, and write a test that varies exactly those. Scan the window at a
fixed cap, independent of page size.

## Also assert

- Pages do not overlap and cover every record exactly once
- Sort order holds **across** page boundaries (sort before slicing, never after)
- Last page is partial, not padded
- Offset past the end is empty, not an error
- Search `total` counts matches, not the corpus
- A no-match search returns empty, never falls back to unfiltered
- **An empty search result is distinct from an empty corpus** — otherwise the
  "no records yet, get started" onboarding state renders for a search that
  simply matched nothing

## Verification order (do not skip)

1. Unit tests — including the varying-`limit` invariant
2. **Probe the deployed API at several limits** and compare totals
3. **Load the actual page and read every number on it**

Steps 2 and 3 are not ceremony. In the case this skill is written from, step 2
caught the `total` bug and step 3 caught two surfaces still showing the page
size — after the test suite was fully green. A green build is not evidence that
the screen is right, and the screen is the whole deliverable.

## When the browser tool is wedged

If the headless browser times out, you can still verify the deployed client
bundle without it:

```bash
curl -s "$HOST/page" -o /tmp/p.html
grep -o 'src="/_next/static/chunks/[^"]*"' /tmp/p.html | sed 's/src="//;s/"//' > /tmp/chunks.txt
while read c; do curl -s "$HOST$c" -o /tmp/c.js; \
  grep -q "NEW STRING" /tmp/c.js && echo "FOUND in $c"; done < /tmp/chunks.txt
```

Grepping the server HTML alone proves nothing for a client-rendered SPA — the
shell contains no list markup. Check the JS chunk for strings you added AND
confirm strings you removed are gone.
