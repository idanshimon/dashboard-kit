# Data Integrity Specification

## Purpose
Rules for how dashboards handle missing, stale, or degraded data so users can
always tell whether a value is real, inherited from an earlier run, or absent.

This spec exists because of the Apr 16, 2026 regression where a a trading dashboard
Research page condition rendered `0.00 → 5.00 unmet` — identical to a
legitimate "below threshold" reading — when the underlying value was actually
unavailable. Users cannot distinguish "0" from "no data" by sight. The fix
must be enforced at the data layer AND reflected at the UI layer.

## Requirements

### Requirement: Never overwrite good data with empty data

Data producers (scripts that write JSON files consumed by the UI) SHALL NOT
silently replace a populated file with an empty or obviously-degraded one.

#### Scenario: Upstream API returns zero records
- **WHEN** a data producer script fetches its source (yfinance, IB, etc.)
  and receives zero items
- **THEN** the script SHALL refuse to write the output file
- **AND** the script SHALL log an explicit warning containing the word
  `refusing` or `skipped` and the expected vs actual count
- **AND** the previous good file SHALL remain the source of truth

#### Scenario: Upstream API returns partial data
- **WHEN** a data producer receives fewer than 50% of expected records
- **THEN** the script SHALL merge fresh values over the prior file's values
- **AND** the output SHALL include a `source` or `partial` flag identifying
  the merge (e.g. `"source": "yfinance+carryforward"`)
- **AND** the script SHALL log the partial count

### Requirement: Carry forward on sentinel values

Signal/metric compute functions that return sentinel values like `no_data`,
`no_sma`, `missing`, etc. on input failure SHALL NOT cause their output JSON
file to overwrite a prior good value with a placeholder like `0`.

#### Scenario: Compute hits a no_data sentinel with a good prior
- **WHEN** a compute function returns a sentinel label (typically paired with
  a zeroed numeric value) AND the prior file has a non-sentinel, non-zero
  value for the same key
- **THEN** the new file SHALL carry forward the prior `value`, `score`, and
  `signal` fields
- **AND** the carried-forward entry SHALL be stamped with a boolean flag
  (e.g. `"stale": true`) so downstream UI and observers can detect it
- **AND** a `[warn]` line SHALL be printed identifying the key and the
  carry-forward action

#### Scenario: Recovery from a stale run
- **WHEN** a subsequent compute succeeds with fresh data
- **THEN** the fresh values SHALL overwrite the carried-forward values
- **AND** the `stale` flag SHALL be removed from the entry

### Requirement: Distinguish "missing" from "zero" in the UI

UI components SHALL render missing/stale data differently from real zero
values. A condition unmet because data is missing must not look identical
to a condition unmet because the metric is genuinely at/below threshold.

#### Scenario: Rendering a metric value
- **WHEN** a backing JSON value carries a `stale: true` flag OR the
  `signal`/`label` field is a known sentinel (e.g. `no_data`, `no_sma`)
- **THEN** the component SHALL visually distinguish the value (dimmed
  opacity, muted color, dashed border, or a "stale" / "no data" badge)
- **AND** SHALL include a tooltip or caption explaining the state
- **AND** SHALL NOT treat the numeric value as comparable to real data for
  purposes of threshold evaluation, sorting, or ranking

#### Scenario: Rendering a value that is genuinely zero
- **WHEN** the backing data is a real measured zero (no stale/sentinel flag)
- **THEN** the component renders normally with full contrast and the normal
  color treatment for its tier (met/unmet, positive/negative, etc.)

### Requirement: Empty-state placeholders

Cards, lists, and charts SHALL have an explicit empty-state treatment when
their data source is fully unavailable.

#### Scenario: No data at all
- **WHEN** the backing dataset is empty (zero rows, file not found, HTTP
  error)
- **THEN** the component SHALL render a dedicated empty-state element
  (icon + short message) rather than a zero-filled chart/table
- **AND** messaging SHALL be specific ("No regime history yet — builds
  over time" NOT "No data")
- **AND** SHALL NOT silently render a blank or zero-filled area

### Requirement: Regression tests for data producers

Any script that writes JSON consumed by the UI SHALL have tests covering:
1. The happy path (realistic input → expected output)
2. Empty input (missing keys, zero rows)
3. Partial input (some expected keys present, others missing)
4. Recovery (prior stale state + fresh input → stale flag cleared)

Tests SHALL NOT make network calls; use `monkeypatch` / `patch` to inject
fake responses.

#### Scenario: New data-producing script is added
- **WHEN** a new script under `scripts/` writes to `data/*.json`
- **THEN** a matching `tests/test_<script>.py` SHALL be added in the same
  change set
- **AND** the test suite SHALL run as part of pre-push or CI

## Rationale

The Apr 16 bug was invisible to both the data producer (script exited 0)
and the UI (rendered a plausible-looking number). The only way to catch
it was a human spot-check. A design system that treats missing data as
a first-class visual state — distinct from measured zero — makes this
class of bug loud instead of silent.

## Related

- Project implementation: `trading-dashboard/openspec/changes/data-integrity-guards/OPENSPEC.md`
- Tests demonstrating the pattern: `trading-dashboard/tests/test_update_regime.py`,
  `tests/test_update_prices.py`
