# Worked example — agentic-sdlc `ledger-insights-ui` overhaul (2026-07-26)

Concrete instance of every pattern in SKILL.md. Repo:
`~/projects/msft/agentic-sdlc`, app `apps/ledger-insights-ui`, deployed to
Azure Container Apps (`ca-ledger-ui-vnet`, revision `0000029`).

Related in the `agentic-sdlc` skill's own references (that skill is manually
authored and off-limits to autonomous curation — read, don't patch):
`operator-legibility-plain-language-over-state-machine.md`,
`dashboard-ux-table-not-cards.md`,
`live-ui-crash-repro-and-deploy-traps-2026-07.md`,
`build-and-deploy-recipe.md`.

## Diagnosis (from screenshotting the LIVE deployed app)

- Gradient hero "Governed agentic SDLC, made auditable" + a four-plane
  architecture explainer owned the entire first fold — while the app's own
  `DESIGN.md` said *"❌ Don't add a hero section, marketing copy... gradient
  backgrounds. This is an operator dashboard, not a landing page."*
- 50 runs, 24 failed, 2 `awaiting_gate` rows buried at ranks 14–15 under
  eleven failures. ~50% failure rate stated in 9pt grey.
- Sidebar grouped Pipeline Plane / Ledger Plane / Standards Plane / Agent HQ;
  15 items, four of them views of one dataset (Decisions, Decision Map,
  Precedent Lineage, Run Flow).
- `#001018` hand-typed in 4 files; `#1A1520`/`#475569` invented in
  `decisions/lineage-v2`; 78 canvas hexes undocumented.

## What landed

| Fix | Files | Commit |
|---|---|---|
| A attention-first dashboard | `lib/attention.ts`, `components/domain/needs-attention.tsx`, `kpi-card.tsx` (`href`), `app/page.tsx` | `d6d97ac` |
| B triage runs | `components/domain/runs-triage.tsx`, `app/runs/page.tsx` | `1493af7` |
| C verb nav + decision tabs | `layout/sidebar.tsx`, `layout/page-header.tsx`, `domain/decision-views.tsx` | `6195c1a` |
| D `--on-primary` + canvas exception | `globals.css`, `DESIGN.md`, 4 call sites | `e32fd11` |

Gates: `tsc` 0 · vitest 25 files / **179 tests** · production build clean ·
`@google/design.md lint` 0 errors.

## Domain-specific field mappings (this codebase)

- Teaching signals are `runtime_kind === "decision_flagged"` / `"class_paused"`.
  **Not** `status === "demoted"` — that field does not exist on `LedgerEntry`
  and the LSP catches it.
- Deep-link a flag to `entry.references_entry_id` (the decision it acts on),
  not the signal's own `id`.
- Blocked = `awaiting_gate | paused`. Gate stage from
  `run.pending_gate?.stage` → `run.current_stage` → `"a gate"`.
- Failure reason: walk `run.events` backwards for the last
  `status === "failed"` with a `message`.

## Bugs vision caught that 179 green tests did not

1. **Six identical rows** — "A run is waiting on your decision at resolver" ×6.
   Fixed with `collapseDuplicates`; now "13 runs are waiting…" + `×13` badge +
   "Open queue".
2. **"Failed (24h) 0"** while 24 runs sat failed (all >24h old). Now
   "Failed runs 24 · 48% of all runs".
3. **DEMO MODE badge on** despite container env `NEXT_PUBLIC_DEMO_MODE=0`.

## Demo Mode correction (user-initiated)

the user: *"demo mode should still run through all the gates and database."*

Found in `app/runs/new/page.tsx`:
- `onSample` short-circuited BEFORE the orchestrator — `startDemoRun()` replayed
  a localStorage fixture. No gates, no ledger write, no Cosmos.
- Samples without a fixture greyed out and unclickable.
- Paste/upload hard-disabled via `disabled={… || demo}`.
- Copy claimed "Zero LLM calls, zero network."

Fix: sample click now runs `submit()` → real `/api/run`; fixture replay moved
into the `catch` as an announced offline fallback; all cards clickable;
paste re-enabled; `ledger-mcp.ts` query made live-first with an explicit
`live_unreachable`; badge → `DEMO DATA`.

## The `NEXT_PUBLIC_DEMO_MODE` trap in detail

`apps/ledger-insights-ui/Dockerfile:23` is `ARG NEXT_PUBLIC_DEMO_MODE=1`.
`NEXT_PUBLIC_*` is inlined at `next build`, so the runtime container env var is
too late — the app showed the demo badge despite `=0` in its env.

Build correctly:

```bash
ACR_NAME=acragenticsdlctj6c673gu6x5w \
RESOURCE_GROUP=rg-agentic-sdlc-v07-eastus2 \
CONTAINER_APP_NAME=ca-ledger-ui-vnet \
NEXT_PUBLIC_DEMO_MODE=1 \
NEXT_PUBLIC_ORCHESTRATOR_URL=https://ca-orchestrator-vnet.<host> \
NEXT_PUBLIC_LEDGER_MCP_URL=https://ca-ledger-mcp-vnet.<host> \
bash scripts/build-ledger-insights-ui.sh
```

The script enforces spec REQ-9: it REFUSES `=0` unless EasyAuth is enabled on
the target app. `az containerapp auth show -n <app> -g <rg> --query
"properties.platform.enabled" -o tsv` returning empty = no auth config = the
build will be rejected. Matched the prior image's `=1` rather than silently
changing security posture; flagged it to the user instead.

Deploy by digest, then verify:

```bash
az containerapp update -n ca-ledger-ui-vnet -g rg-agentic-sdlc-v07-eastus2 \
  --image <acr>.azurecr.io/ledger-insights-ui@sha256:<digest>
az containerapp revision list -n ca-ledger-ui-vnet -g <rg> \
  --query "[?properties.active].{name:name,running:properties.runningState,traffic:properties.trafficWeight}" -o table
```

## Local live-data preview

```bash
find .next/standalone -name server.js      # monorepo root → .next/standalone/server.js
cp -r .next/static .next/standalone/.next/ && cp -r public .next/standalone/
TOK=$(az containerapp secret show -n ca-ledger-ui-vnet -g <rg> \
      --secret-name ledger-mcp-token --query value -o tsv)
HOSTNAME=127.0.0.1 PORT=3012 LEDGER_MCP_URL=... ORCHESTRATOR_URL=... \
LEDGER_MCP_TOKEN="$TOK" node .next/standalone/server.js
```

`browser_navigate` blocks localhost (SSRF guard) — use headless Chrome
`--screenshot` + `vision_analyze` instead.

## Test-design lessons

- `collapseDuplicates` initially called `ago(at)` without the injected `now` →
  three failures. That was a **real defect** (clock-dependent pure function),
  not a bad assertion. This Mac's clock also runs hours behind real time, which
  makes any unpinned-`now` test flaky.
- The "caps the fold at the requested limit" test built 12 identical fixtures;
  once collapsing worked they became 1 row. Rewrote with six distinct stages.
- Ordering test had the same problem — gave the two runs different gate stages
  so they stay separate rows.
