# When the SCREENSHOT is the bug, not the CSS

Caught the hard way (Shlife dashboard, Sep 2026). Cost three wasted fix rounds
and one self-inflicted regression. This is the highest-value entry in this
skill for anyone doing responsive/mobile QA.

## The trap

Vision QA reported, across THREE separate rounds, that a card's description was
truncated at a 390px mobile viewport:

> "Rose from $4,337.11. The entire +$726/mo increase is **escro**"
> *"Does any sentence end mid-word at the right edge?" -> "Yes."*

Every round I patched CSS. Every round the next screenshot still showed the cut.

**Nothing was ever clipped.** The capture method was cropping the image.

## What actually proved it

Stop patching. Measure the live DOM over CDP:

```
docW 390  bodyScrollW 390
  P     w=290 right=340 scrollW=290 clientW=290 ov=visible wrap=anywhere
  TD    w=290 right=340 scrollW=290 clientW=290 ov=visible wrap=anywhere
  TR    w=316 right=353 scrollW=314 clientW=314 ov=visible wrap=anywhere
```

`scrollWidth === clientWidth` at every level in the ancestor chain, and
`bodyScrollWidth === docWidth`. **There is no overflow anywhere.** Then the
decisive check, per-line rects:

```
TEXT: Rose from $4,337.11. The entire +$726/mo increase is escrow.
rendered on 2 line(s); box right edge: 329  viewport: 379
overflows viewport? False
  line 1: width=239 right=289
  line 2: width=107 right=157
```

The text wraps to two lines and ends 222px inside the right edge. The word
`escrow.` was always fully rendered.

Cross-check that costs one command: `--dump-dom | grep` for the full string.
If the complete text is in the DOM and `scrollWidth === clientWidth`, the
layout is fine and your CAPTURE is wrong.

## Root cause

Chrome's `--headless=new --screenshot=out.png --window-size=W,H` flag can crop
the rendered page. It does not reliably honor a narrow mobile viewport the way
device emulation does.

**Fix: capture through CDP with real device metrics**, not the CLI flag.

```python
await send("Emulation.setDeviceMetricsOverride",
           {"width": 390, "height": 950, "deviceScaleFactor": 2, "mobile": True})
await send("Page.navigate", {"url": url})
await asyncio.sleep(3)
r = await send("Page.captureScreenshot",
               {"format": "png", "captureBeyondViewport": True})
```

`captureBeyondViewport: True` gets the full scrollable page, and
`mobile: True` makes it a genuine mobile viewport rather than a narrow desktop
window. Re-shot with this, vision read the sentence back complete, first try.

Runnable probe: `scripts/cdp-measure.py` in this skill.

## The regression I caused (don't repeat it)

First "fix" was:

```css
.shl-root, .shl-main { overflow-x: hidden; }
.shl-table tr { max-width: 100%; overflow: hidden; }   /* WRONG */
```

**`overflow: hidden` CLIPS text. It is the opposite of wrapping.** If the goal
is "long strings must wrap inside their container," the tools are:

```css
overflow-wrap: anywhere;   /* break anywhere only if needed */
word-break: break-word;
min-width: 0;              /* REQUIRED inside flex/grid, or children refuse to shrink */
```

`min-width: 0` is the one people forget. A flex or grid child defaults to
`min-width: auto`, which refuses to shrink below its content and pushes the
layout wide. No amount of `overflow-wrap` helps until you set it.

Reaching for `overflow: hidden` to "fix" a wrap problem is a smell that you
haven't diagnosed the problem yet.

## The rule

**Two failed CSS fixes for the same visual defect = stop editing CSS and
measure the DOM.** A third blind patch is never the answer. Cheap ordered
diagnosis:

1. `--dump-dom | grep` for the full string. Present -> not a data problem.
2. CDP: `scrollWidth` vs `clientWidth` up the ancestor chain. Equal -> not an
   overflow problem.
3. `range.getClientRects()` for per-line geometry. Inside the viewport ->
   **the capture is lying, not the page.**
4. Only now touch CSS.

## Vision-model calibration

This skill already says vision QA is a smoke test, not an arbiter. This session
shows the failure mode in the OTHER direction from the usual one:

- Known: vision **over-reports legibility** ("looks fine") on subtle same-hue
  contrast. Under-trust its passes.
- New: vision also **confidently reports clipping that does not exist** when
  handed a cropped screenshot. It faithfully describes the IMAGE; it cannot
  know the image misrepresents the page.

Both collapse to one rule: **vision judges the artifact you hand it, not the
system.** For any geometry claim (clipped / overflowing / cut off / off-screen),
confirm with a DOM measurement before acting. Contrast and "does this look
broken" stay a human call; geometry is machine-checkable, so check it.

## Where vision WAS right in the same session

Don't over-correct into ignoring it. In the same run vision correctly caught:

- A genuinely clipped 3-column table at 390px (third header truncated to
  "PE...") -> fixed by restacking to labeled cards under 700px.
- Washed-out secondary text and pastel badges in light theme -> fixed by
  deepening tints, darkening badge text, and adding
  `border: 1px solid currentColor` so each badge is FRAMED rather than relying
  on a tint alone.

The difference: those were style judgments on a faithful image. The false
positive was a geometry claim on an unfaithful one.
