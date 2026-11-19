# Choosing emoji/icons that are correct AND render everywhere

Picking an emoji from memory produces two independent defect classes, and both
ship silently:

1. **Wrong referent** — the glyph depicts something the item is not.
2. **Tofu boxes (☐)** — the emoji is too new for the target device's font.

Both are invisible to type checkers, tests, and often to your own machine (a
current macOS renders nearly everything; a 4-year-old school iPad does not).

## Ground the choice in the Unicode registry

`emoji-test.txt` is the authoritative list: every emoji, its fully-qualified
sequence, its CLDR name, and the **E-version** it was introduced in.

```bash
curl -s https://unicode.org/Public/emoji/latest/emoji-test.txt -o /tmp/emoji.txt
```

Search it by name instead of guessing:

```python
import re
rows = []
for l in open('/tmp/emoji.txt', encoding='utf-8'):
    if 'fully-qualified' not in l:
        continue
    m = re.search(r'#\s+(\S+)\s+(E[\d.]+)\s+(.+)$', l)
    if m:
        rows.append((m.group(3).strip(), m.group(1), m.group(2)))  # name, emoji, version

for name, emo, ver in rows:
    if 'pretzel' in name.lower() or 'fries' in name.lower():
        print(f"{emo}  {ver:6} {name}")
```

Only `fully-qualified` lines are safe. `minimally-qualified` and `unqualified`
variants are missing their VS16 selector and can render as monochrome text
glyphs.

## Cap the E-version for the audience

Support is a function of the OS font, not the browser.

| Cap | Rough floor | Use when |
|-----|-------------|----------|
| **E0.6–E5.0** | Universal | Kiosks, unknown/old devices |
| **E14.0 (2021)** | Safe default | Consumer web, school tablets, older phones |
| **E15.0+ (2022+)** | Recent only | Internal tools on current hardware |

Verified 2026-08-26: `🫛 pea pod` is **E15.0** and was deliberately rejected for a
kids' school app in favour of `🫘 beans` (E14.0), accepting that chickpeas, peas,
and edamame then share one glyph. Correct trade — a visible-but-imperfect icon
beats an empty box.

Record the name and version in a comment next to each mapping. It makes the
choice auditable and stops a later editor "upgrading" to a newer glyph:

```js
const I = {
  "BBQ Bissli":  "\u{1F35F}",  // french fries E0.6 — fried wheat sticks
  "Hard-Boiled Egg": "\u{1F95A}",  // egg E3.0
};
```

Use `\u{...}` escapes rather than pasting raw emoji — survives any encoding
mishap in the toolchain, and makes the codepoint greppable.

## Match the OBJECT, not the category

The wrong-referent failure comes from picking by category ("it's a salty snack")
instead of by appearance.

Worked case: **Bissli BBQ** was mapped to `🥨 pretzel` because it is a salty
bagged snack. The user pushed back with a photo. Bissli is a *fried wheat snack
in short stick shapes* — `🍟 french fries` (E0.6) is the only glyph in the entire
registry with that shape. Category said pretzel; the object said fries.

Process:

1. Describe the physical object — shape, colour, form factor.
2. Grep the registry for every plausible candidate, not just the first hit.
3. Pick on **shape resemblance**, then check the E-version.
4. For a brand/regional item, ask what it physically *is* — a foreign brand name
   carries no shape information.

When no glyph matches, say so and use a deliberate generic (`🍽️` E4.0) rather
than a confidently wrong specific one.

## When emoji CANNOT be right: escalate to a hand-authored SVG sprite

There is a hard ceiling here, and it is worth recognising early instead of
grinding through replacement glyphs. **Branded, regional, and fine-grained items
have no emoji and never will** — Pringles, Bissli, Klick, Pirate's Booty,
Cheerios-vs-Cinnamon-Toast-Crunch, chickpeas-vs-peas-vs-edamame. Each round of
"pick a better emoji" buys a marginally less-wrong glyph while the real answer is
a different medium.

