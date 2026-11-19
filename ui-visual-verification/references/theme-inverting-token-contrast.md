# Theme-inverting tokens: invisible controls that no hex-pair check can catch

The bug `scripts/contrast_ratio.py` **cannot** find, because there is no fixed
pair of hex colors to compare — one side of the pair changes with the theme.

## The defect

```jsx
className="bg-[color:var(--color-ink)] text-white"
```

Reads fine. Ships. In light mode `--color-ink` is `#171a20`, so white text on
near-black — perfect. In dark mode the token **inverts** to `#f4f4f5`, and the
hard-coded `text-white` does not. Result: **white on white, measured 1.10:1**,
against a WCAG AA requirement of 4.5:1. The control is not "low contrast," it is
invisible — present in the DOM, clickable, completely unreadable.

Real case 2026-08-31 (cartrack): the user reported "dark colors hard to see
button text." Measuring it live gave:

```
"Calculate"      #ffffff on #f4f4f5   ratio 1.10:1
"Dealer page"    blue-600  on #000     ratio 1.29:1
```

Grepping the pattern found **five more instances** — Save settings, filter
chips, active facet pills, pagination. All shipped, all invisible in one theme,
none caught by review or by any automated check in the repo.

## Why it survives review

A semantic token named `ink` reads as "dark" to a human. The class is written
against that mental model and is correct in exactly the theme the author had
open. Nobody re-reads a button that looked right.

The second failure in the same session is the same root cause in reverse:
`text-blue-600 dark:text-blue-400` — a **hard-coded palette pair** bypassing the
token system entirely. `blue-600` on `#000` is 1.29:1. Once a design system
exists, any raw `blue-600`/`stone-400` is an unreviewed color decision.

## The rule

**A filled control must be built from a color that is stable BY INTENT.**

In a two-theme system, tokens fall into two classes and mixing them up is the bug:

| Class | Examples | Safe behind fixed `text-white`? |
|---|---|---|
| **Inverting** — crosses the light/dark boundary | `--color-ink`, `--color-ink-body`, `--color-canvas` | **NO** |
| **Stable** — may shift hue/brightness, never crosses | `--color-accent`, `--color-danger`, `--color-good` | Yes |

`--color-accent` shifting `#3e6ae1` → `#3368ff` for dark is fine: it stays a
mid-blue that white text reads on in both. Verified after the fix: 4.60:1 and
4.56:1.

## The check: a SOURCE lint, not a DOM check

This failure is invisible to any DOM-free assertion and to any single-theme
screenshot. It is cheapest to catch in source, because the pattern is textual.

`scripts/theme_token_contrast_lint.py` fails on:

1. an inverting token as `bg-` behind a hard-coded `text-white` / `text-black`
2. any hard-coded palette color (`blue-600`, `stone-400`, `gray-700`) once a
   token system exists

Run it in the same breath as a build. In the real case it immediately earned its
place by catching a `stone-500` in a file an earlier token migration had missed
because that file was not in the sweep list — a bug found by the lint on its
first run, not by the eye.

## Live-DOM measurement over CDP (when you need the actual number)

To turn "hard to see" into a ratio against **composited** backgrounds — which is
what the user is actually looking at — evaluate in the live page. This walks up
for the first non-transparent ancestor background, so it handles controls whose
own background is `transparent`:

```js
(() => {
  const lum = c => {
    const m = c.match(/[\d.]+/g); if (!m) return 0;
    const [r,g,b] = m.slice(0,3).map(Number).map(v => {
      v/=255; return v<=0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4);
    });
    return 0.2126*r + 0.7152*g + 0.0722*b;
  };
  const solid = el => {                       // nearest painted ancestor bg
    let n = el;
    while (n) {
      const b = getComputedStyle(n).backgroundColor;
      if (b && !/rgba\(0, 0, 0, 0\)|transparent|oklab/.test(b)) return b;
      n = n.parentElement;
    }
    return getComputedStyle(document.body).backgroundColor;
  };
  const R = (f,b) => {
    const L1=lum(f), L2=lum(b);
    return +(((Math.max(L1,L2)+0.05)/(Math.min(L1,L2)+0.05)).toFixed(2));
  };
  const out = [];
  document.querySelectorAll('a,button').forEach(el => {
    const t = (el.textContent||'').trim(); if (!t || t.length > 20) return;
    const s = getComputedStyle(el);
    let bg = s.backgroundColor;
    if (!bg || /rgba\(0, 0, 0, 0\)|oklab/.test(bg)) bg = solid(el);
    out.push({ text: t.slice(0,18), fg: s.color, bg, ratio: R(s.color, bg) });
  });
  return { theme: document.documentElement.className,
           failing: out.filter(o => o.ratio < 4.5) };
})()
```

### Two traps in the measurement itself

- **Confirm the tab is in the theme you think it is.** The first run of this
  returned `theme: "light"` on a stale tab and reported everything passing. Always
  return `document.documentElement.className` alongside the numbers, and check it.
- **Modern CSS pipelines emit `oklab(...)` for alpha-composited backgrounds**,
  which a naive `\d+` color parser reads as garbage and reports as an absurd
  ratio (`4395009027.13`). Skip `oklab` values and fall through to the ancestor.
- **Alpha-over-black is a false positive.** An active nav pill of
  `rgba(255,255,255,0.04)` under `#f4f4f5` text reports ~1.1:1 because the
  script cannot composite alpha; the true ratio against the real black backdrop
  is ~18:1 and perfectly readable. Report these as checker limitations rather
  than silently filtering them — but do not "fix" them.

## Migration pitfall: a regex that kills the thing it migrates

Bulk-migrating raw palette classes onto tokens with `perl -0pi -e` will happily
rewrite **both** halves of a hover pair:

```
decoration-stone-300 + hover:decoration-stone-900
  -> decoration-[--color-hairline] + hover:decoration-[--color-hairline]
```

Now the underline is hairline-on-hairline: invisible at rest *and* on hover. The
link is technically present and visually gone. In the real case the user
reported this as "I lost the links on the listing" — a *contrast* regression
read as a *missing feature*.

After any bulk color migration, re-check the states that are supposed to
**differ** (rest vs hover, default vs active vs disabled). A migration that
makes two states identical is a silent regression that no build catches.

Also: delete `dark:*` variants rather than remapping them. Once a token is
theme-aware, a `dark:` override on top of it is dead weight that silently fights
the theme.
