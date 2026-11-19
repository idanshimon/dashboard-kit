# Measuring a scaled canvas

Why `getBoundingClientRect()` disagrees with your CSS, and how to tell a real layout
bug from a unit error. Verified 2026-09-08 on a fixed 1920×1080 deck scaled to the viewport.

---

## The trap

`getBoundingClientRect()` returns **post-transform** pixels. If any ancestor carries
`transform: scale(...)`, every width, height and offset you read is multiplied by that
factor.

This is common in:

- slide decks / fixed-canvas layouts (`scale(min(innerWidth/1920, innerHeight/1080))`)
- zoom-to-fit editors and design surfaces
- embedded previews and thumbnail panes
- print-preview and page-fit views

What makes it dangerous: the factor is usually **~0.85–0.95**. Close enough to look like a
plausible layout bug, far enough that declared values look ignored.

## The worked case

Column widths were declared and measured back:

```
declared   [112, 236,  — , 222, 230]
measured   [100, 211, 802, 198, 206]
```

Reported to the user as three separate defects: `<colgroup>` ignored, `table-layout:fixed`
only partly applying, and an evidence column that had somehow got *wider* after the fix.

All false. The scale factor was `0.8958`:

```
112 × 0.8958 = 100.3
236 × 0.8958 = 211.4
```

Dividing back gives exactly `[112, 236, 952, 222, 230]`, summing to 1752 — the 1920 canvas
minus 84px padding each side. The CSS had been correct the whole time. Two rounds were
spent "fixing" it, and a working `<colgroup>` was replaced with `th` classes for no reason.

## The fix

```js
const k = new DOMMatrix(getComputedStyle(scaledAncestor).transform).a;   // scale factor
const trueWidth = Math.round(el.getBoundingClientRect().width / k);
```

`DOMMatrix(...).a` is the horizontal scale component. For a uniform `scale(n)` it is `n`.

## Which checks need normalising

| Check | Compares | Normalise? |
|---|---|---|
| overflow (`child.bottom > parent.bottom`) | two measured values | no — factor cancels |
| collision (`a.bottom > b.top`) | two measured values | no — factor cancels |
| equal heights (`new Set(hs).size === 1`) | measured to measured | no |
| "is this column 236px?" | measured to **declared** | **yes** |
| "does this fit in 1752px of canvas?" | measured to **declared** | **yes** |

Rule of thumb: comparing two things on screen is safe. Comparing screen to stylesheet is not.

## The general rule

**Before reporting that any declaration did not apply, read `getComputedStyle` for the
property you set.**

```js
getComputedStyle(el).width     // '112px'  → the rule landed; your measurement is wrong
                               // '100px'  → the rule really did lose
```

One call, and it splits the two causes that produce identical symptoms:

1. **The rule lost** — inline `style`, specificity, an `!important` elsewhere. Computed
   style shows the value you did *not* write.
2. **The rule landed and the measurement is wrong** — scaled ancestor. Computed style shows
   exactly what you wrote, while `getBoundingClientRect()` disagrees.

A measurement that disagrees with a computed style is a measurement bug, not a CSS bug.

## Checklist

- [ ] `getComputedStyle` read for the property before calling any rule inert
- [ ] Scale factor extracted from the transformed ancestor, not assumed to be 1
- [ ] Every measurement compared against a declared value divided by that factor
- [ ] Overflow/collision checks left unnormalised (both sides carry the factor)
- [ ] Sum of normalised child widths reconciled against the declared canvas width
