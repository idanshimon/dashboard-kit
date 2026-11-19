# Session 2026-07-26 — attention-queue redesign, worked example

Concrete detail behind the rules in SKILL.md. Codebase: a Next.js operator
dashboard over a governed decision ledger (`ledger-insights-ui`).

## The audit findings, verbatim

Screenshotted `/`, `/runs`, `/decisions` on the deployed Container App.
`/` returned a 369KB PNG (real content, not the error screen).

1. **Spec violation.** The dashboard opened with a gradient hero — headline
   *"Governed agentic SDLC, made auditable."* plus a marketing paragraph and an
   "Architecture" explainer of the product's own four planes. The repo's
   `DESIGN.md` Do's-and-Don'ts contains, literally: *"❌ Don't add a hero
   section, marketing copy, 'join the future' CTA, gradient backgrounds… This is
   an operator dashboard, not a landing page."* The first two sections of the
   operator dashboard were pitch material.
2. **No attention surface.** `/runs` showed 50 runs — **24 failed**, 3 live — as
   a flat reverse-chronological table. The two `awaiting_gate` rows, the only
   ones literally requiring a human, sat at rank 14 and 15 beneath eleven
   failures. The KPI strip read "10 done · 3 live · 24 fail" as passive,
   non-clickable text. A ~50% failure rate was the most important fact in the
   system, rendered in 9pt grey.
3. **Nav as architecture diagram.** Sidebar sections were *Pipeline Plane*,
   *Ledger Plane*, *Standards Plane*, *Agent HQ* — the implementer's model. Four
   sibling entries (Decisions, Decision Map, Precedent Lineage, Run Flow) were
   four views of one dataset competing as four destinations. 15 items, none
   named "what needs you."
4. **Theme drift.** `#001018` (primary-button foreground) hardcoded in
   `button.tsx`, `sidebar.tsx`, `assistant-panel.tsx`, `teaching-signal-bar.tsx`
   with no `onPrimary` token. `#1A1520` and `#475569` appeared in a graph page
   and were not in the token set at all. 78 total hex literals, ~75 in canvas
   (Cytoscape/react-flow) pages where hex is forced — a legitimate exception the
   spec never documented.

## The classifier bug worth remembering

First implementation guessed the flag mechanism:

```ts
const isFlagged = entry.status === "demoted" || entry.decision_kind === "reject";
```

Both fields were wrong — `status` didn't even exist on the type. The real
mechanism was a dedicated discriminator on `runtime_kind`:
`"decision_flagged"` and `"class_paused"`. Grepping the `runtime_kind` union in
`types.ts` before writing the classifier would have caught it in seconds. A
wrong guess here yields a permanently empty queue that *looks* like good news.

`class_paused` deserved its own plain-language row — "Autopilot is paused for
`auth-policy`. Every run hitting this class now waits for a human." — because a
paused class silently slows every future run and nothing else surfaces it.

## The clock-skew test failure

`buildAttentionQueue` ranking test asserted
`["blocked","failed","flagged","stalled"]` and got `["blocked","failed","flagged"]`.
Cause: that one test forgot `{ now: NOW }`, so the module used `Date.now()`
while fixtures were built from a pinned `NOW`. On a machine whose clock runs
behind, the stalled item fell outside its threshold and vanished. 20 tests
passed, 1 failed — the failing one was always the time-thresholded case.

Fix: thread `now` explicitly through every call in every test, and derive all
fixture timestamps as `new Date(NOW - msAgo).toISOString()`.

## What shipped vs. what didn't

Proven: `src/lib/attention.ts` + `src/lib/attention.test.ts`, 21/21 green.
Written but unverified (session ended before `tsc`/full suite/screenshot):
`components/domain/needs-attention.tsx`, rewritten `app/page.tsx`, `KpiCard`
gaining an optional `href`. Not started: triage-grouped runs page, nav collapse
to verbs, `onPrimary` token + canvas-exception documentation.

Reported to the user split into verified / written-but-unproven / not-started
rather than as "done" — the honest split is the deliverable when a session runs
out of room.
