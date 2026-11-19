# Interactivity Specification

## Purpose
Alpine.js patterns for UI state management. Vanilla JS for data fetching and charting only.

## Requirements

### Requirement: Alpine.js for UI State

All UI state management SHALL use Alpine.js.

#### Scenario: Loading Alpine
- **WHEN** building any interactive HTML page
- **THEN** include `<script src="https://cdn.jsdelivr.net/npm/alpinejs@3/dist/cdn.min.js" defer></script>`
- **AND** include `[x-cloak] { display: none !important; }` in CSS

#### Scenario: Tab navigation
- **WHEN** implementing tab switching
- **THEN** use Alpine `x-data`, `:class`, `@click`, `x-show`
- **AND** hidden tabs use `x-cloak` to prevent flash

#### Scenario: Search/filter
- **WHEN** implementing client-side filtering
- **THEN** use Alpine `x-model` on input + `x-for` with filter expression
- **AND** NOT vanilla `element.addEventListener` + `element.style.display`

### Requirement: Vanilla JS for Data/Charts

Data fetching and chart initialization SHALL use vanilla JavaScript.

#### Scenario: Fetching API data
- **WHEN** loading data from APIs or JSON files
- **THEN** use `fetch()` in a `<script>` block
- **AND** wire results into Alpine `x-data` via `Alpine.store()` or component methods

#### Scenario: Initializing charts
- **WHEN** creating ECharts or Lightweight Charts instances
- **THEN** use vanilla JS in `<script>` blocks
- **AND** chart containers can reference Alpine data for dynamic updates

### Requirement: No Vanilla Event Listeners for UI

UI state changes SHALL NOT use `addEventListener` + manual DOM manipulation.

#### Scenario: Toggle visibility
- **WHEN** showing/hiding content
- **THEN** use Alpine `x-show` + `x-collapse` or `x-transition`
- **AND** NOT `element.style.display = 'none'`
- **AND** NOT `element.classList.add('hidden')`

#### Scenario: Click handlers
- **WHEN** handling user clicks for UI changes
- **THEN** use Alpine `@click` + reactive data
- **AND** NOT `element.addEventListener('click', ...)`
