# Charts Specification

## Purpose
Standardized chart theming and library selection for data visualizations.

## Requirements

### Requirement: Chart Library Selection

ECharts SHALL be the default charting library for new projects.

#### Scenario: New dashboard
- **WHEN** building a new dashboard or adding charts to an existing page
- **THEN** use Apache ECharts (`cdn.jsdelivr.net/npm/apache-echarts@5/dist/echarts.min.js`)
- **AND** Chart.js is acceptable ONLY if the project already uses it

#### Scenario: Trading/time series
- **WHEN** building financial time series charts
- **THEN** prefer Lightweight Charts (`cdn.jsdelivr.net/npm/lightweight-charts@4/dist/lightweight-charts.standalone.production.js`)

### Requirement: ECharts Theme

All ECharts instances SHALL use the dark theme configuration.

#### Scenario: Creating a chart
- **WHEN** initializing an ECharts instance
- **THEN** apply theme with `backgroundColor: 'transparent'`, text color `#8b949e`, axis/grid colors matching design tokens
- **AND** color palette: `['#58a6ff', '#3fb950', '#d29922', '#f85149', '#bc8cff', '#f778ba', '#d18616', '#79c0ff']`
- **AND** tooltip: `backgroundColor: '#1c2128'`, `borderColor: '#30363d'`, `textStyle.color: '#e6edf3'`

### Requirement: Chart.js Theme (Legacy)

When Chart.js is used in existing projects, it SHALL match the design system.

#### Scenario: Chart.js defaults
- **THEN** set `Chart.defaults.color = '#8b949e'`
- **AND** `Chart.defaults.borderColor = '#30363d'`
- **AND** font family matches `--font-sans`

### Requirement: Lightweight Charts Theme

Trading charts SHALL match the dark theme.

#### Scenario: Creating a trading chart
- **THEN** layout background transparent, text `#8b949e`
- **AND** grid lines `#21262d`
- **AND** price scale and time scale borders `#30363d`
