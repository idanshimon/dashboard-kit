# Exact-URL deployment and real interaction proof

A production deploy is not complete merely because the CLI says READY or the project's canonical hostname serves the new build. A user-supplied alias can still point at an older deployment of the same app.

## Verify the address the user actually uses

1. Before deployment, record the requested URL, linked project and a marker unique to the new build. Distinguish local build, cloud build, project hostname and legacy/custom alias.
2. Build and test locally; if proving the hosting install/build path, deploy from source. A prebuilt upload does not exercise remote dependency installation.
3. Read the exact user URL after deployment and assert the marker and requested content. Also read the canonical project URL; disagreement is an alias/routing issue, not proof that the code failed.
4. Inspect the alias target. For the exercised Vercel case:

       vercel alias ls
       vercel alias set <verified-ready-deployment-host> <user-requested-host>

   Reassignment must remain within the user's requested app/domain **and access-control scope**. Do not alter unrelated domains or replace a protected preview URL with a production alias that bypasses its protection. Test cold unauthenticated access to the proposed alias before sharing it. Read back the alias after writing: Vercel's authenticated GET `/v4/aliases/<hostname>?teamId=<team>` returned deploymentId and projectId. Compare them to the actual READY deployment, then fetch the user URL again.
5. Test all requested routes and at least one decisive interaction on THAT production URL. An HTTP200 proves routing, not hydration. Do not claim success on a CLI message without read-back.

A manually assigned alias may require the same update on future deploys; inspect project-domain configuration rather than assuming it advances automatically. Likewise, a CLI deployment does not prove GitHub auto-deploy is connected. Inspect the actual project link before promising push-to-deploy.

## Branch-aware explanatory artifacts

1. Build an acceptance matrix of narrative step × normal/exception path × role × viewport. Exercise the actual controls with HTTP(S) blocked for bundled artifacts, persist captured-state records, and verify reload/deep links reproduce the selected path and open evidence dialog. These tests qualify the explanatory artifact, not the depicted backend.
2. Check branch semantics in navigation as well as body text. A missing-evidence branch must change completed-sounding step labels, history and downstream outcome together; a correct “not ready” card still contradicts a stepper implying departure already occurred. Add explicit text assertions for the branch's later steps.
3. Derive counts from the displayed case and test singular/plural labels. Keep role selection from changing shared facts, and distinguish source owner, task state and evidence freshness. Do not combine sponsor/operator labels when the explanation depends on their different authority.
4. Inspect short mobile steppers for intentional navigation rather than accepting a technically contained strip. Prefer wrapped steps when partial offscreen labels look broken; otherwise provide an obvious scroll affordance and keep the active step discoverable. Measure secondary evidence controls as real hit targets, not just readable text.
5. Re-render after the semantic fixes and inspect the relevant states with narrow vision questions: ask whether missing evidence prevents completion, capacity release and measured-value claims, and whether text clips. Avoid requesting a full image inventory when a defect check is sufficient. Repeat verification after assembling separately built illustration and narrative components.

## Three different kinds of QA evidence

- Numerical/unit gates: computations and explicit invariants. Preserve source quotes separately from recalculated values.
- Rendered route sweep: derive the route inventory; collect per-route/per-viewport JSON with status, heading, body text, console exceptions, broken images and document overflow. Persist batches, assert collected count equals expected count.
- Interaction and visual proof: change controls and verify dependent output, inspect screenshots, exercise navigation and saved preferences. A contact sheet is broad-layout evidence, not proof of tiny financial numbers.

The exercised financial UI checks covered model selection, APR, cash due, taxes, mileage and resale extremes; the verdict flipped at low/high resale and after raising APR. Mobile menu opening/route closing, a checkbox and reload persistence were also tested. Sub-navigation tabs can hide substantial content: enumerate actual hrefs and verify distinct populated bodies, not just the default route.

Use screenshots at full size for dense text and long identifiers. Separate a viewport crop from actual container clipping. A mobile screen that technically fits can still obscure the comparison: show the decisive headline values together and place the requested option first. Avoid repeating a long explanatory paragraph above every card.

For fixed mobile navigation, test **reachability**, not merely whether Playwright thinks the element is in the viewport. `scroll_into_view_if_needed()` can leave a cell behind a fixed bar because it is already inside the viewport rectangle. Explicitly call `element.scrollIntoView({block: 'center'})`, wait for layout, and assert the target bottom is above the navigation top using `getBoundingClientRect()`. Inspect an actual viewport screenshot at that scroll position. A sticky header appearing in the middle of a full-page composite is not sufficient proof of an overlap defect; distinguish capture artifacts, harness omissions and genuine insufficient bottom padding.

## Reproduce and repair covered filter controls

