# Theme-token contrast failures: hardcoded alpha and dead variants

Session 2026-08-17. User: *"when viewing on light theme, i cant see the highlighted
text in the code snippets, its too light of a colors there."*

Two independent causes compounded. Both are latent in any app that themes via CSS
custom properties, and neither is visible from the dark theme the developer works in.

---

## Cause 1 — hardcoded alpha bakes in a theme assumption

Call sites wrote Tailwind arbitrary-alpha syntax:

```tsx
line.type === "added"   && "bg-[var(--success)]/10",
line.type === "removed" && "bg-[var(--danger)]/10",
```

The theme did the right thing and the markup undid it:

| Theme | `--success` | 10% alpha on the surface |
|---|---|---|
| dark | `#22C55E` (luminous) | reads clearly on `#11161D` |
| light | `#15803D` (darkened) | **near-invisible on `#FFFFFF`** |

Light theme correctly *darkens* accents so they clear 4.5:1 as text. But a dark
colour at 10% alpha is almost no fill. **Darkened accents need MORE alpha to
register as a background, not less** — the alpha has to move in the opposite
direction from the hue.

Roughly 25 call sites carried `/5`, `/10`, `/15` in this codebase.

## Cause 2 — `dark:` variants that never fire

```tsx
pm:        "text-blue-500 dark:text-blue-300",
architect: "text-purple-500 dark:text-purple-300",
```

Check how the app actually themes before trusting a `dark:` prefix:

```
grep -rn "ThemeProvider" src/app/layout.tsx
# → <ThemeProvider attribute="class" defaultTheme="dark" ...>
grep -rn "classList.contains" src/lib/
# → document.documentElement.classList.contains("light")
```

`next-themes` with `attribute="class"` toggles a **`.light`** class, and the
CSS-variable indirection in `globals.css` is the real re-theming mechanism. The
`dark:` variant is dead weight — only the failing 500 mid-tone ever rendered, in
both themes.

## Measure, never eyeball

Not one Tailwind mid-tone passed AA 4.5:1 against `#FFFFFF`:

| Colour | Ratio | |
|---|---|---|
| `green-500` `#22C55E` | **2.28:1** | worst — near-invisible |
| `orange-500` `#F97316` | 2.80:1 | |
| `blue-500` `#3B82F6` | 3.68:1 | |
| `red-500` `#EF4444` | 3.76:1 | |
| `purple-500` `#A855F7` | 3.96:1 | |
| `indigo-500` `#6366F1` | 4.47:1 | fails by a hair |

The WCAG helper is ~6 lines — there is no excuse for shipping by eye:

```python
def lum(h):
    h = h.lstrip('#'); r,g,b = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    f = lambda c: c/12.92 if c <= 0.03928 else ((c+0.055)/1.055)**2.4
    r,g,b = f(r),f(g),f(b); return 0.2126*r + 0.7152*g + 0.0722*b

def ratio(a,b):
    la,lb = lum(a),lum(b); hi,lo = max(la,lb),min(la,lb)
    return (hi+0.05)/(lo+0.05)
```

Run every token against **the surface it actually lands on, in BOTH themes**.

---

## The fix: tokens, not 25 patches

Do not hand-edit every call site — the alpha is a theme-varying quantity, so it
belongs in a token.

```css
:root {                      /* dark */
  --tint-weak: 8%;  --tint: 12%;  --tint-strong: 16%;
  --code-keyword: #C4B5FD;  --code-string:  #86EFAC;
  --code-heading: #93C5FD;  --code-marker:  #6EE7B7;
  --code-comment: var(--text-tertiary);
}
.light {
  /* MORE alpha, not less — the accents are darker here */
  --tint-weak: 12%; --tint: 18%; --tint-strong: 24%;
  --code-keyword: #6D28D9;  --code-string:  #047857;
  --code-heading: #1D4ED8;  --code-marker:  #047857;
}
```

Utility classes so markup stops carrying the alpha:

```css
.diff-added {
  background: color-mix(in srgb, var(--success) var(--tint), transparent);
  box-shadow: inset 2px 0 0 0 var(--success);   /* rail, see below */
}
.diff-removed {
  background: color-mix(in srgb, var(--danger) var(--tint), transparent);
  box-shadow: inset 2px 0 0 0 var(--danger);
}
.code-highlight {
  background: color-mix(in srgb, var(--warning) var(--tint), transparent);
  box-shadow: inset 2px 0 0 0 var(--warning);
}
```

**Add a 2px inset left rail while you are in there.** Colour alone was carrying
add-vs-remove, which fails red/green colour-blind readers at *any* contrast ratio.
Fixing contrast without fixing the redundant-encoding gap only solves half of it.

Verified after — all pass AA in both themes:

| Token | light on `#FFF` | dark on `#11161D` |
|---|---|---|
| `--code-keyword` | 7.10:1 | 9.84:1 |
| `--code-heading` | 6.70:1 | 10.07:1 |
| `--code-string` | 5.48:1 | 12.93:1 |
| `--code-marker` | 5.48:1 | 11.91:1 |

---

## Sweep commands

```bash
# hardcoded alpha on accent tokens — every hit is a latent theme bug
grep -rn "var(--\(success\|danger\|warning\|primary\|secondary\))\]/" src/ --include="*.tsx"

# dark: pairs on mid-tone Tailwind stops — the light value is the failing one
grep -rn "dark:text-\(blue\|purple\|green\|red\|amber\|yellow\|pink\|indigo\)-[0-9]00" src/ --include="*.tsx"

# residual literals after the fix — expect zero in the touched files
grep -rnE 'text-(blue|purple|green|red|amber|yellow)-[0-9]00' src/components/domain/<file>.tsx
```

## Pitfalls

- **Developing in dark theme only.** Every one of these was invisible from the
  default theme. Toggle to light before calling any visual work done.
- **Fixing the reported component only.** The user reported code snippets; the
  same bug class sat in `prompt-chain-badge`, compliance callouts, report cards,
  and the graph pages. Sweep for the pattern, don't patch the symptom.
- **Trusting a `dark:` prefix without checking the theming mechanism.** If the app
  toggles `.light`, `dark:` may be doing nothing at all.
- **Treating contrast as the whole fix.** Redundant encoding (rail, icon, prefix
  character) is a separate requirement.
