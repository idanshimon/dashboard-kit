# The single-file, zero-dependency operator dashboard

A different build shape from the Next.js surfaces in the main skill. Use it when
the dashboard displays **confidential data**, must open on any machine with no
build step, or has to survive being handed to someone as one file.

Constraints that force this shape:

- Every external request (CDN, font, chart library) is a potential egress path
  for the data on screen. With account-level actuals under a "must not be
  shared" banner, that is a real objection, not a purist one.
- A CDN outage must not break a surface used live in a customer meeting.
- No build step means no stale-bundle class of bug at all.

Structure: one `index.html` with embedded `<style>`/`<script>`, plus a generated
`data.json` fetched at load. Hand-rolled SVG for charts.

## Author it skeleton-first, or the write times out

A rich dashboard blows past the per-tool-call argument limit in one
`write_file`. The stream dies mid-delivery and nothing lands.

1. Write a **complete skeleton** — full `<head>` with *every* CSS token and rule
   already defined, `<body>` with nav/footer scaffolding, and one HTML comment
   placeholder per planned section (`<!-- SECTION:OVERVIEW -->`,
   `<!-- SCRIPT:CHARTS -->`).
2. `patch` each placeholder with its full content. Independent placeholders can
   be patched in parallel.
3. Define all styling up front so later patches never revisit `<head>`.

Gotcha: if you must reference a placeholder's literal text in a patch's
`old_string`, do not HTML-escape it. `&lt;!-- STYLE:EXTRA --&gt;` will not match
`<!-- STYLE:EXTRA -->`.

## Sticky table headers: the offset is relative to the SCROLL CONTAINER

The bug that shipped and drew a user correction — *"the Account headline is
stuck when scrolling"*:

```css
/* WRONG — 60px is the PAGE nav's height, but the table lives in .scroll */
th { position: sticky; top: 60px; }
.scroll { max-height: 640px; overflow-y: auto; }
```

`position: sticky` resolves against the nearest **scrolling ancestor**, not the
viewport. Inside an `overflow-y:auto` container the header parks 60px *down*
from the container's top edge and sits there visibly detached while rows slide
past it.

```css
/* RIGHT — scope the sticky rule to the container it actually lives in */
table { border-collapse: separate; border-spacing: 0; }
th { padding: 10px 12px; border-bottom: 1px solid var(--line); background: var(--panel); }
.scroll thead th {
  position: sticky; top: 0; z-index: 5;
  box-shadow: inset 0 -1px 0 var(--line), 0 1px 6px rgba(0,0,0,.14);
}
```

Three coupled details, and the second one is the classic follow-on bug:

- **Scope to `.scroll thead th`, not bare `th`.** Tables elsewhere (a docs tab,
  a static summary) do not scroll independently and must not be sticky.
- **`border-collapse: collapse` drops a sticky header's own border**, because
  collapsed borders belong to the table rather than the cell — rows then bleed
  through the header. Switch to `separate` + `border-spacing: 0` and draw the
  edge with `inset` box-shadow.
- **Add a real drop shadow** so the header reads as floating above the rows
  instead of merging into them.

Rule of thumb: any `top:` value on a sticky element needs the question *"sticky
inside what?"* answered before it is written.

## Preflight structure, then execute in a real browser

Use the following checks as cheap preflight only; DOM IDs, tag balance and a
sample row cannot prove JavaScript ran or charts rendered. Serve the real
payload on loopback and exercise it in an available local browser, for example
with Playwright's `chromium.launch(headless=True, channel='chrome')` when that
browser is installed. Capture page errors, click every tab, reload while a filter
is active, open a detail view, and inspect screenshots at desktop and mobile
widths. Assert `document.documentElement.scrollWidth <= innerWidth` at the narrow
viewport so a crowded nav cannot silently push controls offscreen.

These static checks can catch missing targets before that runtime pass:

```python
import re, json
src = open('index.html').read()

# 1. Every element the JS writes to must exist in the DOM.
used = set(re.findall(r"getElementById\('([^']+)'\)", src))
defined = set(re.findall(r'id="([^"]+)"', src))
assert not (used - defined), f"JS targets missing from DOM: {used - defined}"

# 2. Every function called must be defined.
called  = set(re.findall(r'\b(render[A-Za-z]+|openDrawer|closeDrawer)\s*\(', src))
defined_fns = set(re.findall(r'function\s+([A-Za-z_]\w*)\s*\(', src))
assert not (called - defined_fns)

# 3. The data contract: every field the UI reads exists in the payload.
row = json.load(open('data.json'))['accounts'][0]
need = ['tpid', 'name', 'risk', 'class', 'anomalies', 'named_competitor']
assert not [k for k in need if k not in row]
```

Plus a tag-balance pass with `html.parser` and a VOID allow-list that **includes
SVG self-closing elements** (`path`, `circle`, `rect`, `line`, `text`, `stop`,
`use`, `polygon`, `ellipse`) — omit those and a hand-rolled chart reports dozens
of phantom unclosed tags.

Also assert **zero placeholders remain**: `src.count('<!-- SECTION:')` must be 0.
A skeleton comment left un-patched renders as nothing at all, which looks
identical to a section you simply forgot to write.

Report static checks as structure-only. Wiring requires executing the real
producer's payload in the browser; visual legibility requires inspecting the
render. If either is unavailable, leave that verification explicitly pending.

## Grep before believing a duplicate

Scanning for `border-collapse` returned two hits and looked like an override
fighting the fix. One was the CSS rule; the other was a word inside the comment
explaining the rule. Read the surrounding line before patching — a match inside
your own prose is not a second declaration.

## Design notes that carried

- **`color-mix(in srgb, var(--accent) 12%, transparent)`** for badge fills keeps
  one accent token driving both border and background across light and dark,
  instead of six hand-mixed hexes. Same lesson as the tint-strength section in
  the main skill, reached from the other direction.
- **Two themes from one token block**: `html[data-theme="light"]` /
  `[data-theme="dark"]` each redefining the same variable names. The theme
  toggle swaps one attribute and persists to `localStorage`.
- **Charts as pure functions returning SVG strings** (`areaChart(pts, w, h,
  color)`) compose into any view and need no library. A "baseline band" chart —
  a translucent rect for the learned normal range, a dashed median line, and the
  actual series over it — makes a per-entity threshold self-evidently
  data-derived rather than arbitrary.
- **`file://` cannot `fetch` a sibling JSON.** Ship the one-line
  `python3 -m http.server --directory <dir>` command in the error state itself,
  because "it opens but the page is empty" is otherwise the first bug report.
