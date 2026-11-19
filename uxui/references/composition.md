# Composition — hierarchy, density, precedence
*(v2.1 — unverifiable "taste tests" removed; global rules demoted to archetype defaults)*

## 0. PRECEDENCE — read before any other rule

When rules conflict, higher wins. The rules below are defaults, not absolutes.

1. **Correctness & domain semantics** (units, missing != zero, no invented values)
2. **Accessibility & safety** (contrast, never color-alone, keyboard, reduced motion)
3. **Task completion** (primary action reachable and obvious)
4. **Information hierarchy**
5. **Responsive behavior**
6. **Aesthetic consistency** (tokens, spacing, type)
7. **Decorative polish** (gradients, glass, micro-interaction)

A clinical threshold band overrides the color budget. An ops console overrides "one hero".
Any override must appear in the manifest's `overrides:` block with a reason.

## 1. Focal hierarchy — DEFAULT for executive/narrative, NOT universal

- **Executive / narrative**: one hero (the answer), 3-5 uniform secondary metrics, muted tertiary.
- **Operational**: NO single hero. Operators scan for exceptions. Two independent channels:
  - **Importance** — layout position + size, fixed at author time.
  - **Urgency/status** — color + icon + badge, driven by data at runtime.
  A healthy critical service stays quiet; a firing alert on a minor service goes loud.
  Collapsing these two channels into one is the classic ops-console failure.
- **Analytical**: controls + coordinated views; the hero is the *comparison*, not one number.

## 2. Color — semantic roles, not pixel budgets

v2.0's "<=10% of pixel area" is DELETED: an agent cannot measure it, and heatmaps, status grids
and incident timelines legitimately break it. Replacements that are actually checkable:

- **At most 3 simultaneous accent meanings** per view (excluding data-driven status and
  continuous chart scales). Beyond 3 the reader cannot hold the legend.
- Color always carries meaning; decorative color is forbidden. But *encoding is protected* —
  never strip a variance/threshold/status color to look calmer.
- Neutral is the default state. If everything is colored, nothing is.
- Never color-alone: pair with icon, text, or position.

## 3. Whitespace & density

Space between groups must exceed space within groups (`--space-8` between sections,
`--space-3` inside a card).

| Mode | Card padding | Row height | Use for |
|---|---|---|---|
| Comfortable | `--space-6` | 48px | Executive, narrative |
| Compact | `--space-4` | 36px | Operator consoles, analytical |
| Dense | `--space-3` | 28px | Data tables, log views |

**Density is per component family/region, not per page.** A comfortable exec summary above a
dense detail table is correct. Forbidden: arbitrary variation among *peers* — two sibling cards
at different densities. Declare density per region in the manifest.

## 4. Type — named roles, no ad-hoc sizes

The v2.0 "max 4 sizes" cap is DELETED (easy to count, poorly correlated with quality). Instead:
every text element maps to a named role; sizes outside the scale are forbidden.

`--text-xs .75rem` · `--text-sm .875rem` · `--text-base 1rem` · `--text-lg 1.125rem`
· `--text-xl 1.25rem` · `--text-2xl 1.5rem` · `--text-3xl 1.875rem`

Roles: `eyebrow` (xs, uppercase, tertiary) · `title` · `deck` · `section` · `body` · `caption`
· `data-label` · `metric`. Hierarchy comes from **weight + color before size**.
Numbers always `font-variant-numeric: tabular-nums`. Prose 60-80ch.

## 5. Elevation

| Level | Meaning | Dark | Light |
|---|---|---|---|
| 0 | Page | `--bg-primary`, no shadow | `--bg-primary`, no shadow |
| 1 | Card/panel | `--bg-surface` + border | `--bg-surface` + `--shadow-sm` |
| 2 | Popover/dropdown | `--bg-elevated` + `--shadow-md` | `--shadow-md` |
| 3 | Modal | `--bg-elevated` + `--shadow-lg` + scrim | same |

No skipping levels; no two level-1 surfaces stacked. Dark separates with borders (shadows are
invisible on near-black); light separates with shadows and recedes borders to `--border-muted`.

## 6. Layout

CSS Grid with **named regions** sized to the archetype. The v2.0 "one 12-col grid" mandate is
DELETED — it mimics a framework without improving composition in a single-file artifact.
One gutter token per surface. Numbers right-aligned, text left-aligned, nothing centered in tables.

## 7. Motion

- Two durations: `--transition-fast` 150ms (hover/press), `--transition-normal` 250ms (enter/exit).
- **Prefer** `transform`/`opacity` for moving geometry. Paint transitions (`background-color`,
  `border-color`) are permitted on small bounded controls — v2.0's "transform and opacity ONLY"
  contradicted its own skeleton and hover primitives.
- Never `linear` on UI, never bounce. No count-up animations on operational data.
- `prefers-reduced-motion` block is mandatory (polish.md).
