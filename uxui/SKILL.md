---
name: uxui
version: 2.1.0
description: Use when building any UI — dashboards, explainers, charts, data visualizations, HTML pages, or anything user-facing. Provides design system, component library (CDN), chart configs, responsive patterns, and professional dark-theme aesthetics.
triggers:
  - dashboard
  - chart
  - graph
  - visualization
  - UI
  - UX
  - frontend
  - HTML page
  - explainer
  - dark theme
  - responsive
  - mobile friendly
  - icons
  - design system
role: specialist
scope: implementation
output-format: code+design
---

# UX/UI Design System — Single-File HTML

## 🚦 v2.1 WORKFLOW — DO THIS, not "copy TEMPLATE.html"

**The generic-AI-dashboard problem lives in page COMPOSITION, not the skin.** Tokens and polish
do not fix it. Four steps:

1. **Write the manifest FIRST** (`references/manifest.md`) — artifact_class, audience,
   primary_question, data_lifecycle, data_semantics, provenance, density per region, chart
   rationale, overrides. Emit it as an HTML comment and state it to the user. Skipping this is
   how you end up with a card grid regardless of how much guidance you read.
2. **Copy the ARCHETYPE template** — `templates/{executive|operational|analytical|narrative}.html`.
   They share `_core.css`/`_core.js` and differ only in page geometry. There is no generic one.
3. **Build**, consulting references by topic. Read `composition.md` §0 PRECEDENCE first.
4. **Run the validator** — `python3 scripts/validate.py artifact.html`. Exit 0 required.
   Paste the output. Do NOT claim compliance from self-assessment.

### PRECEDENCE (resolves every rule collision)
correctness/domain semantics → accessibility/safety → task completion → information hierarchy →
responsive → aesthetic consistency → decorative polish.
An ops console overrides "one hero". A clinical threshold overrides the color budget.
Any override goes in the manifest's `overrides:` block with a reason.

### ANTI-INFLATION (defects, not style opinions)
No invented deltas/trends/forecasts · no fake "last updated" · no unreachable loaders or retry
buttons for bundled data · no dead export/share/refresh · no sidebar <3 destinations · no tabs
<2 views · no KPI card restating an adjacent chart · placeholders visibly labeled · derived
values marked as derived.

### Archetype defaults (NOT global rules)
- **One hero per screen** — executive/narrative only. Operational uses two independent channels:
  importance (position/size, author-time) and urgency (color/icon, runtime data-driven).
- **Density** is per component family/region, not per page. Forbidden only among peers.
- **Brand** is a user input, never inferred from domain. Default `github`.

### Files
`references/` manifest · composition · charts · theming · polish
`templates/` _core.css · _core.js · executive · operational · analytical · narrative
`scripts/validate.py` — 30 static checks
`openspec/changes/2026-09-uxui-v2-taste-layer/` — proposal, GPT-5.6-sol review, full changelog


**Use this skill for one-off, single-file HTML artifacts: dashboards, explainers, charts, setup guides, reports, data visualizations served from a file, GitHub Pages, or a static directory.**

## When to ESCALATE — DO NOT use this skill

If the user's brief signals ANY of the following — STOP, do not write single-file HTML, escalate to a real framework stack:

- "swap-friendly" / "we'll be adding components" / "replace components later"
- "audience: developers + product people" / "audience: engineers / PMs"
- "professional" / "amazing" / "production-grade"
- "abstracted properly" / "structured properly"
- "this is a real product surface" / "the UI for our system" / "the operator dashboard"
- multi-page navigation, operator dashboards, or anything someone will iterate on for weeks
- the deliverable lives in a repo that someone else maintains alongside backend code

For those briefs, load the **`shadcn-ui` skill** (production-grade primitives, type-safe API layer, swappable design system, Container Apps deployable) plus **`claude-design`** (process and taste, brief framing, variants). A single-file HTML page cannot be made "abstracted properly so we can replace components later" — that's an architectural request, not a styling one. Trying to retrofit single-file HTML into a real component architecture is wasted work; the user will reject it.

**Caught the hard way 2026-06-06**: user asked for a UI that "needs to be flexible because we will be adding components" with "audience are developers + product people" and "abstracted properly so we can replace components". The right answer was Next.js 16 + shadcn primitives + token system in `lib/design/` + typed API client in `lib/api/{service}/client.ts` + domain components on top of UI primitives — NOT a single-file HTML dashboard. The instinct to load this skill on the word "dashboard" was wrong; the brief was an architectural ask, not a styling ask.

The remainder of this skill is for SKETCHES, REPORTS, and one-off artifacts that someone reads once and never iterates on.

## 📁 Skill Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Full design system reference (this file) |
| `COMPLIANCE.md` | Pre-delivery checklist — run before shipping any HTML |
| `TEMPLATE.html` | Ready-to-copy starter template with all tokens + components |
| `openspec/INDEX.md` | Formal specifications for each design system capability |
| `openspec/specs/` | Individual specs: design-tokens, components, icons, charts, layout, interactivity |
| `references/clinical-ui.md` | Clinical / medical UI overlay — light-default theme, no emoji, density toggle, units always shown, calibration context next to predictions, SCAI palette, decision-support not authority. Load this when the audience is a clinician (physician, nurse, registry abstractor, hospital admin). |

**Workflow:** Copy `TEMPLATE.html` → build your page → check against `COMPLIANCE.md` → deliver.

**For architectural changes to the design system itself:** Write a change proposal in `openspec/changes/` first.

## ⚡ Quick Stack (CDN, Zero Build)

```html
<!-- Design system: always include these -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lucide-static@latest/font/lucide.min.css">
<script src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js" defer></script>

<!-- Charts (pick one based on need) -->
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<!-- OR for trading/time series: -->
<script src="https://cdn.jsdelivr.net/npm/lightweight-charts@4/dist/lightweight-charts.standalone.production.js"></script>
<!-- OR for simple charts: -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>

<!-- Diagrams (if needed) -->
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
```

## 🎨 Design Tokens (MANDATORY)

