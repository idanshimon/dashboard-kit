# Verifying single-file HTML artifacts (explainers, decks, reports)

> Filed 2026-07-30 after building a 7-section interactive explainer as one
> self-contained HTML file. Three render defects survived the first write; each
> cost a screenshot cycle. None would have been caught by any test, because
> there are no tests — a single-file artifact has NO build step and NO type
> checker, so the screenshot is not the last mile, it is the ONLY line of
> defence.

## Why this path needs its own recipe

The main skill's loop assumes a framework app: production build, standalone
server, real data, public URL. A single-file HTML artifact has none of that.
What it also has none of: a compiler that catches a typo'd class name, a linter
that notices a grid row count, or a test that renders the page. Every defect is
a *silent* visual defect.

Consequence: the verification bar is HIGHER here, not lower. Screenshot every
view before delivering.

> **Before you screenshot anything, parse-check the script.** If the artifact
> has an inline `<script>`, a single syntax error means NOTHING runs and the
> page still serves 200 showing its static skeleton — which reads as a styling
> bug, not a fatal one. Tag-balance checks, DOM-id audits and HTTP status all
> pass on a completely dead page. See
> `references/js-parse-check-before-visual-qa.md` for the one-call
> `new Function()` check, the in-page bisect that finds the offending line, and
> the `${...}`-leaked-into-static-markup sibling bug.

## Hash-routed pages: screenshot EVERY tab

A single-file explainer usually fakes routing with `#anchor` + Alpine `x-show`.
Only one section is in the DOM-visible state at a time, so defects hide in the
tabs you skipped.

```bash
for t in why design enforce proof arch apply limits; do
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
    --force-device-scale-factor=1.5 --virtual-time-budget=4000 \
    --screenshot=/tmp/x_$t.png --window-size=1440,1500 \
    "file:///abs/path/artifact.html#$t"
done
```

- `--headless=new` — bare `--headless` sometimes writes a 0-byte file or nothing
  at all, silently.
- `--virtual-time-budget=4000` — Alpine needs to boot and apply
  `x-show`/`x-cloak`, or you photograph the unstyled pre-hydration flash.
- `--force-device-scale-factor=1.5` — 1x text looks soft and you will misread it
  as a font problem.
- `--window-size` height is a **guess per tab**. Too short silently clips the
  bottom; there is no error. Size to the longest section and re-run if the
  vision pass reports a cut-off.

Then `vision_analyze` each PNG with a falsifiable question — for this artifact
class: *"are the icons rendering as real glyphs or empty space, is any text
clipped or overlapping, are the code blocks readable, are there unexplained
empty regions?"*

## The three silent defects that recur

**1. Icon-font class prefix mismatch → invisible icons, no error.**
The npm package is `lucide-static`; the CSS classes it ships are `.icon-*`, NOT
`.lucide-*`. Writing `class="lucide-shield-check"` matches no rule and renders
**empty space** — no console error, no missing-glyph box, no layout shift. On a
page with 90+ icons the result reads as "the design is flat and unfinished" and
you will hunt a styling bug that is actually a typo.

Verify the prefix in force rather than trusting any doc (including this one —
icon packages rename classes between majors):

```bash
curl -s "https://cdn.jsdelivr.net/npm/lucide-static@latest/font/lucide.min.css" \
  | grep -o '\.[a-z-]*shield[a-z-]*' | head -5
# → .icon-shield-check, .icon-shield-alert, ...
```

Note: the icon NAME after the prefix is stable and correct in most docs; only
the prefix is wrong. Generalise the check — for ANY icon font, grep one known
class out of the live stylesheet before writing 90 of them.

**2. Never mass-rename a prefix with an unscoped `sed`.**
`sed 's/lucide-/icon-/g'` also rewrites the CDN URL in the `<link>` tag to
`npm/icon-static@latest`, which 404s — you trade invisible icons for no
stylesheet at all, which is worse and looks like a different bug. Either scope
the replace to `class="` attributes, or run it and immediately repair the
`<link>`, then `grep -n "cdn.jsdelivr"` to confirm the URL survived.

General rule: after any repo-wide string replace, grep the URLs and imports the
token also appears in.

**3. `grid-template-rows` with fewer entries than children → huge empty void.**
`.dashboard { display:grid; grid-template-rows: auto 1fr; }` with THREE children
(header, nav, main) puts the third in an implicit row that absorbs the slack —
the sticky nav floated ~500px below the header with a void between. Fix is
`auto auto 1fr`. Symptom presents as "there's a giant gap"; instinct is to hunt
padding/margin. **Count the grid children first.**

**4. Box-drawing / ASCII blocks need `white-space: pre`.**
A `<div>` of tree characters without it collapses into a wrapped blob that reads
as corrupted text rather than a diagram. `white-space: pre; overflow-x: auto;`.
`<pre>` gets this free; a styled `<div>` does not.

**5. Layout-variant classes on `.slide` / `.tab` elements override `display: none`.**
If a slide or tab element carries its layout kind as a class (`<section class="slide architecture">`) and a later CSS rule sets `.architecture { display: grid }`, that later rule overrides `.slide { display: none }` because both have equal specificity (`0,1,0`). The inactive slide stays permanently visible on top of later slides while `scrollHeight <= clientHeight` checks still pass. Scope layout rules to the inner container (`.content .architecture { display: grid }`) and assert in the runtime sweep that `[...document.querySelectorAll('.slide')].filter(el => getComputedStyle(el).display !== 'none')` has length `1` and matches the active slide ID at every index.

**6. Synchronize 1-based eyebrow numbers and strip internal coaching from recipient-facing decks.**
When cover slides are unnumbered, hardcoded `01`..`N` eyebrows on subsequent slides lag the 1-based deck footer and teleprompter index by one (`SLIDE 14` on slide `15 / 30`). Compute eyebrow numbers from the 1-based slide index, and when generating a sendable deck for a guest speaker, strip internal source codes (`S01`, `T:12:00`), audit disclaimers, and "confirm/discuss with <speaker>" prompts—verifying with a regex scan over the rendered HTML.

## Delivery pitfall

Writing the file and screenshotting one tab, then reporting "built and
verified", is the failure mode this reference exists to prevent. State plainly
which views you actually inspected versus which you assumed — and if you fixed
a defect, re-screenshot rather than asserting the fix landed.

## Keep the .html on disk

Explainers get 2–3 correction passes ("make it Microsoft-themed", "add a
section", "that diagram is wrong"). Each correction is then a `patch` +
re-render, not a rebuild from scratch.
