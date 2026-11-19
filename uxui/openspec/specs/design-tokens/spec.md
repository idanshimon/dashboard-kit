# Design Tokens Specification

## Purpose
CSS custom properties that define the visual language. Every color, spacing value, font size, and radius in any HTML output MUST reference these tokens.

## Requirements

### Requirement: Canonical Variable Names

Design tokens SHALL use full, descriptive names. Abbreviated names are prohibited.

#### Scenario: Using background tokens
- **WHEN** setting any background color
- **THEN** use `var(--bg-primary)`, `var(--bg-surface)`, `var(--bg-elevated)`, or `var(--bg-overlay)`
- **AND** NEVER use shortened forms like `var(--bg)`, `var(--surface)`

#### Scenario: Using text tokens
- **WHEN** setting any text color
- **THEN** use `var(--text-primary)`, `var(--text-secondary)`, `var(--text-tertiary)`, or `var(--text-link)`
- **AND** NEVER use `var(--text)`, `var(--muted)`

#### Scenario: Using semantic color tokens
- **WHEN** indicating status or meaning
- **THEN** use `var(--color-accent)`, `var(--color-success)`, `var(--color-warning)`, `var(--color-danger)`
- **AND** NEVER use `var(--green)`, `var(--red)`, `var(--yellow)`, `var(--accent)`

### Requirement: No Hardcoded Values

No CSS property SHALL use raw color, spacing, font-size, or radius values outside the `:root` block.

#### Scenario: Setting spacing
- **WHEN** setting padding, margin, or gap
- **THEN** use `var(--space-N)` where N is 1,2,3,4,5,6,8,10,12,16
- **AND** NEVER use raw `px` values (exception: `1px` for borders, `0` for reset)

#### Scenario: Setting font sizes
- **WHEN** setting any font-size
- **THEN** use `var(--text-xs)` through `var(--text-3xl)`
- **AND** NEVER use raw `rem` or `px` values

#### Scenario: Setting border radius
- **WHEN** setting any border-radius
- **THEN** use `var(--radius-sm)` through `var(--radius-full)`
- **AND** NEVER use raw `px` values

### Requirement: Color Palette

The color palette SHALL be dark-theme GitHub-inspired.

#### Scenario: Background hierarchy
- **GIVEN** the design follows a layered elevation model
- **THEN** backgrounds are ordered: `--bg-primary` (#0d1117) < `--bg-surface` (#161b22) < `--bg-elevated` (#1c2128) < `--bg-overlay` (#2d333b)

#### Scenario: Semantic color usage
- **WHEN** using semantic colors
- **THEN** green (`--color-success` / #3fb950) = good/complete
- **AND** yellow (`--color-warning` / #d29922) = warning/risk
- **AND** red (`--color-danger` / #f85149) = critical/error
- **AND** blue (`--color-accent` / #58a6ff) = info/primary action
- **AND** purple (`--color-purple` / #bc8cff) = special/highlight

### Requirement: Spacing Scale

Spacing SHALL follow a 4px base scale.

#### Scenario: Available spacing values
- **WHEN** choosing spacing
- **THEN** use only: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64 (px)
- **AND** reference as `--space-1` through `--space-16`

### Requirement: Typography Scale

Font sizes SHALL use a defined rem scale.

#### Scenario: Available sizes
- **WHEN** choosing font size
- **THEN** use: xs (0.75rem), sm (0.875rem), base (1rem), lg (1.125rem), xl (1.25rem), 2xl (1.5rem), 3xl (1.875rem)

### Requirement: Font Stacks

Two font stacks SHALL be available.

#### Scenario: Body text
- **WHEN** rendering body text, labels, buttons, or headings
- **THEN** use `var(--font-sans)`: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif`
- **AND** body font-family SHALL always be `var(--font-sans)`, never monospace

#### Scenario: Code or data
- **WHEN** rendering code, terminal output, or tabular numbers
- **THEN** use `var(--font-mono)`: `'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace`

## Token Reference

See `SKILL.md` → "Design Tokens (MANDATORY)" section for the complete `:root` block.
