# Artifact Manifest — MANDATORY pre-code step

Before writing a single line of markup, emit this block as an HTML comment at the top of the
file AND state it to the user. It forces the ambiguities to be resolved before generation
instead of being papered over with a card grid.

This is the highest-leverage part of the skill. An agent that skips it will default to the
generic dashboard skeleton regardless of how much taste prose it has read.

```yaml
artifact_class: operational          # executive | operational | analytical | narrative | report
audience: on-call engineer
primary_task: identify the source of current customer impact
primary_question: which services are degraded right now, and since when?
primary_answer: active incidents grouped by affected service
critical_actions:                    # what the user must be able to DO
  - acknowledge incident
  - open runbook
data_lifecycle: live                 # bundled | fetched | live   -> determines required states
data_semantics:
  missing: unknown                   # unknown | measured-zero
  zero: measured zero
  stale_after: 120s
  timezone: UTC
  units: {latency: ms, errors: count/min}
provenance:                          # REQUIRED — see rule set below
  supplied: [service list, latency series]
  derived: [error rate = errors/requests]
  assumptions: [SLO target 99.9% assumed, not supplied]
  placeholder: []                    # MUST be empty for delivered artifacts, or visibly labeled
density:
  controls: compact
  tables: dense
  alerts: comfortable
theme: [dark, light]
brand: github                        # user-supplied only; never inferred from domain
charts:
  latency:
    chart: line
    reason: change over time
    interpolation: none              # justified against charts.md Q7
    value_axis_zero: false
    missing: gap
overrides:                           # any default rule broken, with reason
  - rule: one-hero-per-screen
    reason: operational archetype scans for exceptions; hierarchy and urgency are separate channels
```

## Artifact classes

| Class | Primary behavior | Default density | Composition model | Hero rule |
|---|---|---|---|---|
| Executive | Decide / summarize | Comfortable | Hero + supporting evidence | One hero |
| Operational | Detect / act | Compact + dense | Exception-first console | No hero; urgency channel |
| Analytical | Compare / investigate | Compact | Controls + coordinated views | Hero is the comparison |
| Narrative | Understand sequentially | Comfortable | Editorial flow, paced beats | One thesis, many beats |
| Report | Read / export | Comfortable | Document hierarchy | Print-first |

Pick exactly one. If the request genuinely spans two, build the dominant one and say so.

## ANTI-INFLATION RULES (agent-specific — this is where generated UI actually fails)

Violating any of these is a defect, not a style opinion:

- **Do not invent data.** No fabricated trend percentages, comparison periods, forecasts, or
  filler rows. If the delta is not derivable from supplied data, omit the delta.
- **No fake "last updated"** timestamps. Show one only if a real timestamp exists.
- **No unreachable states.** No loading skeletons, retry buttons, reconnect banners, or
  partial-failure notices for bundled/static data.
- **No manufactured interactivity.** No export/share/refresh buttons that do nothing.
- **No sidebar** for fewer than 3 destinations. **No tabs** for fewer than 2 durable views.
- **No filters** that the data does not support or the user did not ask for.
- **No KPI card** restating a value already legible in an adjacent chart.
- **Placeholder data must be visibly labeled** in the UI, not just in a comment.
- **Derived values must be marked** as derived, with the formula available (title attr or caption).

## Provenance disclosure

Every artifact distinguishes: supplied data / derived values / assumptions / placeholder /
agent-authored interpretation / missing inputs. Polished UI makes invented claims look
authoritative — that is the single biggest risk of agent-generated dashboards.

Minimum: a footer line naming the data source and generation time, plus visible marking on any
value that is derived or assumed.
