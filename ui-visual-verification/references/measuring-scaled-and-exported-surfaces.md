# Measuring scaled surfaces, and verifying PDF/print exports

Two failure classes where **the measurement lies, not the code**. Both cost real rounds on
2026-09-08 building a 1920×1080 MBR deck. The parent skill's rule is "verify by looking, not
by trusting green tests" — these are the cases where your *looking apparatus itself* is wrong,
so you confidently report a defect that does not exist, or an export that is fine as broken.

---

## 1. `getBoundingClientRect()` on a CSS-scaled slide returns SCALED pixels

Fixed-canvas decks (1920×1080) fit the viewport with:

```js
const fit = () => { const s = Math.min(innerWidth/1920, innerHeight/1080);
  S.forEach(x => { x.style.transform = 'scale(' + s + ')'; }); };
```

Every rect you read is then multiplied by `s`. Column widths set to `[112,236,952,222,230]`
measured as `[100,211,852,198,206]`. The conclusion drawn — "my `colgroup` is being
overridden" — was false. Two rounds went into swapping `colgroup` for `th` widths and adding
`table-layout:fixed` to CSS that was already correct, and the user was told a layout bug
existed that never did.

**Recover the scale factor before believing any number:**

```js
const k = new DOMMatrix(getComputedStyle(slide).transform).a;   // e.g. 0.8958
const w = Math.round(el.getBoundingClientRect().width / k);     // real slide px
```

**Two cheap cross-checks that would have caught it immediately:**

- **Compare against `getComputedStyle`.** It reports the *unscaled, authoritative* value.
  Computed `112px` vs rect `100px` means the CSS landed and your arithmetic is off — not that
  a rule lost.
- **Sum the columns against the known canvas.** `1920 − padding×2 = 1752`. If the unscaled
  widths sum to exactly that, the layout is doing what you asked.

Overflow checks (`rect.bottom > slide.bottom`) are safe unscaled, because both sides scale
together. Only **absolute** widths and gaps need dividing out.

---

## 2. "No text extracted" from a PDF is usually your parser, not the PDF

A hand-rolled `zlib.decompress` over `stream…endstream` returned **zero** matching strings
from a PDF whose pages were completely intact. Chrome subsets and re-encodes fonts on export,
so naive stream scraping finds nothing. Reporting "the PDF is broken" on that basis is the
same error as reporting a page empty because your extraction harness failed.

**Verify an export against properties that do not depend on text extraction:**

```bash
# page count + page geometry, no dependencies
mdls -name kMDItemNumberOfPages -name kMDItemPageWidth -name kMDItemPageHeight out.pdf
# → 7 pages, 1440 × 810  (exact 16:9 landscape)

# render page 1 to an image, then read it with vision
sips -s format png --out /tmp/p1.png out.pdf
```

Then `vision_analyze` the PNG and ask *"is this complete, or blank/cut off?"* That is the
verification that actually holds.

Links survive extraction even when text does not — `/URI\s*\(([^)]+)\)` is reliable, and
proves clickable sources made it into the export.

---

## 3. Print CSS cannot beat inline transforms — use beforeprint

The same `fit()` writes **inline** `style.transform`, which outranks any stylesheet. A print
block alone therefore exports one scaled slide, not N clean pages. Strip the inline styles for
the export and restore them after, or the deck stops being navigable:

```js
addEventListener('beforeprint', () => {
  S.forEach(x => { x.style.transform = ''; x.classList.add('on'); });  // reveal ALL slides
  document.body.style.width = '';
});
addEventListener('afterprint', () => { fit(); show(i); });
```

Paired with:

```css
@page { size: 1920px 1080px; margin: 0 }
@media print {
  .slide { position:relative!important; display:block!important; opacity:1!important;
           transform:none!important; page-break-after:always;
           width:1920px; height:1080px; overflow:hidden }
  .slide:last-child { page-break-after:auto }
  .pdfbtn { display:none }                       /* controls must not export */
  * { -webkit-print-color-adjust:exact; print-color-adjust:exact }
}
```

**Headless export, no npm dependency** — drive the browser already on the machine:

```js
execFileSync(CHROME, ['--headless', '--disable-gpu', '--no-pdf-header-footer',
  '--print-to-pdf=' + pdf, '--virtual-time-budget=4000', 'file://' + path.resolve(out)]);
```

Candidates in order: Chrome, Edge, Chromium under `/Applications/`. The macOS
`CVDisplayLinkCreateWithCGDisplay failed` spew on stderr is **noise** — the PDF still writes;
check the file, not the log.

---

## 4. Flags parsed as positional args

`node render.js --pdf` wrote a file literally named `--pdf`, because `argv[2]` was taken as
the output path unconditionally. Cheap to prevent:

```js
const args    = process.argv.slice(2);
const wantPdf = args.includes('--pdf');
const outArg  = args.find(a => !a.startsWith('--'));
```

Symptom is quiet: the run reports success and the real artifact is never updated.

---

## Checklist for a fixed-canvas deck

- [ ] Scale factor divided out of every **width/gap** measurement
- [ ] Unscaled column sum equals canvas minus padding
- [ ] `getComputedStyle` cross-checked before declaring a CSS rule overridden
- [ ] Zero elements overflow their slide (safe unscaled)
- [ ] No element collides with a fixed footer/guardrail bar (`el.bottom > guard.top`)
- [ ] Export: page count and page dimensions verified via `mdls`
- [ ] Export: one page rendered to PNG and read with vision
- [ ] Export: screen-only controls absent from the file
- [ ] Export: links present via `/URI` scan
