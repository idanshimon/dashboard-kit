# Icons Specification

## Purpose
Consistent iconography across all UI output using Lucide icon font.

## Requirements

### Requirement: Lucide Icon Font

All icons SHALL use the Lucide CSS font, loaded via CDN.

#### Scenario: Loading Lucide
- **WHEN** building any HTML page
- **THEN** include `<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/lucide-static@latest/font/lucide.min.css">`
- **AND** use icons via `<i class="lucide-{name}"></i>`

### Requirement: No Emoji as UI Elements

Emoji SHALL NOT be used as icons, status indicators, or UI elements.

#### Scenario: Prerequisite cards
- **WHEN** showing a grid of tool requirements
- **THEN** use Lucide icons (e.g., `lucide-hexagon`, `lucide-wrench`, `lucide-cloud`, `lucide-lock`)
- **AND** NEVER use emoji (⬡, 🔧, ☁️, 🔒)

#### Scenario: Section headers
- **WHEN** adding visual flair to section headings
- **THEN** use Lucide icons inline
- **AND** NEVER use emoji (📋, 🚀, 📖, 🔄, 🔴, 📊, 🏗️, 💡)
- **AND** emoji in markdown/prose content (not rendered in HTML) is acceptable

### Requirement: Icon Sizing

Icons SHALL be sized via CSS font-size, not width/height.

#### Scenario: Inline icon
- **WHEN** placing an icon next to text
- **THEN** default font-size inherits from parent
- **AND** for emphasis, use explicit `font-size` (e.g., `1.2rem`, `1.4rem`)

### Requirement: Icon-to-Concept Mapping

Standard mappings SHALL be used for consistency.

#### Scenario: Common concepts
- **THEN** revenue/money → `lucide-dollar-sign` or `lucide-trending-up`
- **AND** success → `lucide-check-circle`
- **AND** warning → `lucide-alert-triangle`
- **AND** error → `lucide-alert-circle`
- **AND** customer → `lucide-building-2`
- **AND** user → `lucide-user`, team → `lucide-users`
- **AND** calendar → `lucide-calendar`
- **AND** chart → `lucide-bar-chart-3`
- **AND** target → `lucide-target`
- **AND** search → `lucide-search`
- **AND** settings → `lucide-settings`
- **AND** git → `lucide-git-branch`
- **AND** security → `lucide-shield-check`
- **AND** milestone → `lucide-flag`
- **AND** dashboard → `lucide-layout-dashboard`
