# Components Specification

## Purpose
Reusable UI components that form the building blocks of all dashboards and pages.

## Requirements

### Requirement: Card Component

Cards SHALL provide the primary content container.

#### Scenario: Standard card
- **WHEN** grouping related content
- **THEN** use `background: var(--bg-surface)`, `border: 1px solid var(--border-default)`, `border-radius: var(--radius-lg)`, `padding: var(--space-6)`
- **AND** cards SHALL NOT use box-shadow for visual separation — subtle borders only

### Requirement: Stat Card (KPI)

Stat cards SHALL display key metrics.

#### Scenario: Rendering a KPI
- **THEN** label uses `var(--text-sm)` + `var(--text-secondary)`
- **AND** value uses `var(--text-2xl)` + `font-weight: 700`
- **AND** change indicator uses green for positive, red for negative

### Requirement: Badge Component

Badges SHALL indicate status with semantic colors.

#### Scenario: Badge variants
- **THEN** success badge: `var(--success-bg)` background + `var(--color-success)` text
- **AND** warning badge: `var(--warning-bg)` + `var(--color-warning)`
- **AND** danger badge: `var(--danger-bg)` + `var(--color-danger)`
- **AND** info badge: `var(--accent-bg)` + `var(--color-accent)`
- **AND** badge uses `var(--radius-full)` for pill shape

### Requirement: Table Component

Tables SHALL be scannable with hover feedback.

#### Scenario: Table headers
- **THEN** use `var(--bg-elevated)` background, `var(--text-secondary)` color
- **AND** uppercase, `var(--text-xs)`, `letter-spacing: 0.05em`

#### Scenario: Table rows
- **THEN** rows MUST have hover state: `tr:hover td { background: rgba(88,166,255,0.04) }`
- **AND** bottom border uses `var(--border-muted)`

### Requirement: Button Component

Buttons SHALL provide clear affordance and feedback.

#### Scenario: Button states
- **THEN** default: `var(--bg-surface)` background + `var(--border-default)` border
- **AND** hover: `var(--bg-elevated)` background
- **AND** disabled: `opacity: 0.6`, `cursor: not-allowed`
- **AND** primary variant: `var(--color-accent)` background + `var(--bg-primary)` text

### Requirement: Nav / Tabs Component

Tab navigation SHALL indicate active state clearly.

#### Scenario: Tab states
- **THEN** default tab: `var(--text-secondary)`, `border-bottom: 2px solid transparent`
- **AND** active tab: `var(--text-primary)`, `border-bottom-color: var(--color-accent)`
- **AND** hover: `var(--text-primary)`

### Requirement: Alert Component

Alerts SHALL use semantic colors with left-border accent.

#### Scenario: Alert variants
- **THEN** info: `var(--accent-bg)` + `3px solid var(--color-accent)` left border
- **AND** warning: `var(--warning-bg)` + `3px solid var(--color-warning)`
- **AND** danger: `var(--danger-bg)` + `3px solid var(--color-danger)`

### Requirement: Visual Feedback

Every interactive element SHALL provide visual feedback.

#### Scenario: Async button action
- **WHEN** a button triggers async work
- **THEN** show spinner (Lucide `loader` icon + CSS spin animation), disable button, change label
- **AND** on success: show green checkmark or toast
- **AND** on error: show inline error near the trigger

#### Scenario: Page loading
- **WHEN** page or section is loading data
- **THEN** show skeleton placeholders, progress bar, or spinner overlay
- **AND** NEVER just freeze with no visual change
