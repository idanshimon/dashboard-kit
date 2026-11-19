# uxui v2.1 — Build Workflow (replaces "copy TEMPLATE.html")

The generic-AI-dashboard problem lives in **page composition**, not in the skin. Tokens and
polish do not fix it. This workflow does, in four steps.

## Step 1 — Write the manifest FIRST (before any markup)
See `references/manifest.md`. Emit it as an HTML comment at the top of the file and state
`artifact_class` + `primary_question` to the user. Skipping this is how you end up with a card
grid regardless of how much design guidance you read.

## Step 2 — Copy the ARCHETYPE template, not a generic one

| artifact_class | Template | Geometry |
|---|---|---|
| executive | `templates/executive.html` | Hero band → uniform secondary strip → evidence |
| operational | `templates/operational.html` | Status rail + alert queue + telemetry + log, mixed density |
| analytical | `templates/analytical.html` | Sticky control panel + coordinated views + small multiples |
| narrative | `templates/narrative.html` | Reading column with full-bleed figures, paced beats |
| report | `templates/executive.html` (print-first) | Document hierarchy |

All four share `templates/_core.css` + `_core.js` (already inlined) and differ **only** in page
geometry. That is the point — same system, genuinely different compositions.

## Step 3 — Build, consulting the references by topic
- `references/composition.md` — **read section 0 (PRECEDENCE) first.** Hierarchy, density, type, elevation.
- `references/charts.md` — the 10-question procedure before picking a chart; data semantics.
- `references/theming.md` — tokens, brand presets, theme resolution.
- `references/polish.md` — a11y, motion, print, decorative effects.
- `references/manifest.md` — anti-inflation rules + provenance.

## Step 4 — RUN THE VALIDATOR. Not a self-assessment.
```bash
python3 scripts/validate.py artifact.html
```
Exit 0 required. Fix every ERROR; justify or fix every WARN. Do not claim compliance without
pasting the validator output — the old prose checklist ("squint at it", "count chromatic
elements") invited unverified "passed" claims and has been deleted for exactly that reason.

Optional visual pass: screenshot both themes at desktop + mobile widths and actually look.

## What v2.1 deleted from v2.0 (and why)
| Deleted | Why |
|---|---|
| "color ≤10% of pixel area" | Agent cannot measure it; wrong for heatmaps/status grids |
| "count chromatic elements" | Same unverifiable rule as a checklist item |
| squint test / grayscale test | An agent cannot perform them; invites a false "passed" |
| "halve the widest column" | Taste-signalling, not reproducible; wrong for tables/timelines |
| "max 4 type sizes" | Easy to count, poorly correlated with quality → named type roles instead |
| "one 12-col grid" | Framework mimicry; named grid regions per archetype instead |
| "1px optical icon nudge" | LLMs cargo-cult it blindly; solve in the primitive |
| Teal = "clinical" hue personas | Aesthetic stereotyping; brand is an input, never inferred |
| Glass as a core primitive | Taught a fashionable effect then banned it → moved to optional appendix |
| Blanket 4-state requirement | Unreachable states for bundled data is a defect, not thoroughness |

## Rules demoted from global to archetype defaults
- **"One hero per screen"** → executive/narrative only. Operational uses two independent
  channels (importance = position/size; urgency = color/icon, data-driven).
- **"Never mix density modes"** → density is per component family/region. Forbidden only among
  *peers*. A comfortable exec summary above a dense table is correct.
- **"Animate transform/opacity only"** → *prefer*. Paint transitions permitted on small bounded
  controls (v2.0 contradicted its own skeleton and hover primitives).

## Bugs fixed from v2.0 (all were real defects)
1. `color+'40'` alpha only worked on 6-digit hex while brand tokens were HSL → `alpha()` helper.
2. Theme flash: Alpine-time resolution → synchronous `<head>` script.
3. Fake auto mode: persisted the detected system theme, never followed OS → 3-state `auto`+listener.
4. `<meta name="color-scheme">` does not bind native controls → per-theme `color-scheme:` property.
5. Light tokens were the inverse of the prose → page greys, surfaces whiten.
6. `--text-tertiary:#818b98` failed 4.5:1 on white at 11px → `#6a737d` + 12px axis labels.
7. "Bar chart y-axis at zero" → **value** axis (x on horizontal bars).
8. "smooth on for dense" → `smooth:false` default; interpolation is semantic, not density-driven.
9. `[tabindex]` outlined `tabindex="-1"` containers → `:not([tabindex^="-"])`.
10. 3:1 on *all* borders contradicted the muted-border aesthetic → *essential* boundaries only.
11. reduced-motion `.01ms` left infinite animations running → `animation:none` + `scroll-behavior`.
12. `getDataURL()` alone does not print → `beforeprint` `<img>` swap.
13. Print CSS overrode `body` only, leaving cards dark → override at the token layer.
14. ECharts `setOption` merges → `{notMerge:true}` on theme change.
15. One window resize listener per chart → shared `ResizeObserver`.
