# UX/UI Design System — OpenSpec

> Last updated: 2026-04-17
> Status: **Production**
> Version: 1.3.0

## Purpose

This is the source of truth for all visual output produced by AI agents in this workspace.
Every HTML file — dashboards, explainers, guides, reports, data visualizations — MUST comply with these specs.

## Specs

| Capability | Spec | Status | Description |
|------------|------|--------|-------------|
| Design Tokens | [specs/design-tokens/spec.md](specs/design-tokens/spec.md) | Implemented | CSS custom properties — colors, spacing, typography, radius, shadows |
| Components | [specs/components/spec.md](specs/components/spec.md) | Implemented | Card, stat-card, badge, table, button, nav, alert, progress |
| Icons | [specs/icons/spec.md](specs/icons/spec.md) | Implemented | Lucide icon font — zero emoji in UI |
| Charts | [specs/charts/spec.md](specs/charts/spec.md) | Implemented | ECharts (primary), Chart.js (legacy), Lightweight Charts (trading) |
| Layout | [specs/layout/spec.md](specs/layout/spec.md) | Implemented | Grid system, dashboard shell, container, responsive breakpoints |
| Interactivity | [specs/interactivity/spec.md](specs/interactivity/spec.md) | Implemented | Alpine.js patterns — tabs, toggles, filters, loading states |
| Data Integrity | [specs/data-integrity/spec.md](specs/data-integrity/spec.md) | Implemented | Missing/stale data handling — empty-write guards, carry-forward with `stale: true`, visually distinct empty states, required regression tests for data producers |

## Rules

1. **Spec BEFORE code.** Read these specs before building any HTML.
2. **Compliance check AFTER code.** Run `COMPLIANCE.md` checklist before delivering.
3. **Use TEMPLATE.html.** Copy the template, don't write from scratch.
4. **Exceptions must be documented.** If a project deviates (e.g., a trading dashboard brand colors), document it in that project's openspec.
5. **Update specs when design system changes.** New components, tokens, or patterns get a spec first.

## Cross-Project Applicability

This design system applies to ALL projects unless a project's own openspec explicitly overrides specific tokens or patterns:

| Project | Compliance | Notes |
|---------|-----------|-------|
| MSX SE Helper — Dashboard (`src/dashboard/`) | ✅ Compliant | Reference implementation — 3-file split, 9 tabs, 4 modals, sticky headers, KPI cards on all tabs |
| MSX SE Helper — Setup Guide (`docs/setup-guide.html`) | ❌ Non-compliant | Abbreviated vars, emoji icons, no Lucide — migration backlogged |
| a trading dashboard Dashboard v2 | ⚠️ Partial | Has own `variables.css` token system + Lucide. Colors diverge (branded). Acceptable — document in BT openspec. |
| Hormuz Crisis Dashboard | ❌ Non-compliant | Different palette, monospace font, no tokens — migration backlogged |
| CPapper App | ⚠️ TBD | React+TS+Vite — different stack, needs adapted spec |

## File Reference

| File | Path (relative to skill root) | Purpose |
|------|------|---------|
| SKILL.md | `./SKILL.md` | Full design system reference + quick-copy snippets |
| COMPLIANCE.md | `./COMPLIANCE.md` | Pre-delivery checklist |
| TEMPLATE.html | `./TEMPLATE.html` | Ready-to-copy starter template |
| OpenSpec | `./openspec/` | This directory — formal specs for each capability |
