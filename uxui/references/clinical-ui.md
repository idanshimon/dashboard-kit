# Clinical / medical UI conventions

Use this when the user-facing surface is a clinician (physician, nurse, advanced
practice provider, registry abstractor, hospital admin). The base uxui design
system applies; this overlay tightens conventions where clinical context demands
it. Failing these conventions in front of a senior physician reads as
"non-clinical software" within seconds — the dashboard loses credibility before
the first chart renders.

## Hard rules — non-negotiable for clinical context

1. **Default to LIGHT theme.** Hospital reading rooms and CICU bays are bright;
   medical records have always been black-on-white. Dark mode is opt-in only
   (on-call rooms, 3am pages). Do not invert this.

2. **No emoji anywhere in production UI.** Lucide icons only. Emoji reads as
   non-serious in clinical context — not appropriate for a mortality score.

3. **Every numeric output ships with its unit.** `4.2 mmol/L`, never bare `4.2`.
   No exceptions, including in tables and stat cards. Render units in muted
   color (`var(--text-secondary)`), value in primary. Same applies to %, mmHg,
   bpm, mg/dL, etc.

4. **Every prediction ships with calibration context.** Show "well-calibrated
   in this subgroup" / "n=143 SCAI-C cases, AUROC 0.84, ECE 0.04" near the
   point estimate. A bare probability is not credible to a senior clinician.
   Link to a per-case explanation page (SHAP for that prediction) from every
   surfaced score.

5. **Density is tunable, not fixed.** Senior physicians want dense; nurses want
   sparse; med students want labeled. Provide a `data-density` toggle on
   `<html>` and design rows to honor `--row-py` / `--row-px`. Three levels:
   `comfortable` (default), `compact`, `dense`. The toggle should persist
   per-user.

6. **Color semantics are clinical, not generic.**
   - red = critical / mortality / shock urgency
   - amber = at-risk / deterioration trajectory
   - blue = stable / accent / informational
   - green = improving / on therapy / recovering
   - purple = mechanical circulatory support / device (Impella / IABP / VA-ECMO / LVAD)
   - slate = unknown / unavailable / pre-data

7. **WCAG AA minimum, AAA where feasible.** Senior clinicians work long shifts;
   under-contrast text loses to fatigue. Test the dashboard at 25% display
   brightness — that's the night-shift reality.

8. **Synthetic-data badges are mandatory in pre-production.** Until the
   dashboard reads real patient data with BAA + IRB executed, every page
   header carries a discreet but visible pill: "Synthetic data only — DUA
   airgap active" or equivalent. Drop the badge only after legal sign-off.

9. **Predictions are decision SUPPORT, not authority.** Every prediction-bearing
   component carries a footer line: "Clinical decision belongs to the bedside
   team" or equivalent. This shapes the whole product tone: "AI surfaces
   patterns for the physician to weigh," not "AI tells doctor what to do."

10. **No inferred PHI.** Never construct an identifier the source data didn't
    explicitly carry (age + sex + admission date is sometimes enough to
    re-identify in small cohorts). De-identification is a code-level boundary,
    not a UI concern — but the UI must not violate it.

## Clinical design tokens (additive to uxui base)

Drop these on top of the uxui `:root` block. Override the base background /
foreground / surface tokens to flip the default to light:

```css
:root {
  /* Default light, clinical-environment friendly */
  --background: #fafbfc;
  --foreground: #0f172a;            /* slate-900 */
  --surface: #ffffff;
  --surface-elevated: #f8fafc;      /* slate-50 */
  --border: #e2e8f0;                /* slate-200 */
  --border-muted: #f1f5f9;          /* slate-100 */
  --muted-foreground: #64748b;      /* slate-500 */
  --primary: #1e40af;               /* blue-800 — clinical, calm */

  /* Clinical semantic colors (must pass WCAG AA on white) */
  --critical: #dc2626;              /* mortality / shock / urgent */
  --atrisk: #d97706;                /* deterioration risk */
  --improving: #059669;             /* recovering on therapy */
  --device: #7c3aed;                /* MCS / Impella / ECMO / LVAD */

  /* SCAI shock-stage palette (cardiology) */
  --scai-a: #84cc16;                /* lime — at risk */
  --scai-b: #facc15;                /* yellow — beginning */
  --scai-c: #f97316;                /* orange — classic */
  --scai-d: #ef4444;                /* red — deteriorating */
  --scai-e: #7f1d1d;                /* dark red — extremis */
}

.dark {
  /* Dark theme — opt-in only, on-call rooms / 3am pages */
  --background: #0b1220;
  --foreground: #e2e8f0;
  --surface: #111a2e;
  --surface-elevated: #1a2540;
  --primary: #3b82f6;
  /* clinical semantic colors stay mostly the same on dark — adjust for contrast only */
}

/* Density tuning — bind row padding to data-density on <html> */
[data-density="comfortable"] { --row-py: 0.75rem;  --row-px: 1rem;    }
[data-density="compact"]     { --row-py: 0.375rem; --row-px: 0.75rem; }
[data-density="dense"]       { --row-py: 0.25rem;  --row-px: 0.5rem;  }
```

## Component patterns specific to clinical

### Severity / stage badges
Don't reach for the generic `Badge`. Clinical staging vocabularies (SCAI shock,
NYHA HF class, AKI stage, CKD stage, SOFA score band, GCS band) are
fixed-vocabulary and must map to immutable color schemes. Drift between
"SCAI C" rendered orange in one place and red in another loses trust instantly.

```tsx
<ScaiBadge stage="C" />        // → orange "C · Classic"
<NyhaBadge class="III" />      // → amber "NYHA III"
<AkiStageBadge stage="2" />    // → orange "AKI Stage 2"
```