Every HTML file MUST start with these CSS variables. This is our design system — never hardcode colors.

```css
:root {
  /* Backgrounds */
  --bg-primary: #0d1117;
  --bg-surface: #161b22;
  --bg-elevated: #1c2128;
  --bg-overlay: #2d333b;
  
  /* Borders */
  --border-default: #30363d;
  --border-muted: #21262d;
  --border-accent: rgba(88,166,255,0.4);
  
  /* Text */
  --text-primary: #e6edf3;
  --text-secondary: #8b949e;
  --text-tertiary: #6e7681;
  --text-link: #58a6ff;
  
  /* Semantic colors */
  --color-accent: #58a6ff;
  --color-success: #3fb950;
  --color-warning: #d29922;
  --color-danger: #f85149;
  --color-info: #58a6ff;
  --color-purple: #bc8cff;
  --color-pink: #f778ba;
  --color-orange: #d18616;
  
  /* Accent backgrounds (for badges, highlights) */
  --accent-bg: rgba(88,166,255,0.1);
  --success-bg: rgba(63,185,80,0.1);
  --warning-bg: rgba(210,153,34,0.1);
  --danger-bg: rgba(248,81,73,0.1);
  
  /* Spacing scale (4px base) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --space-8: 32px;
  --space-10: 40px;
  --space-12: 48px;
  --space-16: 64px;
  
  /* Typography */
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  --font-mono: 'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace;
  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1rem;     /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.5rem;    /* 24px */
  --text-3xl: 1.875rem;  /* 30px */
  
  /* Radius */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.3);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg: 0 8px 24px rgba(0,0,0,0.5);
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-normal: 250ms ease;
}
```

## 📐 Base Reset (MANDATORY)

```css
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--font-sans);
  background: var(--bg-primary);
  color: var(--text-primary);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--text-link); text-decoration: none; }
a:hover { text-decoration: underline; }
```

## 🧱 Component Library

### Card
```css
.card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
}
.card-header { margin-bottom: var(--space-4); }
.card-title { font-size: var(--text-lg); font-weight: 600; }
.card-subtitle { font-size: var(--text-sm); color: var(--text-secondary); margin-top: var(--space-1); }
```

### Stat Card (KPI)
```css
.stat-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  padding: var(--space-5) var(--space-6);
}
.stat-label { font-size: var(--text-sm); color: var(--text-secondary); display: flex; align-items: center; gap: var(--space-2); }
.stat-value { font-size: var(--text-2xl); font-weight: 700; margin-top: var(--space-1); }
.stat-change { font-size: var(--text-sm); margin-top: var(--space-1); }
.stat-change.positive { color: var(--color-success); }
.stat-change.negative { color: var(--color-danger); }
```

### Badge
```css
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 600;
}
.badge-success { background: var(--success-bg); color: var(--color-success); }
.badge-warning { background: var(--warning-bg); color: var(--color-warning); }
.badge-danger { background: var(--danger-bg); color: var(--color-danger); }
.badge-info { background: var(--accent-bg); color: var(--color-accent); }
.badge-neutral { background: var(--bg-overlay); color: var(--text-secondary); }
```

### Table
```css
.table { width: 100%; border-collapse: collapse; font-size: var(--text-sm); }
.table th {
  text-align: left;
  padding: var(--space-3) var(--space-4);
  background: var(--bg-elevated);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-default);
}
.table td {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--border-muted);
}
.table tr:hover td { background: rgba(88,166,255,0.04); }
```

### Nav / Tabs
```css
.nav { display: flex; gap: var(--space-1); border-bottom: 1px solid var(--border-default); padding: 0 var(--space-4); }
.nav-item {
  padding: var(--space-3) var(--space-4);
  font-size: var(--text-sm);
  color: var(--text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: var(--transition-fast);
}
.nav-item:hover { color: var(--text-primary); }
.nav-item.active { color: var(--text-primary); border-bottom-color: var(--color-accent); }
```

### Button
```css
.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  border: 1px solid var(--border-default);
  background: var(--bg-surface);
  color: var(--text-primary);
  transition: var(--transition-fast);
}
.btn:hover { background: var(--bg-elevated); border-color: var(--text-secondary); }
.btn-primary { background: var(--color-accent); color: var(--bg-primary); border-color: var(--color-accent); }
.btn-primary:hover { opacity: 0.9; }
/* Semantic buttons (danger/success/warning) use a TONAL treatment, NOT a
   full-saturation fill — a solid neon green/red on a dark theme reads as
   "horrible blinding" (real user reaction), especially several on screen at once.
   Soft tinted bg + saturated colored text + colored border at rest; fill to solid
   only on :hover. Reserve the solid fill for the ONE primary CTA. */
.btn-danger { background: var(--danger-bg); color: var(--color-danger); border-color: var(--color-danger); }
.btn-danger:hover { background: var(--color-danger); color: #fff; }
.btn-success { background: var(--success-bg); color: var(--color-success); border-color: var(--color-success); }
.btn-success:hover { background: var(--color-success); color: #fff; }
.btn-ghost { background: transparent; border-color: transparent; }
.btn-ghost:hover { background: var(--bg-surface); }
.btn-sm { padding: var(--space-1) var(--space-3); font-size: var(--text-xs); }

/* TONAL semantic buttons — use these for paired success/danger actions
   (Approve/Deny, Confirm/Delete). A full-saturation green/red FILL on a dark
   theme is blinding (caught the hard way: user reaction to solid Approve/Deny
   buttons was literally "horrible blinding"). The fix: soft tint background +
   saturated text + a 1px colored border at rest; fill solid only on :hover.
   Calm at rest, unmistakable intent, readable on BOTH themes. Reserve the loud
   solid fill for the single primary CTA (.btn-primary) — never for a row of
   destructive/confirm buttons. */
.btn-success-tonal { background: var(--success-bg); color: var(--color-success); border-color: var(--color-success); }
.btn-success-tonal:hover { background: var(--color-success); color: var(--bg-primary); }
.btn-danger-tonal  { background: var(--danger-bg);  color: var(--color-danger);  border-color: var(--color-danger); }
.btn-danger-tonal:hover  { background: var(--color-danger);  color: #fff; }
/* React/inline-style equivalent: bg = *-bg token, color = saturated token,
   border = 1px saturated token; on mouseenter swap bg→saturated + text→on-accent. */
```

