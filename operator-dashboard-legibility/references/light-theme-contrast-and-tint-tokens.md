# Light-theme contrast failures: baked alphas and dead `dark:` variants

A dashboard built and tuned in dark theme ships a light theme that is *technically*
correct — surfaces invert, accents darken — and is still unreadable in the places
that matter most: code snippets, diff rows, syntax highlighting, badge pills.

Reported as *"I can't see the highlighted text in the code snippets, the colors
are too light."* Verified 2026-08-17 on `agentic-sdlc/apps/ledger-insights-ui`.

## Measure it — do not eyeball it

Compute the actual contrast ratio before and after. A three-line function ends
the argument and gives you numbers for the commit message.

```python
def _lum(h):
    h = h.lstrip("#"); r, g, b = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def ratio(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)
```

Gates: **4.5:1** body text, **3.0:1** large text / UI boundaries.

## Failure mode 1 — Tailwind mid-tone stops fail on white

`text-green-500`, `text-blue-500` etc. read fine on a dark surface and fail AA on
white. Measured against `#FFFFFF`:

| Colour | Ratio | |
|---|---|---|
| `green-500` `#22C55E` | **2.28:1** | FAIL |
| `orange-500` `#F97316` | **2.80:1** | FAIL |
| `blue-500` `#3B82F6` | **3.68:1** | FAIL |
| `red-500` `#EF4444` | **3.76:1** | FAIL |
| `purple-500` `#A855F7` | **3.96:1** | FAIL |
| `indigo-500` `#6366F1` | **4.47:1** | FAIL (just under) |

Not one passes. Green at 2.28:1 is barely distinguishable from the background.

## Failure mode 2 — the `dark:` variant that never fires

The code looked defended: `text-blue-500 dark:text-blue-300`. It was not.

With `next-themes` configured as `<ThemeProvider attribute="class">`, the app
toggles a **`.light`** class and re-themes through CSS custom properties. Whether
Tailwind's `dark:` variant fires at all depends on `darkMode` config — and even
when it does, the *light* value is the failing one, so the pair form defends the
side that was never broken.

**Check how the app actually themes before trusting any `dark:` prefix:**

```bash
grep -rn 'ThemeProvider\|attribute=' src/app/layout.tsx
grep -rn 'classList.*light\|darkMode' src/ tailwind.config.*
```

If theming runs through a `.light`/`.dark` class plus CSS variables, the correct
fix is a **token**, not a Tailwind colour pair. Sweep for the pattern:

```bash
grep -rn "dark:text-\(blue\|purple\|green\|red\|amber\|indigo\)-[0-9]00" src/ --include=*.tsx
```

## Failure mode 3 — hardcoded alpha fights the theme

The subtlest one, and the most widespread. A tint written inline:

```tsx
line.type === "added" && "bg-[var(--success)]/10"
```

The `var()` is theme-aware; the **`/10` is not**. Light theme correctly *darkens*
`--success` (`#22C55E` → `#15803D`), and 10% of an already-dark green on white is
almost no fill at all. The theme did the right thing and the baked alpha undid it.

The rule is counter-intuitive and worth stating explicitly:

> **Darkened accents need MORE alpha on light surfaces, not less.**

## The fix — tint tokens, not 50 hand-edited alphas

Put the *strength* in the theme alongside the *hue*:

```css
:root {                      /* dark */
  --tint-weak: 8%;  --tint: 12%; --tint-strong: 16%;
  --code-keyword: #C4B5FD; --code-string: #86EFAC; --code-heading: #93C5FD;
}
.light {
  --tint-weak: 12%; --tint: 18%; --tint-strong: 24%;   /* MORE, not less */
  --code-keyword: #6D28D9; --code-string: #047857; --code-heading: #1D4ED8;
}
```

Then give the recurring surfaces real classes instead of inline tints:

```css
.diff-added {
  background: color-mix(in srgb, var(--success) var(--tint), transparent);
  box-shadow: inset 2px 0 0 0 var(--success);   /* rail: not colour-only */
}
```

The inset rail matters independently of contrast — **a diff row whose only signal
is a red/green wash is unreadable for colour-blind users** at any alpha. A 2px
left rail survives both low contrast and colour blindness.

Verified after: light **5.48–7.10:1**, dark **9.84–12.93:1**. Both pass AA.

## Sweep the whole app, not the one component reported

The user reports one surface; the pattern is everywhere. Script the migration —
21 files and 52 occurrences in the real case, far too many to hand-edit reliably:

```python
pat = re.compile(r'bg-\[var\(--(success|danger|warning|primary|secondary|info)\)\]/(\d+)')
MAP = {5: "--tint-weak", 10: "--tint", 15: "--tint"}   # leave >=70 (opaque) alone
```

Print the alpha distribution first (`collections.Counter`) — it tells you which
values are tints and which are intentional near-opaques you must not touch.

## Verify at the right layer

Contrast maths proves the tokens; it does not prove the render. Finish with
`npx tsc --noEmit`, a production build, then a screenshot with the theme forced
before first paint:

```js
await ctx.addInitScript(() => localStorage.setItem("theme", "light"));
// belt and braces, in case the provider hasn't rehydrated:
await page.evaluate(() => {
  document.documentElement.classList.remove("dark");
  document.documentElement.classList.add("light");
});
```

**Confirm you screenshotted the right server.** A stray process holding the port
you asked for will make the framework bind elsewhere, and the screenshot silently
captures a 404 page from the squatter. Check before believing the image:

```bash
lsof -nP -iTCP:<port> -sTCP:LISTEN     # expect YOUR process, not something else
```