Each clinical badge component owns its mapping in one file; the generic Badge
handles non-clinical cases.

### Watch-list / risk-stratified tables
- Sort by deterioration / risk score descending by default
- Three-color score pill: red ≥ critical-threshold, amber ≥ at-risk-threshold,
  green below at-risk-threshold
- Always include Δ (delta) over a clinically-meaningful window (4h for acute
  ICU, 12h for step-down, 24h for ward). Color the delta independently from the
  score — improving Δ on a still-critical score matters
- Vital signs columns: arrow indicators for trajectory (↑↓→) plus the value;
  highlight values out of range (red for HR > 120 or < 50, MAP < 65, lactate ≥
  4, etc.) inline
- Click-through to per-patient detail page is mandatory; a watch-list with no
  drill-down is a disposable demo

### Patient list rows
- Header line: initials · age · sex (`J.M. · 64M`)
- Sub line: synthetic patient ID OR (post-BAA) MRN — never both
- Primary diagnosis must truncate cleanly with a `title=` tooltip carrying the
  full string
- Notes column truncates similarly; one line of clinical context is more
  useful than three lines of noise

### Stat cards in clinical dashboards
Always include:
- The metric label (`Active patients`, `Critical / SCAI D-E`)
- The value with its unit (`12`, `5 / 100`, `38 hrs`)
- A single hint line — what this number actually means in clinical workflow
  (`Eyes-on candidates`, not `count of patients with score >= 80`)
- Tone variant (`critical` / `atrisk` / `improving` / `device` / `default`)
  to color the value and icon

Avoid:
- Sparkline-only deltas without numeric context
- Trend percentages without an explicit direction-is-good vs direction-is-bad
  label (mortality going up is bad; "improving" rate going up is good — color
  must reflect the clinical, not arithmetic, direction)

### Charts in clinical context
Prefer in this order:
1. **Ranked tables with score pills + delta** — most clinically useful, best
   information density, accessible
2. **Calibration curves and ROC curves** — clinicians know these from JAMA /
   NEJM; render them on every model card
3. **Decision-curve analysis (DCA)** — net benefit at threshold; this is the
   chart that wins arguments with cardiology fellows because it answers "is
   using this model better than treating everyone or no one"
4. **Stacked area for cohort trajectory over time** — fine for program-level
   overview
5. **Gauges** — only for a single hero KPI, never as the primary risk surface;
   they look executive, not clinical

### Per-prediction explanations
Every surfaced prediction has a "why" link. The destination shows:
- The patient's input feature values (what the model saw)
- SHAP top features for THIS prediction (not just global SHAP)
- The cohort-level calibration plot with this patient's predicted probability
  marked
- The decision-curve net benefit at this prediction's threshold

## Anti-patterns (will lose physician trust on contact)

- **Toast-only error reporting.** Clinicians work across multiple windows; a
  toast that fades after 5s is gone before they look back. Use persistent
  inline errors near the trigger plus a toast for the moment-of-action signal.
- **Auto-refresh that destroys scroll position.** A nurse reviewing a patient
  list at row 30 should not be reset to row 0 every 30s when the model
  re-scores. Use diff-based updates, or pause auto-refresh on user interaction.
- **"Smart defaults" that hide what the model is doing.** Clinicians must be
  able to inspect every input that drove a prediction. Never collapse the
  feature panel by default on the per-case page.
- **Confidence intervals shown only on hover.** A point-estimate-only mortality
  prediction is a malpractice claim waiting to happen. Show CI inline by
  default; let users hide it if density is the priority, but it's on by default.
- **Color as the only indicator of severity.** Always pair color with text
  ("Critical", "At risk", "Improving") or with shape/position. Color-vision
  limitations are common; long shifts under bright light reduce color
  discrimination further.
- **Generic "no data" states.** "No patients found" is fine for empty cohorts;
  for missing model output it should say "Model has not yet scored this patient
  — try refreshing in 60s" or "Model unavailable for this cohort (n < 50)" with
  the actual reason.

## Worked example — SBM Cardiology POC, 2026-06-06

Project: `~/projects/stony-brook-cardiology-poc/web/` — Next.js 16 App Router +
Tailwind v4 + ECharts.

Implements:
- `src/app/globals.css` — clinical light defaults + SCAI palette + density tuning
- `src/app/layout.tsx` — `data-density="comfortable"` on `<html>`
- `src/components/ui/badge.tsx` — generic Badge + `ScaiBadge` with stage→color mapping
- `src/components/ui/stat-card.tsx` — clinical stat card with tone variants
- `src/components/layout/top-bar.tsx` — synthetic-data warning pill
- `src/app/page.tsx` (Overview) — KPIs + cohort-trajectory stack + watch-list with
  three-color score pills + Δ4h
- `src/app/cohort/live/page.tsx` — full filterable patient table with vital
  signs trajectory arrows
- `src/app/models/page.tsx` — ROC + calibration + SHAP + DCA on every model card

The synthetic-data badge appears on every page header. Predictions all carry
"Clinical decision belongs to the bedside team" copy in their parent card
footer. Score pills are uniform across pages. Charts default to ranked tables;
ECharts renders the DCA / ROC / calibration as ground truth for model
credibility.

## When to break these rules

- Rapid throwaway prototype for an internal-only conversation: drop the
  synthetic-data badge, simplify the density toggle, skip the calibration
  context. But never drop unit-on-every-number or no-emoji.
- Patient-facing surfaces (different audience entirely): different design
  system, simpler vocabulary, explicit "this is decision support, not medical
  advice" disclaimers. The conventions above are clinician-facing.
- Animation-heavy demos for executive audiences: the executive eye prefers
  motion; the clinical eye prefers stillness and information density. If you
  must add animation for an exec demo, gate it behind a feature flag so the
  clinical version stays calm.
