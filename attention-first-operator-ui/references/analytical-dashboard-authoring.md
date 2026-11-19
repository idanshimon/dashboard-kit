# Self-contained analytical dashboards

The sibling case to the triage surface in SKILL.md. A triage surface answers *what needs
me now*. An **analytical / intelligence** surface answers *what is happening, and how much
should I believe it* — a ranked book of accounts, a risk register, a competitive-signal
console. The attention-first rules still apply; these are the additions.

Learned building a competitive-intelligence dashboard over BI telemetry, 2026-08.

## Ship one HTML file with no dependencies

For an internal analytical surface, resist the framework. A single `index.html` with
embedded CSS/JS plus a generated `data.json` beside it:

- opens on any machine with no build step, no `node_modules`, no network
- survives being emailed, copied to a share, or opened a year later
- has no CDN that can 404 or get blocked by corporate egress
- diffs cleanly in git

Hand-roll the charts as inline SVG. An area chart with a gradient fill, a donut, a
progress ring and a sparkline row are each ~20 lines of path math and look better than a
default charting library. Attach `<title>` inside each shape for free native tooltips.

**Pitfall — `file://` blocks `fetch`.** The moment the page loads its data over `fetch`,
double-clicking the file fails with an opaque CORS error. Either inline the payload, or
serve it and *say so in the failure message*:

```js
catch(e){
  document.querySelector('.wrap').innerHTML =
    `<div class="panel pad empty"><h2>Could not load data.json</h2><p>${esc(e.message)}</p>
     <p>Serve this directory over HTTP — <code>file://</code> blocks fetch:</p>
     <pre>python3 -m http.server 8899 --directory dashboard</pre></div>`;
}
```

A load failure that tells the reader exactly how to fix it costs three lines.

## Authoring: skeleton + patch, always

A dense dashboard lands well over the per-tool-call argument limit. Write a skeleton first
— full `<head>` with **every** design token and CSS rule already defined, `<body>` with nav
and layout scaffolding, and one HTML comment placeholder per section
(`<!-- SECTION:OVERVIEW -->`, `<!-- SCRIPT:CHARTS -->`). Then patch each placeholder in.

Define all styling up front so later patches never revisit `<head>`. Independent
placeholders can be patched in the same tool-call block.

**Pitfall:** if you write the skeleton with `patch` semantics in mind, do not HTML-escape
the placeholder comments when searching for them — match the literal `<!-- SECTION:X -->`.

Verify before claiming done: a tag-stack parser with a void-element allow-list (`br`,
`hr`, `img`, `input`, plus SVG's `path`, `circle`, `rect`, `line`, `text`, `stop`) catches
unclosed tags, and a grep for remaining `<!-- SECTION:` / `<!-- SCRIPT:` proves every
placeholder was filled.

## Dual theme is a token problem, not a CSS problem

Declare every colour as a variable under `html[data-theme="dark"]` and
`html[data-theme="light"]`, then never write a literal colour anywhere else — including
inside generated SVG, where `fill="var(--bad)"` works fine. Persist the choice to
`localStorage` and re-render on toggle so canvas-drawn elements pick up the new tokens.

`color-mix(in srgb, var(--accent) 12%, transparent)` gives per-theme tinted badge
backgrounds from a single accent token instead of maintaining two palettes.

## The dashboard must carry its own epistemics

This is the rule that separates an intelligence surface from a pretty table. A dashboard
that presents derived scores without stating what it does not know will be trusted further
than it deserves. Give it a **Method** tab, and put in it:

- **Measures that look useful but are not implemented.** Name them, show what they
  actually return, and say why it matters. A field called `Weekly Usage %` that returns the
  string `"TBD"` for every row is exactly the trap the next person will fall into.
- **Semantics established empirically**, labelled as behavioural equivalence rather than
  source, with the fit ratio quoted.
- **Corrections on the record.** If an earlier reading was wrong, say so in the artifact.
  "An earlier read treated X as Y; that was wrong, here is why" builds more trust than
  silently fixing it.
- **Alternative explanations still live** — the benign readings you have *not* excluded.
- **What would change the answer**, i.e. what evidence is actually needed.

Pair it with an explicit **delivers / does not deliver** two-column block. Adjacent, not a
footnote.

## Show the learned baseline, don't just apply it

If thresholds are learned per entity (median + MAD), draw it: a shaded ±2σ band, a dashed
median line labelled with its value, and the actual series over the top with out-of-band
points enlarged and recoloured. Put the deviation in the tooltip (`3.4σ from baseline`).

This is the single most persuasive element on such a dashboard — it converts "trust my
scoring" into "look, this account's own normal range, and this month is outside it."

## Honest states beat fabricated continuity

With one snapshot held, a trend view has no drift to show. Say that plainly in the view:

> **One snapshot held.** Baselines below are learned from the history *inside* this
> snapshot, which is real. Snapshot-over-snapshot drift needs at least two captures.

Never interpolate, never render a single point as a line. An empty state that explains
what is missing and how to get it is a feature.

## Persist snapshots from day one

Write a dated, atomic snapshot (`snapshot_YYYY-MM-DD.json`, temp-file + `os.replace`) on
every pull, and separate the pipeline into `snapshot` → `analyze` → `build`. Trend
tracking is impossible retroactively; the first run is the one that had to save.

Gitignore the snapshot directory when the inputs are confidential account-level actuals,
and state the classification in the dashboard footer.

## Verification

- Tag-stack parse clean; zero placeholders remaining.
- Data file parses and the row count matches what the generator reported.
- Both themes rendered; charts re-render on toggle.
- **Actually look at it.** Structural validation proves the HTML closes, not that the
  layout works. Say which of the two you did — "verified structurally, not visually" is an
  honest status.