Verified 2026-08-26: after fixing Bissli 🥨→🍟, the user asked "you can do better
png to svg icon?". Correct read — the emoji set had been exhausted, not
mis-searched.

**Reject the licensed emoji SVG sets for this** (check before reaching for them):

| Set | License | Why it fails here |
|-----|---------|-------------------|
| **OpenMoji** | CC BY-SA 4.0 | Share-alike is **viral** — avoid in anything you don't want to license |
| **Twemoji** | CC-BY 4.0 | Legally fine, but still *emoji-shaped*: Pringles is still a potato |

Both lose to hand-authoring, because the defect was never rendering fidelity —
it was that **no emoji depicts the object**. Tracing a PNG is also the wrong
move: auto-trace produces bloated, muddy paths.

Hand-author a `<symbol>` sprite instead. Flat vector, one `viewBox`, no
dependency, no license, no network fetch, and it prints crisp:

```html
<!-- icons.svg — NOT display:none; that kills <use> in some engines -->
<svg xmlns="http://www.w3.org/2000/svg" id="sprite" aria-hidden="true"
     style="position:absolute;width:0;height:0;overflow:hidden">
  <symbol id="i-bissli" viewBox="0 0 64 64">…</symbol>
</svg>
```

```js
window.ICON = (n) => `<svg class="ic"><use href="#i-${I[n] || "generic"}"/></svg>`;
```

Then inject the sprite **before first render**, so icons exist for both paint and
print:

```js
fetch("icons.svg").then(r => r.text())
  .then(svg => { document.getElementById("spritehost").innerHTML = svg; })
  .catch(() => {})
  .finally(() => { render(); renderSaved(); });   // draw even if the sprite 404s
```

Sizing moves from `font-size` to CSS width/height (`.ic{width:38px}`), and print
needs explicit mm sizes plus `print-color-adjust:exact` or the icons drop to
outlines.

**Audit the mapping mechanically — every name must resolve to a real symbol:**

```python
have = set(re.findall(r'<symbol id="([\w-]+)"', open('icons.svg').read()))
print("UNMAPPED:", [n for n in food_names if n not in I] or "none")
print("MISSING SYMBOL:", [(n,v) for n,v in I.items() if 'i-'+v not in have] or "none")
```

A `|| "generic"` fallback is a silent-failure surface: a typo'd key renders a
plausible placeholder instead of throwing. The audit is what makes the fallback
safe — and see the main SKILL's *"a verification script that matches nothing
reports green"* rule before trusting its output.

**Hand-drawn vectors are a correctness surface, not decoration** — the main
SKILL's §"Generated vector geometry needs eyes" and the SUV-silhouette case
apply directly. A sprite that audits clean has only been proven *complete*, never
*recognisable*. Screenshot the set and ask a comparative question before shipping.

## Verify by rendering, not by reading the source

Reading `\u{1F35F}` in a diff proves nothing about what a device draws. Render
the real page and look:

```bash
pdftoppm -png -r 150 /tmp/sheet.pdf /tmp/img       # or a headless screenshot
```

Ask a falsifiable question: **"Does every icon render as a real emoji, with no
empty boxes ☐?"** — not "do the icons look right".

The check is cheap and catches the whole tofu class in one pass. A capture from
*your* machine only proves your font has them; when the target is older
hardware, the E-version cap is the actual guarantee, and the render just
confirms the mapping is what you intended.

## Pitfalls

- **Skin-tone and ZWJ sequences multiply the failure surface.** A base emoji can
  be supported while its ZWJ combination is not, and falls back to the component
  glyphs side by side. Prefer single-codepoint emoji for icon sets.
- **`grep -c` on the source is not verification.** It proves the bytes shipped,
  never that they render — same shape as the presence-vs-correctness rule in the
  main SKILL.
- **Distinct items sharing one glyph is a legibility defect worth flagging.**
  Three foods all showing 🫘 read as identical blobs. Surface it to the user as a
  known limitation rather than pretending the icon set is complete.
