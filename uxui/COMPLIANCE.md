# UX/UI Compliance Checklist

**Use this before delivering ANY HTML file.** Every item is mandatory.

## Pre-Flight Checklist

### 1. Design Tokens (CSS Variables)
- [ ] `:root` block includes ALL standard tokens (not abbreviated versions)
- [ ] Variable names match exactly: `--bg-primary`, `--bg-surface`, `--bg-elevated`, `--bg-overlay`
- [ ] NOT shortened: ~~`--bg`~~, ~~`--surface`~~, ~~`--text`~~, ~~`--muted`~~, ~~`--border`~~
- [ ] Text vars: `--text-primary`, `--text-secondary`, `--text-tertiary`, `--text-link`
- [ ] Semantic colors: `--color-accent`, `--color-success`, `--color-warning`, `--color-danger`
- [ ] Accent backgrounds: `--accent-bg`, `--success-bg`, `--warning-bg`, `--danger-bg`
- [ ] Full spacing scale: `--space-1` through `--space-16`
- [ ] Typography scale: `--text-xs` through `--text-3xl`
- [ ] Radius scale: `--radius-sm` through `--radius-full`
- [ ] Font stacks: `--font-sans`, `--font-mono`

### 2. Icons
- [ ] Lucide icon font loaded via CDN
- [ ] **ZERO emoji used as icons** (emoji OK in content text, never as UI elements)
- [ ] Icons use `<i class="lucide-*">` syntax
- [ ] No inline SVGs when Lucide has the icon

### 3. No Hardcoded Values
- [ ] No raw `#hexcolor` outside `:root` — all colors reference variables
- [ ] No raw `px` for spacing — use `var(--space-*)` 
- [ ] No raw `rem`/`px` for font sizes — use `var(--text-*)`
- [ ] No raw `px` for border-radius — use `var(--radius-*)`
- [ ] Exception: `1px` for borders, `0` values, and complex calc() are OK

### 4. Responsive
- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1.0">` present
- [ ] Mobile breakpoint at 768px
- [ ] Grids collapse to single column on mobile
- [ ] No horizontal scroll on mobile

### 5. CDN Stack
- [ ] Lucide: `https://cdn.jsdelivr.net/npm/lucide-static@latest/font/lucide.min.css`
- [ ] Alpine.js: `https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js` (defer)
- [ ] `[x-cloak] { display: none !important; }` in CSS
- [ ] Charts: ECharts preferred for new work; Chart.js only if project already uses it
- [ ] Interactivity via Alpine.js `x-data`, NOT vanilla JS event listeners for UI state

### 6. Component Patterns
- [ ] Cards use `.card` pattern with `--bg-surface` + `--border-default`
- [ ] Tables have hover state (`tr:hover`)
- [ ] Badges use semantic color classes
- [ ] Buttons have `:hover` and `:disabled` states
- [ ] Loading states for all async actions

### 7. Body / Reset
- [ ] `* { box-sizing: border-box; margin: 0; padding: 0; }`
- [ ] Body uses `var(--font-sans)` — NOT monospace (unless terminal-themed)
- [ ] Body background: `var(--bg-primary)`
- [ ] Body color: `var(--text-primary)`
- [ ] `-webkit-font-smoothing: antialiased`

### 8. Architecture (files > 1,500 lines)
- [ ] CSS extracted to separate file served as `<link>` (not inline `<style>`)
- [ ] JS extracted to separate file served as `<script src>` (not inline `<script>`)
- [ ] Server-side variables use `__PLACEHOLDER__` pattern (not template literals in browser code)
- [ ] All `__PLACEHOLDER__` values replaced at server startup (no raw `__X__` in rendered output)
- [ ] Gzip compression enabled for all responses (`Content-Encoding: gzip`)

### 9. Alpine.js Safety
- [ ] No computed getter has the same name as a data property (silent shadowing bug)
- [ ] Server-side variables declared with `const` in `<script>` block (not bare references)
- [ ] Modals are inside the `x-data` scope (before closing `</div>` of wrapper)
- [ ] `x-cloak` on all initially-hidden elements

### 10. Navigation & Layout Consistency
- [ ] App title/logo in header is clickable and navigates to overview/home tab
- [ ] KPI summary cards visible on ALL tabs (not scoped to overview only)
- [ ] **Nav bar sticks to top on scroll across EVERY tab** (`position: sticky; top: 0; z-index: var(--z-nav)`)
- [ ] Sticky header → sticky nav → sticky table headers with correct z-index layering (100 → 90 → 2)
- [ ] **Sub-page sticky elements (table headers, section headers) MUST offset by `var(--sticky-top-offset)` — never `top: 0`** (reserved for nav bar only)
- [ ] **Sticky table headers declare explicit `z-index: var(--z-table-head)` (80)** — below `--z-nav` (100) so they slide under the nav cleanly
- [ ] **Do NOT use `overflow-x: clip` or `overflow-x: hidden` on table containers** — both create a sticky containing block in Chromium and break `position: sticky` on `<thead>`. Leave overflow `visible` (the default). If horizontal scrolling is needed, wrap the table in a separate scroll container *inside* the sticky-capable wrap, not around it.
- [ ] Tooltips use `.tooltip-below` near page top to avoid viewport clipping
- [ ] Every tab has a description (tooltip or subtitle) explaining its purpose

