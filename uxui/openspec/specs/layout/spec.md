# Layout Specification

## Purpose
Responsive grid system, dashboard shell, and container patterns.

## Requirements

### Requirement: Viewport Meta Tag

Every HTML page SHALL include the viewport meta tag.

#### Scenario: Page setup
- **WHEN** creating any HTML file
- **THEN** include `<meta name="viewport" content="width=device-width, initial-scale=1.0">`

### Requirement: CSS Reset

Every page SHALL include the base reset.

#### Scenario: Reset styles
- **THEN** `* { box-sizing: border-box; margin: 0; padding: 0; }`
- **AND** body: `font-family: var(--font-sans)`, `background: var(--bg-primary)`, `color: var(--text-primary)`, `line-height: 1.6`, `-webkit-font-smoothing: antialiased`

### Requirement: Container Widths

Content SHALL be constrained within standard containers.

#### Scenario: Standard page
- **THEN** `.container`: `max-width: 1200px`, centered, `padding: 0 var(--space-4)`

#### Scenario: Wide dashboard
- **THEN** `.container-wide`: `max-width: 1440px`, centered, `padding: 0 var(--space-4)`

### Requirement: Grid System

Grid layouts SHALL use CSS Grid with standard column counts.

#### Scenario: Grid options
- **THEN** `.grid-2`: 2 columns, `.grid-3`: 3 columns, `.grid-4`: 4 columns
- **AND** `.grid-auto`: `repeat(auto-fit, minmax(280px, 1fr))`
- **AND** all grids use `gap: var(--space-4)`

### Requirement: Responsive Breakpoints

Layouts SHALL collapse on smaller screens.

#### Scenario: Mobile (≤768px)
- **THEN** all multi-column grids collapse to single column
- **AND** `.hide-mobile` hides non-essential content

#### Scenario: Tablet (769px–1024px)
- **THEN** 3- and 4-column grids collapse to 2 columns

### Requirement: Dashboard Shell

Dashboard pages SHALL use the standard shell structure.

#### Scenario: Dashboard layout
- **THEN** sticky header: `var(--bg-surface)`, `z-index: 100`, border-bottom
- **AND** body: `padding: var(--space-6)`, containing a `.container-wide`
- **AND** mobile: reduce header and body padding

### Requirement: Dashboard Overview Layout

Dashboard overview pages SHALL follow this vertical ordering:

#### Scenario: Overview page structure
- **THEN** the layout follows this order top-to-bottom:
  1. **Header** — sticky, app title (clickable → overview), FY picker, sync button
  2. **KPI Summary Cards** — grid of stat cards, visible on ALL tabs (not scoped to overview)
  3. **Alert Banners** — negative milestones, warnings (overview tab only)
  4. **Tab Navigation** — sticky below header
  5. **Tab Content** — charts, tables, details per tab
  6. **Territory / Coverage** — collapsible, BELOW charts (overview tab only)
  7. **Status Legend** — color key for milestone statuses (overview tab only)

#### Scenario: KPI cards persistence
- **WHEN** user switches between tabs
- **THEN** KPI summary cards remain visible above the tab bar
- **AND** users always have top-level context (ACR, counts, status) regardless of active tab

#### Scenario: Territory and coverage below charts
- **WHEN** overview tab is active
- **THEN** territory coverage appears BELOW the chart area
- **AND** territory section is collapsed by default (user clicks to expand)
- **BECAUSE** charts are the primary visual on overview; territory is reference data

#### Scenario: No inline legend bars
- **WHEN** status colors or category meanings need explaining
- **THEN** attach them as (i) tooltips on the relevant chart or section title
- **AND** do NOT render a standalone legend bar taking up vertical space
- **BECAUSE** legends clutter the overview; tooltips provide the same info on-demand without wasting space

#### Scenario: No onboarding guides in production
- **WHEN** building a dashboard for internal tooling
- **THEN** do NOT include guided tours, step-by-step onboarding, or "getting started" wizards
- **BECAUSE** internal users learn from context + FAQ tab; guided tours add unused complexity

### Requirement: Engagement Metrics Over Binary Flags

Dashboard KPI sections SHALL show actionable ratios, not binary achievement flags.

#### Scenario: Engagement quality metrics
- **WHEN** displaying engagement or coverage metrics
- **THEN** use percentage-based quality metrics that drive behavior:
  - **Activity Coverage** — % of milestones with ≥1 activity (drives: "go log tasks")
  - **Commitment Rate** — % of engaged milestones that are Committed (drives: "push SSPs to commit")
  - **Completion Rate** — % of engaged milestones Completed (drives: "close things")
  - **At Risk Ratio** — % of active milestones At Risk or Blocked (drives: "go unblock")
- **AND** do NOT use binary flags like "Engage 1+ Milestones: Achieved" which provide zero signal once met
- **BECAUSE** ratios show health and drive action; binary flags just confirm existence

### Requirement: No Horizontal Scroll

Pages SHALL NOT produce horizontal scroll on any screen width.

#### Scenario: Content overflow
- **WHEN** content exceeds container width
- **THEN** use `overflow-x: auto` on the specific element (e.g., table wrapper)
- **AND** the page body SHALL NOT have horizontal overflow

#### Scenario: Sticky `<thead>` in scrollable page
- **GIVEN** a table with `position: sticky` on `<thead>`/`<th>` inside a page that scrolls vertically
- **WHEN** the table is wrapped in `.table-wrap` for visual framing (border + radius)
- **THEN** `.table-wrap` SHALL NOT set `overflow-x: clip`, `overflow-x: hidden`, or `overflow-x: auto`
- **AND** `.table-wrap` SHALL leave overflow at its default `visible`
- **RATIONALE:** `overflow: clip|hidden` creates a painting containing block and `overflow: auto` creates a scroll context; either one pins sticky descendants to the wrap instead of the viewport, causing the `<thead>` to “unstick” mid-table on scroll.
- **AND** `<thead>` SHALL have an explicit solid background (`background: var(--bg-elevated)`) so rows do not bleed through cell gaps when scrolling past the sticky header.
- **AND** if horizontal scroll is genuinely required, the horizontally-scrolling container SHALL be placed *inside* the sticky-capable wrap, wrapping only the table body, never the whole table.
- **Regression reference:** `msx-se-helper` v0.11.3 (commit `569c986`) — sticky `<thead>` broke in every dashboard table because `.table-wrap { overflow-x: clip }` was recommended by an earlier version of this spec. The guidance was wrong; this scenario supersedes it.