1. Use a dedicated browser target per QA workstream and persist its target ID separately. Another actor navigating a shared target can turn a layout assertion into a test of the wrong route. Assert the URL and expected control count, then wait for route-specific controls rather than only `document.readyState`.
2. Preserve a failing geometry test before editing: compare each tab's `getBoundingClientRect()` with the adjacent selector, requiring no positive intersection on both axes. Check `document.elementFromPoint()` at each tab center and require the tab or its descendant, because visible text can still be covered by another control's hit area.
3. Trace shared classes through all consuming pages and later CSS/media-query overrides. Scope queue-specific fixed grids to a queue modifier; give segmented tabs intrinsic width and let the neighboring selector wrap below them at narrow widths. Do not use z-index to conceal the collision: it only changes which control is inaccessible.
4. Rebuild, then click every tab and assert selected state. Exercise the neighboring case selector and compare the displayed records with the same API snapshot filtered by the selected ID. Inspect desktop/mobile screenshots and recheck the queue after changing shared styling.

## Isolate a frontend hotfix from unfinished backend work

1. Verify the previous release archive against its recorded SHA-256 before using it as a baseline; stop if provenance cannot be established.
2. Build the new frontend and create a separate archive retaining every old non-frontend entry. Replace the entire frontend asset subtree, not just matching filenames, so stale content-hashed assets are removed.
3. Apply the deployment artifact allowlist to replacement files and byte-compare every retained backend entry against the baseline. A whole-worktree packager can silently include another worker's unfinished backend code.
4. Exercise the exact assembled package locally, then use the normal validated deployment flow. Read back the new asset identity and repeat the exact hosted control tests before reporting the fix as live. Keep locally verified, packaged and deployed statuses distinct.

## Test the wire contract before trusting independent suites

Before splitting frontend/backend work, share one concrete request/response example
and the exact job-status enum. Green suites written against different contracts do
not prove integration: an editor can send asset IDs and in/out points to a renderer
expecting file paths and start/end, or hide a completed export because it checks
`done` while the backend returns `succeeded`.

1. Read the actual backend schema and response shape, then place conversion in one
typed boundary adapter. Preserve every effective setting, reject missing references,
and strip editor-only fields before sending a strict payload.
2. Round-trip a backend-shaped fixture through the adapter; do not construct every
fixture from the frontend's own types, because that repeats its assumptions.
3. Render completion/failure components with backend-shaped responses. Assert that
success exposes the playable/downloadable artifact rather than a permanent loader.
4. Reconcile returned IDs after saving or undoing: regenerated identifiers can leave
selection pointing at a nonexistent item even though persistence succeeded.
5. Exercise import → edit → save → reload → export through the live application. Keep
unsaved state, saved revision, source preview, and exported revision visibly distinct;
a stale preview must not masquerade as the latest edit.

For media controls, verify the exported file as well as the UI state: probe duration
and dimensions, sample clips on both sides of a cut, measure audio gain/mute, and
extract subtitle streams. An accepted subtitle field is not proof it was rendered;
a source timestamp offset after trimming is not automatically a timing defect.
Run the combined suite and report its measured count instead of adding worker-reported
totals, which can overlap or include different snapshots of the code.

## Server-served helpers and reactive dialog verification