### 10. Modal UX
- [ ] Draft persistence: auto-saves to localStorage on input changes
- [ ] Draft saves on ALL close paths (outside click, X, Cancel)
- [ ] Draft restored with amber banner + Discard button on reopen
- [ ] Draft cleared on successful submit
- [ ] Drafts keyed per entity ID (not global)

### 11. Microcopy
- [ ] Feature spec includes UX Microcopy table (element → copy → purpose)
- [ ] Hover text is actionable (not just descriptive)
- [ ] (i) info icons on concepts that need explaining
- [ ] FAQ entries updated when features ship (no stale "coming soon")
- [ ] Tab descriptions include badge/icon legends when applicable

## Common Mistakes (Do NOT Repeat)

| Mistake | Example | Fix |
|---------|---------|-----|
| Abbreviated variable names | `--bg: #0d1117` | `--bg-primary: #0d1117` |
| Emoji as UI icons | `<div class="icon">⬡</div>` | `<i class="lucide-hexagon"></i>` |
| Different color palette | `--bg: #0a0e17` (blue-tinted) | Use standard `--bg-primary: #0d1117` |
| Monospace body font | `font-family: 'SF Mono', monospace` | `font-family: var(--font-sans)` |
| Hardcoded spacing | `padding: 24px 32px` | `padding: var(--space-6) var(--space-8)` |
| Hardcoded font sizes | `font-size: 0.85rem` | `font-size: var(--text-sm)` |
| Hardcoded radius | `border-radius: 8px` | `border-radius: var(--radius-lg)` |
| Chart.js on new project | `<script src="chart.js">` | Use ECharts unless project already has Chart.js |
| Vanilla JS for UI state | `element.addEventListener('click'...)` | Alpine.js `x-data` / `@click` |
| Missing hover states | Static table rows | `tr:hover td { background: rgba(88,166,255,0.04); }` |
| Server var in browser JS | `'FY' + CURRENT_FY` in `<script>` | Declare `const CURRENT_FY = __CURRENT_FY__;` — server replaces placeholder |
| Alpine getter shadows data | `get categories()` kills `categories: {}` | Use distinct names: `categoryOptions` vs `get categoryFilters()` |
| Modal outside x-data scope | Modal after closing `</div>` of x-data | Place modals inside x-data wrapper, after `</main>` |
| KPI cards only on overview | Cards disappear when switching tabs | Move KPI grid outside tab-specific `x-show` wrapper |
| Non-clickable app title | Users can't get back to overview | Add `cursor:pointer` + `@click="tab = 'overview'"` to header title |
| `overflow-x: clip` / `overflow-x: auto` on `.table-wrap` | Both break sticky `<thead>` — `clip` creates a painting containing block, `auto` creates a scroll context | Leave overflow `visible`. Table is 100% width = no horizontal overflow; border-radius still clips corners. Only add a scroll container if you truly need horizontal scroll, and put it *inside* the sticky-capable wrap. |
| Missing `<thead>` background | Rows bleed through cell gaps as they scroll past the sticky header | `.table thead { background: var(--bg-elevated); }` — solid fill on the thead, not just each `<th>` |
| No tab descriptions | Users don't know what each tab does | Add `tip` field to tabs array, show on hover |
| No draft persistence | Close modal = lose all input | localStorage save on close, restore on open, amber banner + Discard |
| Inline CSS/JS in 2500+ line file | Single monolith server.js | Extract to `style.css` + `app.js` + `index.html`, serve separately |
| No gzip compression | 160KB HTML response | `zlib.gzipSync()` — reduces to ~16KB |
| Stale FAQ copy | "Coming soon in v0.5" after shipping | Update FAQ entries in the same PR as the feature |

## Known Non-Compliant Files (Backlog)

| File | Status | Issues |
|------|--------|--------|
| `msx-se-helper/docs/setup-guide.html` | ❌ Non-compliant | Abbreviated vars, emoji icons, no Lucide, no Alpine, hardcoded values |
| `breaking-trades/hormuz-crisis/dashboard.html` | ❌ Non-compliant | Different palette, monospace font, no tokens, Chart.js (acceptable — pre-existing) |
| `breaking-trades/hormuz-crisis/index.html` | ⚠️ Unchecked | Needs audit |
| `breaking-trades/hormuz-crisis/map.html` | ⚠️ Unchecked | Needs audit |
| `msx-se-helper/src/dashboard/` | ✅ Compliant | Reference implementation — 3-file split (1,343 HTML + 935 JS), 9 tabs, 4 modals with draft persistence, sticky three-layer headers, KPI cards on all tabs |
| `msx-se-helper/src/server.js` | ✅ Compliant | 309 lines, serves dashboard assets with gzip |

## Enforcement

When building HTML:
1. **Read SKILL.md** — the full design system is there
2. **Copy the `:root` tokens block verbatim** — do not abbreviate
3. **Run this checklist before delivering**
4. **If extending an existing non-compliant file**, migrate it to compliance first (or document the exception)

Exceptions are OK for:
- Third-party embeds/widgets with their own styling
- a trading dashboard public-facing pages that have an established visual brand (document in openspec)
- Quick throwaway prototypes (mark as `<!-- NON-COMPLIANT: prototype -->`)