### Progress Bar
```css
.progress { height: 8px; background: var(--bg-overlay); border-radius: var(--radius-full); overflow: hidden; }
.progress-fill { height: 100%; border-radius: var(--radius-full); transition: width var(--transition-normal); }
.progress-fill.success { background: var(--color-success); }
.progress-fill.warning { background: var(--color-warning); }
.progress-fill.danger { background: var(--color-danger); }
```

### Toast / Alert
```css
.alert {
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
}
.alert-info { background: var(--accent-bg); border-left: 3px solid var(--color-accent); }
.alert-success { background: var(--success-bg); border-left: 3px solid var(--color-success); }
.alert-warning { background: var(--warning-bg); border-left: 3px solid var(--color-warning); }
.alert-danger { background: var(--danger-bg); border-left: 3px solid var(--color-danger); }
```

## 📊 Chart Configurations

### ECharts (recommended for dashboards)
```javascript
// Base theme for ALL ECharts instances
const ECHARTS_THEME = {
  backgroundColor: 'transparent',
  textStyle: { color: '#8b949e', fontFamily: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif' },
  title: { textStyle: { color: '#e6edf3' } },
  legend: { textStyle: { color: '#8b949e' } },
  xAxis: { axisLine: { lineStyle: { color: '#30363d' } }, splitLine: { lineStyle: { color: '#21262d' } }, axisLabel: { color: '#8b949e' } },
  yAxis: { axisLine: { lineStyle: { color: '#30363d' } }, splitLine: { lineStyle: { color: '#21262d' } }, axisLabel: { color: '#8b949e' } },
  tooltip: { backgroundColor: '#1c2128', borderColor: '#30363d', textStyle: { color: '#e6edf3' } },
  color: ['#58a6ff', '#3fb950', '#d29922', '#f85149', '#bc8cff', '#f778ba', '#d18616', '#79c0ff'],
};

// Apply: chart.setOption({ ...ECHARTS_THEME, ...yourOptions });
```

### Chart.js (if already in project)
```javascript
const CHARTJS_DEFAULTS = {
  color: '#8b949e',
  borderColor: '#30363d',
  backgroundColor: 'transparent',
  font: { family: '-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif' },
};
Chart.defaults.color = '#8b949e';
Chart.defaults.borderColor = '#30363d';
Chart.defaults.font.family = CHARTJS_DEFAULTS.font.family;

// Palette for datasets
const PALETTE = ['#58a6ff', '#3fb950', '#d29922', '#f85149', '#bc8cff', '#f778ba', '#d18616'];
```

### Lightweight Charts (trading/time series)
```javascript
const chart = LightweightCharts.createChart(el, {
  layout: { background: { color: 'transparent' }, textColor: '#8b949e' },
  grid: { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
  crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
  rightPriceScale: { borderColor: '#30363d' },
  timeScale: { borderColor: '#30363d' },
});
```

## 🔤 Icons — Lucide (MANDATORY, no emoji)

Use Lucide icons via CSS font (no JS needed):
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lucide-static@latest/font/lucide.min.css">

<!-- Usage -->
<i class="lucide-trending-up"></i>
<i class="lucide-alert-triangle"></i>
<i class="lucide-check-circle"></i>
<i class="lucide-bar-chart-3"></i>
<i class="lucide-users"></i>
<i class="lucide-calendar"></i>
<i class="lucide-target"></i>
<i class="lucide-activity"></i>
<i class="lucide-git-branch"></i>
<i class="lucide-shield-check"></i>

<!-- Sizing -->
<i class="lucide-check-circle" style="font-size: 1.2rem;"></i>
```

**Common icon mappings:**
| Concept | Icon |
|---------|------|
| Revenue / Money | `lucide-dollar-sign` or `lucide-trending-up` |
| Success / Complete | `lucide-check-circle` |
| Warning / Risk | `lucide-alert-triangle` |
| Error / Critical | `lucide-alert-circle` |
| Activity / Task | `lucide-activity` |
| Calendar / Date | `lucide-calendar` |
| Account / Customer | `lucide-building-2` |
| User / Person | `lucide-user` |
| Team | `lucide-users` |
| Chart / Data | `lucide-bar-chart-3` |
| Target / Goal | `lucide-target` |
| Settings | `lucide-settings` |
| Search | `lucide-search` |
| Filter | `lucide-filter` |
| Download | `lucide-download` |
| Refresh | `lucide-refresh-cw` |
| External link | `lucide-external-link` |
| Copy | `lucide-copy` |
| Git | `lucide-git-branch` |
| Shield / Security | `lucide-shield-check` |
| Milestone | `lucide-flag` |
| Pipeline | `lucide-git-merge` |

Full icon list: https://lucide.dev/icons

## 📱 Responsive Layout

### Diagnosing mobile text overflow

Verify phone layout at a REAL mobile viewport (playwright-core with Chrome `executablePath`, viewport 390x844 with `isMobile`): assert `documentElement.scrollWidth == clientWidth` and count `img.complete && naturalWidth==0`, and log `requestfailed` events. Headless Chrome `--window-size=<500` screenshots are not phone evidence, because the window has a minimum width and the capture shows false right-edge clipping. Burst image failures (`ERR_CONNECTION_RESET`) from a Python static server mean the default listen backlog of 5 is too small; serve with a `ThreadingHTTPServer` subclass that sets `request_queue_size=128`.

Card grids: use `minmax(min(150px,100%),1fr)`, never a fixed min wider than half a phone, or two columns overflow.

When `scrollWidth > clientWidth` but every element's bounding box fits, inspect text-node `Range.getClientRects()` outside intentional scroll containers. A long URL in a plain metadata span can paint beyond its correctly sized box; give that semantic text class `overflow-wrap:anywhere` rather than hiding page overflow. Treat horizontally scrollable navigation as a separate usability question; a native collapsed contents menu can be clearer in a long mobile report.

### Container
```css
.container { max-width: 1200px; margin: 0 auto; padding: 0 var(--space-4); }
.container-wide { max-width: 1440px; margin: 0 auto; padding: 0 var(--space-4); }
```

### Grid System
```css
.grid { display: grid; gap: var(--space-4); }
.grid-2 { grid-template-columns: repeat(2, 1fr); }
.grid-3 { grid-template-columns: repeat(3, 1fr); }
.grid-4 { grid-template-columns: repeat(4, 1fr); }
.grid-auto { grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); }

