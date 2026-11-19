# Verifying print output ("must fit on one page")

A print stylesheet is a **second layout** that no screenshot of the screen view
can verify. `@media print` rules are invisible in every normal capture, so the
usual build → screenshot → vision loop is structurally blind to them.

## The rule: count pages in a real PDF, never assume

"Fits on one page" is a falsifiable numeric claim. Generate the PDF headlessly
and count the page objects:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=/tmp/sheet.pdf --virtual-time-budget=5000 \
  "https://example.com/"

python3 -c "
import re
d = open('/tmp/sheet.pdf','rb').read()
print('pages:', len(re.findall(rb'/Type\s*/Page[^s]', d)))"
```

The `[^s]` matters — without it the regex also matches `/Type /Pages`, the
container node, and inflates the count by one.

Then **look at it**, because 1 page can still be unreadable:

```bash
pdftoppm -png -r 110 /tmp/sheet.pdf /tmp/sheetimg
# -> /tmp/sheetimg-1.png, then vision_analyze
```

Ask a falsifiable question: *"Is every category present for both columns, and is
anything cut off at the page edge?"* — not "does this look good".

Verified 2026-08-26 (lunchbox-picker): print sheet confirmed at exactly 1 page by
page-object count, then visually confirmed nothing clipped. Both steps were
needed — the count says *how many pages*, the render says *whether it is usable*.

## Build a dedicated print DOM; do not scale the app down

Trying to make the interactive UI print well fights every screen affordance —
tap targets, sticky headers, fixed bottom bars, card padding. Cleaner and far
more predictable: render a **separate hidden section** that only print shows.

```html
<main id="app"></main>          <!-- screen only -->
<section id="sheet" aria-hidden="true"></section>   <!-- print only -->
```

```css
#sheet { display: none; }                    /* hidden on screen */
@page  { size: Letter portrait; margin: 8mm; }
@media print {
  header, main, .bar, .toast { display: none !important; }
  #sheet { display: block; }
}
```

Build its contents on demand from the same data source, and hook **both** entry
points — the in-app button *and* the browser's own Cmd-P:

```js
document.getElementById("printBtn").onclick = () => { buildSheet(); window.print(); };
window.onbeforeprint = buildSheet;      // catches Cmd-P / Share→Print
```

Without `onbeforeprint`, printing from the browser menu emits an empty sheet.

## Density levers that actually control page count

In print context, use physical units (`mm`, `pt`) — they are stable across
browsers and paper sizes in a way `rem`/`vh` are not.

- `@page { size: Letter portrait; margin: 8mm; }` — margin is usually the
  single biggest win; the 12-15mm defaults waste a lot of paper.
- Multi-column flex for parallel sections (`display:flex; gap:5mm`) instead of
  stacked blocks — halves the height for two-of-a-kind content.
- `break-inside: avoid; page-break-inside: avoid;` on each logical block, so a
  section never straddles the boundary. Include both properties; support varies.
- Inline-wrap list items (`display:flex; flex-wrap:wrap` + `white-space:nowrap`
  per item) rather than one item per line.
- `-webkit-print-color-adjust: exact; print-color-adjust: exact;` or the browser
  strips your background colors and borders.

## Pitfalls

- **`id="print"` collides with `window.print()`.** Named DOM ids become global
  properties, so `<button id="print">` shadows the built-in function and
  `window.print()` throws or silently no-ops. Name it `printBtn`. This is a
  silent breakage — nothing errors at build time. Same hazard for any element id
  matching a `window` member: `name`, `length`, `status`, `top`, `history`,
  `location`, `origin`, `closed`, `parent`, `self`, `frames`, `open`.
- **Emoji and background colors are dropped by default in print.** Set
  `print-color-adjust: exact`, then confirm in the rendered PNG — not in the
  screen view.
- **`--print-to-pdf` ignores `--window-size`.** Page geometry comes from `@page`
  and the paper size, so a viewport-based media query will not be what applies.
  Do not tune print layout by resizing the headless window.
- **`--no-pdf-header-footer`** removes Chrome's injected URL/date chrome, which
  otherwise eats vertical space and can push a tight layout to page 2.