1. Assign ownership of both a new browser helper and its server asset route before splitting implementation. Load the tested helper before the app and request its exact URL to verify JavaScript content; a successful HTML fallback is not a served helper. Do not inline a second copy to avoid crossing a worker's file boundary: duplicate implementations disconnect unit tests from production behavior.
2. Wait for the containing page's loading state to settle before testing dialogs or taking screenshots. Assert the selected scope, expected/loaded membership and absence of source errors; then require `document.fonts.status === 'loaded'`, decoded images and completed chart rendering. For ECharts, inspect each visible instance's populated series and `getZr().animation.isFinished()` rather than relying on a canvas element alone. Require several stable observations within a bounded wait, then await the framework render tick (`await Alpine.nextTick()` for Alpine). Save these readiness facts with the screenshot. A refresh can replace dialog DOM, and a same-turn read can reflect an old filter; neither alone proves a defect. If completeness cannot be achieved, label the capture partial rather than claiming fully loaded.
3. Serialize reactive state inside the browser with `JSON.stringify(...)` before returning it through CDP. Nested framework proxies can appear as empty objects when returned directly, creating a false missing-data diagnosis. Check actual scalar fields, rendered rows and endpoint JSON together.
4. Test detail filters against the unchanged original fraction, not only a filtered row count. Inject absent or contradictory detail into browser state to verify the unavailable path, clearly labeling that check as a fixture rather than a live-source result. Keep explicit no-membership distinct from unknown membership.
5. Exercise native dialog Escape, focus return, scroll reachability and bookmark restoration after rendering settles. Set `margin: auto` explicitly when global CSS resets native dialog margins; inspect `getBoundingClientRect()` on desktop and mobile to verify placement rather than assuming browser defaults survived.
6. Treat suspected clipping as a measurement task, not a reason to dismiss the screenshot. Keep `Emulation.setDeviceMetricsOverride`, layout measurement, scrolling and `Page.captureScreenshot` on the same live CDP session; disconnecting between them can discard the override and make measurements describe a different viewport from the image. Do not treat a CLI `--window-size` or PNG width as proof of the CSS viewport; a capture crop can cut text laid out at another width. Set `Emulation.setDeviceMetricsOverride` with explicit `width`, `height`, `deviceScaleFactor` and `mobile`, navigate, await the target section and `document.fonts.ready`, then scroll the section into view and capture with `Page.captureScreenshot`. Record the measured viewport alongside the image before changing CSS. Compare `document.documentElement.clientWidth`, requested emulation width and `scrollWidth`; an enlarged `innerWidth` can create a false pass. When emulated pixels and CSS widths disagree, record `Page.getLayoutMetrics()` including `cssVisualViewport.zoom`, CSS viewport and content sizes before editing CSS. Browser zoom and scrollbar width change the coordinate comparison; neither alone proves page overflow. Do not weaken the assertion or prescribe a zoom-reset command without testing the resulting viewport. Walk each target's `parentElement` chain and inspect `getComputedStyle(parent).overflowX/overflowY` plus its client-area bounds. Intersect the viewport with every clipping ancestor (`clip`, `hidden`, or a scrollport): fitting the viewport does not prove fitting a narrower panel. `scrollWidth === clientWidth` on the button proves only internal text fit, not ancestor visibility.
7. Scroll each control to a usable position, await layout, and test `document.elementFromPoint()` at its center and just inside both horizontal edges. Require the control or a descendant; if a sticky header intercepts it, adjust scroll and repeat rather than accepting a center-only pass. Inspect a readable crop showing the complete label and both border corners. When geometry and vision disagree, measure clipping ancestors and hit targets before declaring either instrument wrong.
8. If rectangles fit but text still overflows, walk text nodes with `document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT)`, use `Range.selectNodeContents(node)` and inspect `Range.getClientRects()`. Allow long metadata to wrap. Scope responsive fixes to the affected component; if secondary columns must collapse, preserve access to their information or filtering. Before changing a table ancestor from `overflow-x: clip` to `auto`, inspect its sticky-header contract: creating a scroll container can detach headers from viewport scrolling. Preserve a failing reachability probe and verify the chosen responsive structure instead of globally changing overflow. Re-run the same assertions at phone, intermediate/tablet and desktop widths, plus narrow split panels; a phone-card fix can leave the intermediate table clipped. Measure the actual container rather than using viewport width alone.

## Verify the frontend when production content is unavailable

1. Read the producer's typed contract and check the actual content file before building tests. Keep the production unavailable/refusal state intact; do not invent biography, metrics or citations to populate it.
2. Put synthetic contract records under `tests/`, label visible names and exported artifacts `TEST ONLY`, and inject them with Playwright `page.route('**/portfolio.json', ...)`. Never import the fixture into production or overwrite the producer's file. Compare that file's hash before and after the suite to prove isolation.
3. Serve the real production build on a dedicated loopback test port. Await its readiness signal, exercise real components and controls, capture console errors, and terminate the test server in `finally`. Rebuild after fixes before rerunning browser tests.
4. Exercise valid, absent, placeholder and malformed content separately. Include missing evidence references, duplicate IDs, dangling relationships, null values, signed chart values and an account containing both a known zero and an unknown amount. Assert the rendered labels, units, scope and dates, not only bar dimensions. Track known-value count separately from numeric sum: a sum of zero does not mean every value is missing.
5. Capture all requested routes at desktop and narrow mobile widths; persist the expected route inventory and measured results. Label fixture screenshots and PDFs as test evidence, not a delivered personal artifact. A passing isolated suite leaves real-content validation explicitly pending.

For a server-side PDF renderer, browser interception on the test page does not affect the renderer's separately launched browser. Use an ephemeral loopback proxy that supplies the fixture at the data endpoint and forwards other requests to the real built app; invoke the actual renderer against that proxy. Inspect the resulting PDF's text, pages and rendering, and keep its test-only identity visible.

## Validate downloads and privacy at the wire