/* Mobile-first responsive */
@media (max-width: 768px) {
  .grid-2, .grid-3, .grid-4 { grid-template-columns: 1fr; }
  .hide-mobile { display: none; }
}
@media (min-width: 769px) and (max-width: 1024px) {
  .grid-3, .grid-4 { grid-template-columns: repeat(2, 1fr); }
}
```

### Dashboard Layout
```css
.dashboard {
  display: grid;
  grid-template-rows: auto 1fr;
  min-height: 100vh;
}
.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--border-default);
  background: var(--bg-surface);
  position: sticky;
  top: 0;
  z-index: 100;
}
.dashboard-body { padding: var(--space-6); }

@media (max-width: 768px) {
  .dashboard-header { padding: var(--space-3) var(--space-4); }
  .dashboard-body { padding: var(--space-4); }
}
```

## 🎯 Interactivity with Alpine.js

```html
<script src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js" defer></script>

<!-- Tabs -->
<div x-data="{ tab: 'overview' }">
  <div class="nav">
    <div class="nav-item" :class="{ active: tab === 'overview' }" @click="tab = 'overview'">Overview</div>
    <div class="nav-item" :class="{ active: tab === 'details' }" @click="tab = 'details'">Details</div>
  </div>
  <div x-show="tab === 'overview'">...</div>
  <div x-show="tab === 'details'" x-cloak>...</div>
</div>

<!-- Toggle -->
<div x-data="{ expanded: false }">
  <button @click="expanded = !expanded" class="btn btn-ghost">
    <span x-text="expanded ? 'Show less' : 'Show more'"></span>
  </button>
  <div x-show="expanded" x-collapse>Hidden content</div>
</div>

<!-- Search/Filter -->
<div x-data="{ search: '', items: [...] }">
  <input type="text" x-model="search" placeholder="Filter..." class="input">
  <template x-for="item in items.filter(i => i.name.toLowerCase().includes(search.toLowerCase()))">
    <div x-text="item.name"></div>
  </template>
</div>
```

**Always add `x-cloak` CSS:**
```css
[x-cloak] { display: none !important; }
```

## 🔗 URL State Persistence (MANDATORY for filterable/tabbed surfaces)

**The test:** copy the URL → open in a new tab → you see the identical view (same tab, filters, sort, open modal). If you don't, the page is broken. Users bookmark views, share links, and reload — the URL is the single source of truth for "what am I looking at," not `localStorage` and not in-memory JS variables.

**What goes in the URL:** active tab, every active filter, sort column + direction, search query, selected row / open detail modal, pagination offset. Anything a control changes.

**What does NOT:** live data, transient hover state, draft form input (that's localStorage — see Modal Draft Persistence), one-frame animations.

### Pattern A — hash router (vanilla, no framework; what a trading dashboard uses)

Encode state as a query string on the hash: `#expected-moves?tier=monthly&filter=indices&sym=SPY`. One tiny helper, shared across pages:

```javascript
// js/lib/url-state.js — read/write the ?query segment of the hash
window.BT = window.BT || {};
BT.urlState = {
  // returns {tier:'monthly', filter:'indices', ...} from #route?tier=monthly&filter=indices
  read: function() {
    var q = (location.hash.split('?')[1] || '');
    var out = {};
    q.split('&').forEach(function(kv){ if(!kv) return; var p=kv.split('='); out[decodeURIComponent(p[0])]=decodeURIComponent(p[1]||''); });
    return out;
  },
  // merge patch into current state; null/'' value deletes the key. Uses replaceState so
  // filter flips DON'T spam browser history (back button should leave the page, not undo 9 filter clicks).
  update: function(patch, pushHistory) {
    var route = (location.hash.replace(/^#\/?/,'').split('?')[0]) || '';
    var st = BT.urlState.read();
    Object.keys(patch).forEach(function(k){ (patch[k]===null||patch[k]==='') ? delete st[k] : st[k]=patch[k]; });
    var qs = Object.keys(st).map(function(k){ return encodeURIComponent(k)+'='+encodeURIComponent(st[k]); }).join('&');
    var newHash = '#'+route+(qs?'?'+qs:'');
    if (location.hash === newHash) return;
    if (pushHistory) location.hash = newHash;
    else history.replaceState(null,'','#'+route+(qs?'?'+qs:''));
  }
};
```

Wiring rules on each page:
1. **On init/render:** read the URL FIRST, fall back to `localStorage`/default only when the URL is silent. `var tier = BT.urlState.read().tier || BT.preferences.getPref('emTier') || 'weekly';`
2. **On every control change:** `BT.urlState.update({tier: newTier})` — then re-render. Persist to localStorage too if you want a per-device default, but the URL write is what makes the view shareable.
3. **router.js already tolerates it:** `parseHash()` strips `?…` before matching the route, so `#expected-moves?tier=monthly` still resolves to the `expected-moves` page. New pages get URL state for free once they read `BT.urlState` in their `render`/`init`.
4. **Opening a detail modal** sets `?sym=SPY`; closing it clears the key. On load, if `sym` is present, auto-open that modal — that's what makes a shared link land on the open row.

### Pattern B — Next.js App Router (the escalated stack)

Use `useSearchParams` + `router.replace` (NOT `push` for filters) so the URL is the state store:

```tsx
'use client';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
export function useUrlState() {
  const sp = useSearchParams(); const router = useRouter(); const pathname = usePathname();
  const set = (patch: Record<string,string|null>) => {
    const next = new URLSearchParams(sp.toString());
    for (const [k,v] of Object.entries(patch)) v===null || v==='' ? next.delete(k) : next.set(k,v);
    router.replace(`${pathname}?${next.toString()}`, { scroll: false }); // replace, not push
  };
  return { get: (k:string)=>sp.get(k), set };
}
// Read on render: const tab = get('tab') ?? 'overview';  Filter changes: set({ tab:'runs', plane:'standards' })
```

**Rule of thumb (both patterns):** filter/tab changes use `replaceState`/`router.replace` (no history spam); a genuine *navigation* (open a different record's page) uses `pushState`/`router.push` so Back works intuitively. Caught the hard way: wiring every filter click to `push` makes the Back button cycle through filter states instead of leaving the page — users hate it.

## 🏗️ Architecture — Performance & Maintainability

### File Extraction for Large Dashboards
When a single-file HTML exceeds ~1,500 lines or ~100KB, extract into separate files:

```
src/dashboard/
├── style.css       # All CSS — served as <link> with Cache-Control
├── app.js          # Alpine.js data + methods — served as <script src>
├── index.html      # HTML shell — server-side interpolation for dynamic values
```

**Proven reference:** MSX SE Hero (`msx-se-helper/src/dashboard/`) — 1,343-line HTML + 935-line JS + external CSS. Three-file split, gzip, sticky headers, 9 tabs, 4 modals with draft persistence.

**Server-side interpolation pattern:**
- Use `__PLACEHOLDER__` syntax in static files (not template literals)
- Replace at server startup: `html.replace(/__CURRENT_FY__/g, String(CURRENT_FY))`
- Cache the composed result in memory — no disk I/O per request
- Serve CSS/JS as separate routes with `Cache-Control` headers
- Add gzip compression via Node.js `zlib` (160KB → ~16KB)

**Why this matters:**
- Browser caches CSS/JS separately (only HTML re-fetched on reload)
- IDE syntax highlighting works (not JS strings containing HTML)
- Browser DevTools/CDP can interact without timeouts
- Debugging: find code in the right file, not line 2,347 of server.js

### Server-Side vs Browser-Side Variables
**Critical rule:** Template literal variables (`${VAR}`) only exist in Node.js. They are NOT available in the browser `<script>` block.

```javascript
// ❌ WRONG — VAR is undefined in the browser
<script>
  const name = 'FY' + CURRENT_FY;  // ReferenceError!
</script>

// ✅ RIGHT — declare the variable in the script block
<script>
  const CURRENT_FY = __CURRENT_FY__;  // server replaces → const CURRENT_FY = 2026;
  const name = 'FY' + CURRENT_FY;     // works
</script>
```

This is a silent killer — the ReferenceError stops execution but shows no visible error to the user. The button/modal just "doesn't work."

### Alpine.js Naming Collisions
**Never use the same name for a data property and a computed getter.**

Alpine.js getters silently shadow data properties of the same name. No error, no warning — the UI just breaks.

```javascript
// ❌ WRONG — getter shadows the object
return {
  categories: { 1: 'POC', 2: 'Production' },  // data
  get categories() { return [...new Set(...)]; } // getter — kills the object!
}

// ✅ RIGHT — distinct names
return {
  categoryOptions: { 1: 'POC', 2: 'Production' },  // for dropdowns
  get categoryFilters() { return [...new Set(...)]; } // for filter lists
}
```

### Consistent KPI Cards Across Tabs
**KPI summary cards should be visible on ALL tabs, not just the overview.** This gives users persistent context while drilling into any tab. Keep the KPI grid outside tab-specific `x-show` wrappers. Tab-specific content (territory, charts, legends) can stay inside their tab div.

### Clickable App Title → Home
**The app title/logo in the header should always navigate to the overview/home tab.** Users expect brand/title clicks to reset navigation:
```html
<h1 style="cursor:pointer;" @click="tab = 'overview'">App Title</h1>
```

### Sticky Headers — Three-Layer Z-Index Stack
For dashboards with fixed header + sticky nav + sticky table headers:

```css
.dashboard-header { position: sticky; top: 0; z-index: 100; background: var(--bg-surface); }
.nav { position: sticky; z-index: 90; background: var(--bg-primary); } /* top offset = header height */
.table thead { background: var(--bg-elevated); } /* solid fill so rows don't bleed through cell gaps */
.table th { position: sticky; z-index: 2; background: var(--bg-elevated); } /* top offset = header + nav */
```

Use `ResizeObserver` to measure header/nav heights and set `top` offsets dynamically.

⚠️ **Do NOT put `overflow: clip`, `overflow: hidden`, or `overflow: auto` on the `.table-wrap`.** Any of them creates a containing block (clip/hidden) or scroll context (auto) for sticky descendants, which pins the `<thead>` to the wrap instead of the viewport. The thead then visually “unsticks” mid-table on scroll. Leave overflow at its default (`visible`). Border-radius still clips corners because the table is 100% width with no horizontal overflow. If you truly need horizontal scroll, put that scroll container *inside* the sticky-capable wrap, not around it.

### Tooltip Positioning
KPI card tooltips should use `.tooltip-below` to render downward, preventing viewport clipping at page top. Edge-flip logic for tooltips near screen edges.

### Tab Descriptions
Every tab should have a one-line muted description explaining its purpose, visible on hover or as subtitle text. Define these in the tabs array data:
```javascript
tabs: [
  { id: 'overview', label: 'Overview', icon: 'icon-layout-dashboard', tip: 'KPI cards and charts — your territory at a glance' },
  // ...
]
```

## 🗂️ Modal Best Practices

### Draft Persistence (localStorage)
Every modal with user input should persist drafts:

```javascript
// Save on: field change (debounced), outside click, X button, Cancel
saveDraft() {
  localStorage.setItem('prefix-' + this.form.id, JSON.stringify(this.form));
}

// Restore on modal open
openModal(id) {
  const draft = localStorage.getItem('prefix-' + id);
  if (draft) {
    this.form = { ...defaults, ...JSON.parse(draft) };
    this.draftRestored = true;  // show amber banner
  }
}

// Clear on successful submit
clearDraft() {
  localStorage.removeItem('prefix-' + this.form.id);
  this.draftRestored = false;
}
```

**UX pattern:**
- Amber banner: "Unsaved draft restored" + Discard button
- Auto-save on input changes (`@input.debounce.500ms`)
- Save on all close paths (overlay click, X, Cancel)
- Clear only on successful submit
- Key per entity ID (not global) — different forms for different records

### Modal Placement in Alpine.js
Modals must be **inside** the Alpine `x-data` scope. Place them after `</main>` but before the closing `</div>` of the x-data wrapper:

```html
<div x-data="app()">
  <header>...</header>
  <main>...</main>
  <!-- ✅ Modals here — inside x-data scope -->
  <div x-show="showModal" x-cloak class="modal-overlay">...</div>
</div>  <!-- x-data scope ends -->
```

## 📝 UX Microcopy Requirements

**Every feature spec with UI MUST include a UX Microcopy table.** Don't improvise copy at build time — spec it first.

| Element | Copy | Purpose |
|---------|------|---------|
| Tooltip on filter | "Filters to..." | Explains what the filter does |
| Badge hover | "On team — counts toward..." | Confirms meaning |
| Tab description | "All milestones on..." | Orients the user |
| FAQ entry | Updated answer text | Keeps docs accurate |
| Empty state | "No items found..." | Guides next action |
| Error message | "Failed to X because Y. Try Z." | Actionable guidance |

**Rules:**
- Hover text should be **actionable** ("Join the team in MSX if you're actively working this") not just descriptive ("You are not on this team")
- Use (i) info icons with rich tooltips for concepts users need explained (e.g., "My Team Only")
- Update FAQ entries when shipping features — don't leave "coming soon" copy after shipping
- Tab descriptions should include visual legends when badges/icons are used

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Page Title</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lucide-static@latest/font/lucide.min.css">
<script src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js" defer></script>
<style>
  :root { /* paste design tokens */ }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  [x-cloak] { display: none !important; }
  body { font-family: var(--font-sans); background: var(--bg-primary); color: var(--text-primary); line-height: 1.6; -webkit-font-smoothing: antialiased; }
  /* ... components ... */
</style>
</head>
<body>
<div class="dashboard">
  <header class="dashboard-header">
    <div style="display:flex;align-items:center;gap:var(--space-3);">
      <i class="lucide-bar-chart-3" style="color:var(--color-accent);font-size:1.4rem;"></i>
      <h1 style="font-size:var(--text-lg);font-weight:600;">Dashboard Title</h1>
    </div>
    <div style="display:flex;gap:var(--space-2);">
      <button class="btn btn-sm" onclick="refresh()"><i class="lucide-refresh-cw"></i> Refresh</button>
    </div>
  </header>
  <main class="dashboard-body">
    <div class="container-wide">
      <!-- Content -->
    </div>
  </main>
</div>
</body>
</html>
```

## 🖼️ Delivering an HTML artifact as an IMAGE (diagram/explainer sent inline)

When the user wants the artifact *shown in chat* ("send it here", "show me a diagram", a single explainer image to paste into email/Teams) rather than a file to open, render the HTML to a PNG and deliver it inline. Browser tools often can't open `file://` (and the managed CDP browser may not be running), so use **headless Chrome's `--screenshot`** — this is the reliable path:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-sandbox --hide-scrollbars \
  --force-device-scale-factor=1.5 \
  --screenshot=/tmp/diagram.png --window-size=1360,1000 \
  "file:///abs/path/to/diagram.html"
```

- `--force-device-scale-factor=1.5` (or 2) → crisp, retina-quality text; plain 1x looks soft.
- `--window-size=W,H` must be set explicitly and sized to the content (a fixed-width `body{width:1300px}` design + a height guess). Too-short height clips the bottom; iterate the height, don't guess once.
- `--headless=new` is the modern flag; bare `--headless` sometimes writes nothing (silent 0-byte or missing file) — if the PNG doesn't appear, switch to `=new`.
- Then **verify before delivering:** `vision_analyze` the PNG and check for clipped/overlapping/empty regions. Rendering blind and sending a clipped diagram is the common miss.
- Deliver the PNG inline in the reply with a `MEDIA:/tmp/diagram.png` line.
- **Keep the `.html` on disk** — the user iterates fast on explainers ("make it Microsoft-themed", "not PDF, HTML", "add the optional lane"). Each correction is then a `patch` + re-render, not a rebuild. Expect 2–3 correction passes on any diagram.
- **PDF vs HTML/PNG:** a raw `.html` won't preview in email/Teams; if they need an email attachment, offer PDF (`--print-to-pdf`), but for "show me / send it here" the inline PNG is what they want. Ask before assuming PDF — users often explicitly say "not PDF."

**Theming to a brand (e.g. Microsoft/Fluent):** override the dark GitHub tokens with the brand palette — Microsoft = light `--bg:#faf9f8`, Segoe UI, `#0078d4` blue / `#107c10` green / `#5c2d91` purple / `#ca5010` gold, the 4-square logo (`#f25022/#7fba00/#00a4ef/#ffb900`), soft Fluent shadow `0 1.6px 3.6px rgba(0,0,0,.10)`. For explainers with a general audience, build a **generic version by default** (no names, "illustrative — verify against your own data" footer) so it's both send-ready and reusable; keep any named/internal copy separate.

## 📏 Rules

**Before delivering any HTML file, run the compliance checklist:** `COMPLIANCE.md` (same directory as this file).

### Variable Naming — NEVER Abbreviate
The design token names are a contract. Use the FULL names exactly as defined in `:root` above:
- ✅ `var(--bg-primary)` · `var(--text-secondary)` · `var(--border-default)` · `var(--color-accent)`
- ❌ ~~`var(--bg)`~~ · ~~`var(--text)`~~ · ~~`var(--muted)`~~ · ~~`var(--surface)`~~ · ~~`var(--accent)`~~

Abbreviated variable names break the design system. Every file must use the canonical names.

### Hard Rules
1. **NEVER use emoji as icons.** Use Lucide icon font. Emoji is for chat, not professional UI.
2. **NEVER hardcode colors.** Always use CSS variables from the design tokens.
3. **NEVER abbreviate variable names.** Copy the `:root` block verbatim from this file.
4. **ALWAYS include the responsive breakpoints.** Every page must work on mobile.
5. **ALWAYS include the viewport meta tag.** `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
6. **Prefer ECharts for new dashboards.** Chart.js only if already in the project.
7. **Use Alpine.js for interactivity.** No vanilla JS event listeners for UI state. Keep `<script>` for data fetching/charting only.
8. **One font stack.** `-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif` — never monospace for body text.
9. **Spacing scale.** Use `--space-*` variables, never raw pixel values.
10. **Font sizes.** Use `--text-*` variables, never raw rem/px.
11. **Border radius.** Use `--radius-*` variables.
12. **Tables need hover states.** Always add `tr:hover` highlight.
13. **Cards need subtle borders.** `1px solid var(--border-default)`, not box-shadow.
14. **Text hierarchy:** Primary (`--text-primary`) for content, secondary (`--text-secondary`) for labels/meta, tertiary (`--text-tertiary`) for disabled/hints.
15. **Status colors are semantic:** green=success/good, yellow=warning/risk, red=danger/critical, blue=info/accent, purple=special.
16. **URL IS STATE — every filter/tab/selection MUST be in the URL.** A user must be able to copy the address bar and paste it (new tab, bookmark, share with a colleague, reload) and land on the EXACT same view — same tab, same filters, same sort, same selected row/modal. If a control changes what's on screen, it changes the URL. This is non-negotiable for any multi-tab or filterable surface. See the "URL State Persistence" pattern below for the implementation. Corollary: reading a filter from `localStorage` instead of the URL is a bug — localStorage is per-device and un-shareable; it's fine as a *fallback default* when the URL has no state, never as the source of truth.
17. **EVERY action MUST have visual feedback.** Buttons, links, and interactive elements must show the user something is happening:
    - **Buttons triggering async work:** Show a spinner icon (replace the button icon with `lucide-loader` + `animation: spin 1s linear infinite`), disable the button, and change the label (e.g., "Refresh" → "Refreshing...").
    - **Page/section loading:** Show a top progress bar, skeleton placeholders, or a subtle overlay with spinner — never just freeze.
    - **Short actions (<500ms):** At minimum, show a brief opacity flash or scale pulse on the button itself.
    - **Success:** Show a brief green checkmark or success toast, then restore the button.
    - **Error:** Show inline error message near the trigger, not just a console log.

### Loading States Pattern

```css
/* Spinner animation */
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.spin { animation: spin 1s linear infinite; }

/* Top progress bar */
.progress-bar-top {
  position: fixed; top: 0; left: 0; height: 3px; z-index: 9999;
  background: var(--color-accent);
  transition: width var(--transition-normal);
}

/* Button loading state */
.btn[disabled] { opacity: 0.6; cursor: not-allowed; }
.btn .loading-icon { display: none; }
.btn.is-loading .loading-icon { display: inline-block; }
.btn.is-loading .default-icon { display: none; }
```

```html
<!-- Button with loading state (Alpine.js) -->
<button class="btn" @click="doAction()" :disabled="actionLoading">
  <i class="lucide-refresh-cw" x-show="!actionLoading"></i>
  <i class="lucide-loader spin" x-show="actionLoading"></i>
  <span x-text="actionLoading ? 'Loading...' : 'Refresh'"></span>
</button>

<!-- Top progress bar -->
<div class="progress-bar-top" x-show="loading" :style="{ width: loading ? '80%' : '100%' }" x-transition></div>
```

## When single-file HTML is the WRONG shape — escalate to a real frontend stack

The whole skill above defaults to single-file HTML + Alpine.js + CDN scripts because it's the right tool for the **majority** of agent UI work: dashboards, explainers, decks, reports, one-off prototypes, internal tools an engineer will use for a week and discard. Zero build, openable from `file://`, easy to send via chat as a single attachment.

It's the WRONG shape — and forcing it costs the user weeks of rework — when ALL of these are true:

1. **Multi-route surface.** ≥4 distinct pages with navigation between them (`/`, `/runs`, `/decisions`, `/bundles`, `/agents`, `/telemetry`, ...). Single-file HTML can hold 2-3 tabs cleanly; once you're past 4 routes the in-page Alpine `x-show="tab === 'foo'"` pattern becomes a single 3000-line file that no one wants to edit.
2. **Long-lived product.** The user will keep extending it ("we will be adding components"). Single-file HTML can't be safely modified by a parallel agent or a coworker without merge hell.
3. **Component swap-friendliness required.** The user explicitly says "abstracted properly so we can replace components" or "professional and amazing" or "audience is developers + product people" — that's a brief for production-grade component architecture, not for a sketch.
4. **Live backend integration** with auth, SSE, server actions, or API routes. Alpine.js + browser-side `fetch` can do simple GETs; once you need bearer-auth proxies, server-side rendering, streaming SSE with reconnection, or per-route layouts, you're fighting the framework.
5. **Eventual deployment as its own service.** If the deliverable will end up in a Container App, Vercel, or Static Web App with its own CI/CD lane, build it as one from the start — retrofitting later is more work than starting in the right shape.

If ≥3 of those are true, **don't reach for `TEMPLATE.html`** — propose Next.js 15+ + Tailwind v4 + shadcn-style primitives instead, and use the architecture below.

### Architecture for the "real frontend" case

When you escalate, the component taxonomy below is the contract that delivers the user's "swap-friendly + abstracted properly" requirement. Three component layers, three folders, one rule each:

```
src/
├── app/                          ← Next.js App Router pages. Dumb — they consume hooks, render components.
│   ├── layout.tsx                ← ThemeProvider + QueryProvider + AppShell + Toaster
│   ├── page.tsx
│   ├── runs/page.tsx
│   ├── runs/[id]/page.tsx
│   └── api/<name>/route.ts       ← Server-side proxies for bearer-auth backends. See companion skill below.
├── components/
│   ├── ui/                       ← shadcn-style primitives (Button, Card, Badge, Dialog, ...).
│   │                              SWAP THIS DIRECTORY to switch design systems (shadcn → MUI → custom).
│   │                              No pages or domain components import design-system internals;
│   │                              only this folder does. That's how the swap stays a one-folder change.
│   ├── domain/                   ← Semantic components for THIS product
│   │                              (RunCard, DecisionCard, PlaneBadge, StagePill, KpiCard, ...).
│   │                              Built ON TOP of components/ui/. These embed the product's vocabulary.
│   └── layout/                   ← AppShell, Sidebar, TopBar, CommandPalette, PageHeader, Breadcrumbs.
│                                  Shell pieces — every page wraps in <AppShell>.
└── lib/
    ├── api/
    │   ├── config.ts             ← Runtime + buildtime endpoint resolution. window.__APP_CONFIG__
    │   │                            for runtime overrides; falls back to NEXT_PUBLIC_* at build time.
    │   │                            Lets the SAME image target different environments by re-injecting
    │   │                            env vars at deploy time without rebuilding.
    │   ├── <service-a>.ts        ← Typed client for one backend (every endpoint as a typed method).
    │   └── <service-b>.ts        ← Typed client for the next backend.
    ├── hooks/
    │   ├── use-<thing>.ts        ← TanStack Query hooks (one per resource). Pages call hooks, NEVER fetch directly.
    │   └── use-<thing>-stream.ts ← Native EventSource SSE subscriptions when live data is needed.
    ├── query-client.tsx          ← TanStack provider, stale time, refetch on focus.
    ├── types.ts                  ← Domain types mirroring backend schemas. One source of truth.
    └── utils.ts                  ← cn (clsx + tailwind-merge), relativeTime, shortId, fmtUsd, fmtNumber.
```

### The five rules that make this work

1. **Pages are dumb.** They call hooks, pass data to components, handle navigation. They don't `fetch` directly, they don't format dates, they don't compose CSS class strings by hand. Anything reusable lives in `components/` or `lib/`.
2. **`components/ui/` is the swap layer.** Replacing shadcn with MUI is a `components/ui/*` rewrite — every page, every domain component, every layout piece keeps working unchanged because they import `<Button>` from `@/components/ui/button`, not from a third-party package directly.
3. **`components/domain/` carries the product vocabulary.** `<PlaneBadge plane="standards" />` renders the same way everywhere — sidebar, page headers, badges. Hand-coding the violet hex anywhere outside `PlaneBadge` is a code-review block. This is how plane-coding, status semantics, brand chrome stay consistent.
4. **API access goes through `lib/api/<service>/client.ts` + typed hooks.** Adding a new endpoint = one typed method on the client + one hook + page consumption. Three files, no plumbing churn. Backend changes get caught at the type boundary in `lib/types.ts`.
5. **No fake data, no AI slop.** Empty states say "No runs yet" — they don't show synthetic demo data to make the screen look populated. Lucide icons only, no emoji. No gradient hero backgrounds, no glassmorphism, no "Insights / Growth / Scale" generic SaaS copy. The aesthetic posture is Linear / Grafana / GitHub Actions, not marketing landing page.

### Stack pinned (as of 2026-06)

- **Next.js 16+** (App Router, Turbopack, `output: "standalone"`).
- **React 19+**.
- **Tailwind v4** (`@theme inline` block in `globals.css` for token wiring; the `@tailwindcss/postcss` plugin replaces v3's `tailwind.config.js` for most cases).
- **shadcn-style primitives** — Radix UI + cva. Hand-written copies in `components/ui/` (no CLI dependency); this keeps them owned and patchable.
- **TanStack Query v5** for caching + refetch on focus + stale time.
- **Zustand** for ephemeral UI state (theme, sidebar collapsed, command-palette open). NOT for server data — that's TanStack's job.
- **next-themes** for dark/light, `enableSystem={false} disableTransitionOnChange` to keep theme toggle snappy.
- **Recharts** with theme baked into wrapper components.
- **Geist Sans + Geist Mono** via the `geist/font/sans` + `geist/font/mono` packages.
- **lucide-react** for icons (the React component package, not lucide-static).
- **sonner** for toasts.

### Hard rule from a real session: don't sketch first if the user said "production-grade"

If the brief mentions "professional," "amazing," "flexible," "swap-friendly," "audience is developers + PMs," or "we will be adding components," propose Next.js + shadcn FROM THE START. Spending an hour on a single-file HTML "MVP first" of a multi-route operator dashboard is throwing away the artifact the user actually wanted, and they'll ask you to rebuild it the next day. The "dashboard" the orchestrator's auto-generated Swagger UI at `/docs` provides is also NOT a dashboard — Swagger is API surface for developers, not an operator UI.

### Deployment of the Next.js shape

Once you escalate to Next.js, the build + deploy lane has its own pitfalls that are NOT in this skill. Load these companion skills before the first Dockerfile:

- `devops/nextjs-acr-build-public-env` — `NEXT_PUBLIC_*` baked at build time vs runtime env, post-deploy chunk-grep verification.
- `devops/nextjs-acr-build-public-env/references/pnpm-build-authorization.md` — pnpm 11's `[ERR_PNPM_IGNORED_BUILDS]` blocker (use `--config.dangerously-allow-all-builds=true`), the `[ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY]` cross-stage trap (collapse deps+builder), the Next.js 15+ standalone `server.js` path change (now lives at root of `.next/standalone/`).
- `devops/nextjs-acr-build-public-env/references/container-apps-cors-and-bearer-proxy.md` — the two browser-side walls after deploy: CORS preflight blocked (`corsPolicy` block in Bicep ingress) and bearer-auth 401 (Next.js route handler proxy with `process.env["TOKEN"]` bracket notation to dodge Hermes redaction).
