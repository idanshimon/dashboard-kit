# Verifying compact, customizable action briefs

## Establish the evidence and settings contract

1. Trace authorized data → deterministic preview → initial evidence pages → optional external-context query → generated narrative. Document each stage's ranking, caps, clock and missing-source handling; a full source snapshot does not mean the model receives every row.
2. Define separate delivery, follow-through, hygiene and membership queues. Preserve source IDs, exact links, observed reason and suggested review action before inference. Deduplicate one record's multiple flags without losing the flags or pre-pagination counts.
3. Define one versioned preference schema for preview and server validation: preset, priority count, planning horizon, enabled sections, authorized account subset, detail and bounded optional-context windows. Reject unknown fields and invalid values; UI validation is not an authority boundary.
4. Specify preset defaults and precedence explicitly. Test that changing a preset/horizon changes real candidate selection, and that an explicit cleanup preset can change emphasis without changing facts or metric denominators.
5. Bind stored preferences to the viewer and validate subsets against the actual records in the current authorized snapshot. An empty dashboard filter means the loaded full scope, not permission to accept arbitrary selected IDs. Inspect picker values before wiring them to the schema: family/aggregate IDs are not record GUIDs. Derive a record-ID picker or an explicit validated mapping; do not weaken the schema to accept display-layer IDs. Pin normalized settings to initial evidence and subsequent allowed tool retrieval; otherwise a later model tool call can silently restore unfiltered evidence.
6. Separate current edits from saved-result settings. Changing settings must not start generation or external retrieval. A conflicting active job must be refused or clearly identified as using its original settings, not silently returned as newly configured.
7. Keep raw task descriptions and external responses out of durable source receipts when only IDs, links, counts, settings and final prose are required. Test the actual saved artifact as well as the inference payload.
8. Exercise a non-default priority count, disabled section, narrow account subset and altered context window through the real orchestration boundary. Inspect initial evidence, tool allowlist, follow-up retrieval, external-query accounts/window and assembled prompt. A persisted preference object does not prove the model used it; legacy prefetch and hardcoded count instructions can contradict an otherwise correct projector.

## Producer-to-template contract checks

1. Inspect a small real authorized payload before designing fixtures. Use the actual category/date/status fields; resolve activity account context through its exact regarding milestone rather than guessing from the title. If every real activity suddenly gains the same missing-field flag, inspect the field mapping before declaring a mass hygiene problem.
2. Trace the producer of each gap collection before labeling its members. Opportunity/deal-team absence is not verified milestone-team absence; require explicit evidence for the exact relationship and preserve unknown independently.
3. Exercise the actual browser template with the shared projector's output shape. If source links are an object map, convert with `Object.entries` into explicit `{kind,url,label}` rows; iterating it as an array can yield undefined keys and broken anchors while helper tests remain green. Assert rendered hrefs and stable keys, not just the existence of a URL-building helper.
4. Guard template expressions independently of visibility. Alpine `x-show` hides an element but still evaluates its `x-text`; a null saved-settings object must be safe during initial load and legacy-result rendering. Prefer a null-safe formatting helper and test both states in the actual browser.
5. Capture CDP `Runtime.exceptionThrown` when a page reports only generic `Script error.`; inspect the expression and stack before changing unrelated layout or data code.
6. Report the chosen priority count against the deduplicated candidate population, not against an already-truncated priority array. Keep per-queue counts separate when one record can carry multiple issue types, and make reason text use the selected horizon instead of a hardcoded default.

## Ticker lifecycle and interaction proof

1. Load with rotation saved ON before asynchronous data arrives. Prove zero/one → multiple items starts exactly one timer without hover or tab changes. A timer-helper test does not establish framework wiring.
2. Move focus from signal text into toolbar/settings and then outside the panel. Pause across the whole panel; inspect `relatedTarget` to distinguish internal focus movement from leaving.
3. Toggle reduced motion in both directions, scroll offscreen/back and background/restore the document. Subscribe to change events: a condition checked only inside an already-stopped timer cannot restart it.
4. Remove the real framework component. Confirm teardown invokes cleanup, clears timers/listeners/observers and invalidates late responses; calling a cleanup helper only in unit tests proves too little.
5. Measure the entire compact panel in idle, running, failed and completed states. A child height cap does not constrain a retained title, stepper or answer wrapper. Hidden should remove the content shell, not substitute another tall shell.
6. Assert actual viewport width, then open settings at the narrowest breakpoint. Measure both popover edges, control hit targets and word wrapping before screenshot review. Scroll to the changed component; header-only captures cannot verify it.
7. Exercise expand/compact/hide/restore, manual previous/next, settings toggle, Escape with focus restoration, outside dismissal and reload persistence. Record generation POSTs and assert zero from every presentation/settings interaction.
8. Observe at least one real slow rotation, then stop it with the user control. Keep text changes out of repeating screen-reader live announcements; job progress remains independently driven by actual server stages.

## Review and release evidence

- Resolve reviewer claims against the production producer, not sparse fixtures. Missing attribution in a fixture is not proof the real field is absent.
- Reject a PASS verdict with unresolved findings. Reproduce observations independently, including stale reports whose overall verdict has been superseded.
- Use complete source populations or disclose the intended shortlist; do not inherit an unrelated presentation layer's first-page cap.
- Compare identical source inputs when claiming unrelated outputs remain unchanged. Choose a replay harness whose expected delta matches this change; a historical harness requiring a changed metric is inappropriate for a no-metric-change release.
- Reconcile OpenSpec status against verified merge/release evidence and retain pending acceptance criteria. Schema validity, local tests, browser acceptance, live-model behavior and installer publication are separate claims.