- Reject successful HTML fallback responses before announcing a PDF download. Check HTTP status, `Content-Type: application/pdf`, and the `%PDF-` signature before creating the download Blob. Test a 200 HTML response as a refusal case, then exercise a genuine generated PDF; a `.pdf` filename is not proof of PDF bytes.
- Normalize extraction whitespace for semantic PDF assertions (`text.replace(/\s+/g, ' ')`), because `pdftotext` can separate adjacent words even when they share a visual baseline. Before changing print CSS for an apparent line-break defect, inspect `pdftotext -bbox file.pdf -`: matching word `yMin`/`yMax` positions distinguish extraction artifacts from actual wrapping. Keep pagination and rendered-page review separate from text-presence checks.
- Capture resource URLs with console failures (`message.location().url`) and failed HTTP responses during the real-content sweep. Fix missing local assets such as an undeclared favicon instead of filtering their errors out; mocked browser routing can suppress requests that occur in a genuine production visit.
- Preserve confidentiality, snapshot date, scope, units and source identifiers in exports. Keep null CSV numeric cells empty rather than coercing them to zero, and neutralize spreadsheet formula prefixes. Assert exported file contents, not just that a download event fired.
- Send hostile Host/Origin headers using a transport that actually transmits them. Use Node `http.request` or an equivalent raw HTTP client for Host-header checks; a high-level Fetch implementation can normalize or discard the override and produce a false server-security failure. Exercise cross-site requests and disallowed methods separately.

## Private-link access and lock recovery

1. Start with the public page already open, then activate its private fragment link. Test this separately from a fresh navigation: changing only the fragment does not remount React, so mount-only unlock effects miss the new credential. Handle `hashchange` or a subscribed access revision, and cancel stale asynchronous unlock results.
2. Verify successful unlock removes the fragment from the address bar, retains only the intended session access state, and does not transmit the key in requests, headers, telemetry or exports. Test missing, malformed and incorrect keys without fabricating a record.
3. Open a real private artifact, activate Lock, then reopen through the original access link in both the same tab and a fresh tab. Assert the artifact returns unchanged; disappearance from the UI is not deletion from storage.
4. Inspect the caller as well as the key-clearing helper. A lock handler may also remount a form and discard unsaved notes. Assert the effect on session drafts and opted-in persistent notes, and make the label, warning and recovery copy match that behavior. Say which record was not deleted rather than offering a blanket reassurance.
5. Make the locked state explain its recovery path. For support handoff, supply the authorized private link landing on the requested view, not the public locked shell. Do not put access-bearing URLs in committed tests, screenshots, skills or public QA reports; load credentials from excluded local state.
6. For routine encrypted-record updates, verify existing access still opens the new revision unless rotation was intended. Compare deployed ciphertext and build identity, then assert corrected source-attributed values are present and superseded claims are absent from the live view and any export.

## Findability and direct-link proof

- Match the user's recognizable name to the actual UI label, including domain synonyms where helpful; a correctly implemented entry is still hard to find when only unfamiliar terminology is visible.
- Keep the selected item or selector ahead of long explanatory panels. Test the user's path from navigation to the requested content rather than checking only that the text exists somewhere in the DOM.
- Exercise the exact deep link and inspect the landing viewport. Selecting a hidden or far-below-the-fold section in URL state is not sufficient proof of useful navigation; make the selected content visibly discoverable without requiring the user to search again.

## React state patterns exercised during this verification

For shared URL state, test a control in a child view whose result is rendered by a parent, such as a research row opening a root-level detail drawer. `history.pushState` and `replaceState` fire neither `hashchange` nor `popstate`; updating only one hook instance leaves sibling subscribers stale even though the address bar is correct. Use a shared external store or dispatch a dedicated route-change event after each programmatic history write, subscribe every consumer, and clean up listeners on unmount. Verify click → dialog, reload → same dialog, filters, graph selection and browser history.

For presentation shortcuts, activate presentation with a real click before pressing arrows or Escape. Focus remains on the trigger button; excluding every `BUTTON` from the keyboard handler silently disables the advertised shortcut. Suppress navigation for editable fields and open dialogs without suppressing ordinary navigation buttons.


For browser-persisted preferences without a hydration mismatch: a `useSyncExternalStore` hydration gate with stable client/server snapshots can render defaults on the server, then remount a keyed inner view whose lazy initial state reads validated localStorage. Persist changed choices in an effect; do not synchronize every initial state setter directly from an effect. Validate stored IDs against current records, and version the storage key when the default shortlist changes. Test both a fresh visit and reload after changing the view.

For mobile navigation that must close on route change: key the stateful navigation child by pathname; its state resets and scroll-lock cleanup runs when identity changes. Also close on link clicks so clicking the already-active route closes the sheet. Exercise Escape, body-scroll restoration and route clicks; lint alone is not proof.

Exclude generated hosting output (for example `.vercel/**`) from source linting, not application source. Keep real type/lint failures visible. After the final code edit, rebuild before browser testing; an old running server may still hold the previous modules. Verify the new process and a new-build marker.
