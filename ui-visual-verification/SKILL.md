---
name: ui-visual-verification
description: "Use when verifying or finishing user-facing UI. Prove rendered routes, real interactions, mobile layout and the exact production URL; distinguish numerical tests, visual inspection, runtime behavior and deployment evidence. Includes hydration, empty surfaces and stale-build diagnosis."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [qa, ui, frontend, verification, vision, screenshots, honesty]
    related_skills: [dogfood, nextjs-acr-build-public-env, agentic-sdlc]
---

# UI Visual Verification

For SPA bookmarks that alias a parent route, verify both the selected tab and its rendered panel on cold entry, then navigate to another view of the same parent and use actual browser Back. A router may intentionally skip remounting same-route transitions.

Verify heading/index, scroll position and image hash for each screenshot; DOM state alone does not prove captured pixels. If reload/focus restoration defeats scrollTo(0,0), open the same URL in a fresh isolated page, wait for readiness and two animation frames, then verify hero bounds and pixels. Never label a repeated mid-page capture as a verified hero.

**Verify the exact URL, clipped hit targets and recovery.** Isolate QA tabs; preserve drafts. For the user's screenshots, use real authorized data—not fixtures—and wait for data, fonts and charts. See `references/exact-url-deployment-and-interaction-proof.md`.
<!-- canvas drag/zoom: references/canvas-chart-interaction-verification.md; phone 390px proof (headless clamps to 500px; CDP emulation + scrollWidth probe): references/phone-viewport-capture.md -->

## Purpose

Green tests prove the code does what the test says. They cannot prove the screen
is usable. This skill covers the last mile: actually looking at the thing before
claiming it works.

**Load this whenever you are about to say "done", "fixed", or "deployed" about
anything a human will look at.**

> **If you are verifying a single-file HTML artifact, read
> "Structural HTML validation certifies NOTHING" below FIRST.** Tag-balance and
> DOM-id checks pass identically over a page that renders nothing at all, and
> that exact false-pass has been reported to a user four times in one session.

## The core rule

`tsc --noEmit` + `vitest` + `pnpm build` + HTTP 200 is the **entry** requirement,
not the finish line. A tested component is not complete until it is mounted on
the real route, fed by the real producer, and *seen*.

Report in four buckets, never collapsed into "done":

- **Verified live** (screenshotted on the public URL)
- **Verified locally** (screenshotted on a local standalone build)
- **Implemented but not proven** (gates green, no eyes on it)
- **Blocked / unknown**

Saying "verified by tests, not yet seen" is honest and more useful than a
confident overclaim. Never report a gate you ran as if it were an inspection you
didn't do.

### PROVE a failing test is pre-existing — never assert it from the traceback

Reproduce a suspected baseline failure in a separate worktree or immutable copy of the exact comparison revision. Never stash, reset or overwrite protected dirty input to obtain a baseline. Use the same runtime, dependencies and selected case; preserve both reports. An identical baseline failure supports a pre-existing classification, not a waiver of a mandatory in-scope defect. Report current passes/failures and the baseline evidence separately.

### Green gates certify SHAPE, not correctness — expect them to pass on broken work

After type checks, tests and builds pass, exercise the rendered routes with their actual data and inspect geometry, contrast and content presence. Treat green gates as the start of visual verification, not its result: they can pass while graphs are empty or fitted against stale container measurements. Report test results separately from observed usability.

### A 200 proves a server answered — not that it is running YOUR build

Same session, and the failure that produced a false "it's live, go look":
three routes were curled, all returned `200`, and that was reported as
verification. The dev server had never started — `predev`'s port check found the
port already held by a **stale process from an earlier session**, the launch
exited, and every request was answered by a build predating all the changes.

The tell was in the process, not the response:

```
process(action='poll', session_id=...)
  status: exited
  "✗ port 3005 is already in use"  /  EADDRINUSE
```

Rules:

- **Poll the process you started; do not infer it from the port.** A background
  launch that died still leaves something listening, and it answers `200`.
- **`curl` a route that only exists in your new code.** A 404 on a brand-new
  route means the server predates your change — the same tell as the stale-dev-
  server section below.
- Verify the holder's command and cwd before cleanup; stop only the owned test process and recheck its exit and port. Never kill every port holder or a broad process name. Start fixture servers with tracked `terminal(background=true)`, then run health checks/tests in foreground calls; do not embed shell `&` in a foreground command.

## The loop

```bash
# 1. Real production build — NOT the dev server.
#    Build-time inlining, prerender, and bundling differ from dev.
pnpm --filter <app> build

# 2. Serve the standalone output against REAL data.
#    LOCATE server.js — do NOT assume its path. In a monorepo/workspace build it
#    is nested under the inferred workspace root, e.g.
#    .next/standalone/projects/<org>/<repo>/apps/<app>/server.js
#    Assets must be staged BESIDE that server.js:
SA=$(dirname "$(find .next/standalone -name server.js -not -path '*/node_modules/*' | head -1)")
cp -r .next/static "$SA/.next/" && cp -r public "$SA/"
TOK=$(az containerapp secret show -n <ui-app> -g <rg> \
      --secret-name <token-secret> --query value -o tsv)
(cd "$SA" && PORT=3012 <BACKEND_TOKEN_VAR>="$TOK" node server.js &)   # background=true

# 3. Screenshot headless
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --no-sandbox --window-size=1600,1200 --virtual-time-budget=18000 \
  --screenshot=/tmp/x.png "http://127.0.0.1:3012/"

# 4. DOWNSCALE before vision — see "Budget your vision payloads" below.
sips -Z 1200 /tmp/x.png >/dev/null

# 5. Actually read it
vision_analyze(image_url="/tmp/x.png", question="<specific, falsifiable>")
```

**Sanity-check the PNG size.** ~200KB = real content. ~17KB = you screenshotted
an error page and are about to "verify" a crash.

**If the server will not come up at all**, the blocker is usually one of four
repo-structural traps rather than your code: the lockfile's package manager
(`pnpm` vs `npm`), a `prestart`/`predev` hook checking a *hardcoded* port that
ignores your `--port`, `next start` refusing to run under `output: standalone`,
or the nested standalone `server.js` path. Each kills the launch while something
else keeps answering — **poll the process, never infer health from the port.**
Full diagnosis + working recipe:
[`references/serving-a-local-build-for-inspection.md`](references/serving-a-local-build-for-inspection.md),
which also covers the `useSearchParams()`-needs-Suspense prerender failure that
`tsc` cannot see.

## 🚨 Structural HTML validation certifies NOTHING — it never executes the JS

Balanced tags, every `getElementById` target present in the DOM, every called
function defined, "18 of 19 glossary keys used" — these feel like verification
and are the exact shape of check that passes over a **completely dead page**.
None of them run the script.

Verified 2026-08-28 (Mission Control dashboard, single-file HTML): a page was
reported as verified **four separate times** across a session on the strength of
a Python `HTMLParser` tag-balance pass plus regex cross-checks of DOM ids and
glossary keys. Every one came back clean. When the user finally asked for a
visual check, the page rendered **nothing at all** — no KPIs, no charts, no data,
`S` undefined — because a JavaScript `SyntaxError` had killed the entire script
on load. `document.querySelectorAll('svg').length` returned 3 (the static nav
icons) while 11 were expected.

**The rule: a check that does not EXECUTE the code is not verification of the
code.** Tag balance is a property of the markup; the page working is a property
of the runtime. Never report the second on evidence of the first.

Cheapest possible execution check, before any screenshot — parse the script the
way the browser will:

```
browser_cdp(method="Runtime.evaluate", target_id=<id>, params={
  "awaitPromise": True, "returnByValue": True,
  "expression": """(async()=>{
    const t = await (await fetch('index.html?x='+Date.now())).text();
    const m = t.match(/<script>([\\s\\S]*)<\\/script>/);
    try { new Function(m[1]); return 'SYNTAX OK' }
    catch(e){ return 'SYNTAX ERROR: ' + e.message }
  })()"""})
```

`new Function()` compiles without running, so it is safe and instant. When it
fails, the message alone (`Unexpected token ':'`) does not locate anything —
**bisect by line** rather than reading the file:

```js
const L = js.split('\n'); let lo = 1, hi = L.length;
while (lo < hi) {
  const mid = (lo + hi) >> 1;
  try { new Function(L.slice(0, mid).join('\n')); lo = mid + 1 }
  catch (e) { /Unexpected token ':'/.test(e.message) ? hi = mid : lo = mid + 1 }
}
return { firstBadLine: hi, ctx: L.slice(hi - 4, hi + 2) };
```

That returned the offending line and three lines of context in one call, after
the error message itself had pointed nowhere useful.

Post-load assertions that would also have caught it, and cost one call:

```js
JSON.stringify({
  dataLoaded: (window.S && S.data) ? S.data.accounts.length : 'NO DATA',
  kpis: [...document.querySelectorAll('.kpi .val')].map(v => v.textContent),
  svgs: document.querySelectorAll('svg').length,   // compare to EXPECTED
})
```

**Assert a rendered count against an expected number.** `svgs: 3` looks fine in
isolation; `3` where the page draws 11 is the whole diagnosis.

### A patch whose `old_string` is a FRAGMENT can delete the line above it

Root cause of that syntax error, and a general hazard of string-replace editing:
the patch matched an object literal's first property line while the intended
target was the whole declaration, so `const KC = {` was silently removed and a
bare `seat_churn:'var(--bad)', ...` was left floating at statement position.

The edit reported success. The diff looked plausible. The file stayed
tag-balanced. Nothing surfaced until the page was opened.

- **Include the declaration keyword in `old_string`** when editing any object,
  array, or function literal — anchor on `const NAME = {`, never on a property.
- **After any patch to embedded JS, run the `new Function()` check**, exactly as
  the skill already mandates `node -c` after editing embedded CSS. Same class of
  defect, same one-call defence.
- Same family as the `re.sub` + `re.S` data-destruction trap below: an unreviewed
  scripted edit is only as safe as the assertion you run after it.

### Template expressions in the STATIC skeleton never evaluate

A single-file page usually mixes a hand-written HTML skeleton with sections built
by JS template literals. `${ex('cls','Risk distribution')}` inside a plain
`<h2>` in the skeleton is **literal text** — it renders on screen as the raw
source, in the middle of an otherwise polished dashboard.

Tag-balance passes. Every function exists. Vision catches it instantly.

Tell: any `${` surviving in the served HTML outside a `<script>` block.

```bash
grep -n '\${' index.html | grep -v '^\s*[0-9]*:\s*//' | head
```

## Budget your vision payloads — the loop can 413 your own session

This loop is vision-heavy by design, and vision payloads are the one thing
context compaction cannot evict. A multi-tab verification pass can silently
brick the session it is trying to validate.

**Always downscale before `vision_analyze`:**

```bash
sips -Z 1200 /tmp/*.png        # macOS, in place, ~4x smaller
```

Full-page retina screenshots run 320-450 KB *each*. Seven tabs is ~2.6 MB of
PNG, roughly 3.5 MB once base64-encoded into the request body. At 1200px the
defects this skill actually looks for — missing glyphs, clipped text, empty grid
voids, wrong nav position — are all still plainly visible.

**Other budget rules:**

- **One verification round per session**, or `/new` between rounds.
- **Capture the region, not the page.** Checking the nav bar? Screenshot the nav
  bar. Use a narrower `--window-size` rather than a full-page grab.
- **Batch-render then batch-downscale**, so you never hand a raw retina PNG to
  the vision tool by reflex.

**Do not assume `compression.enabled: true` protects you.** It does not, for
exactly this workload. The compressor's tool-result pruner handles the vision
message shape correctly, but it only walks messages *outside* the protected
tail (`compression.protect_last_n`, commonly 20). A verification loop takes its
screenshots back to back at the end of a session, so they are all "recent" by
construction and sit inside the protection window. The pruner walks past them.

Consequence: compression can be on, correctly implemented, and still let
megabytes of base64 reach the wire. Lowering `compression.threshold` does not
help — the threshold governs *when* a pass runs, not *what* it may touch.

Why this matters mechanically: the 413 from a provider gateway is a limit on
**serialized body bytes**, not tokens. Agent-side token estimators size the text
`content` field, while the base64 image rides in a separate sidecar and is
invisible to them. So the estimate stays small, text compaction "succeeds" while
changing nothing that matters, and the request fails identically on every retry
until the loop gives up. See
`references/vision-payload-budget.md` for the full mechanism, the diagnostic
queries, and the transcript of a session that died this way. For diagnosing one
after the fact, load `hermes-agent-loop-failure-diagnosis`.

**Ask falsifiable questions.** Not "does this look good" but "are the rows
DISTINCT or repeated?", "does the KPI show a number AND a percentage?", "is the
sidebar grouped by verbs?". Vague prompts get agreeable answers from vision
models.

**Use DOM queries for "did the code path run", vision for "how does it read".**
`browser_console(expression=...)` is ground truth for element counts and
computed styles; vision is for scannability, hierarchy, and layout.

## Pick a layout metric that can actually fail

A numeric geometry check feels more rigorous than a screenshot. It is not — it
is only as good as the failure mode it can express, and the wrong metric returns
a confident pass over a visibly broken screen.

Worked case (yoto-dash mobile nav, Aug 2026): a top bar had to fit five items on
one row. The check was `sidebar.scrollWidth > sidebar.clientWidth` — classic
overflow detection. It reported `false`, so the layout was declared fitting and
reported to the user as verified at 320px.

It was broken. The flex children had been pinned with `flex: 0 0 auto`, so under
pressure they stopped *shrinking* and started **overlapping** instead. Overlap
does not extend scroll width. The metric was structurally incapable of seeing
the defect, and the user had to report it back.

**Measure the thing you actually care about:**

```js
// Pairwise intersection — catches overlap, which scrollWidth never will.
const items = [...bar.querySelectorAll('.brand,.link,.foot')];
const R = e => e.getBoundingClientRect();
const collisions = [];
for (let i = 0; i < items.length; i++)
  for (let j = i + 1; j < items.length; j++) {
    const a = R(items[i]), b = R(items[j]);
    if (a.right > b.left + 0.5 && b.right > a.left + 0.5)
      collisions.push([items[i].textContent, items[j].textContent]);
  }

// Does the last item end inside the viewport?
const last = R(items.at(-1));
return { collisions, fitsInViewport: last.right <= innerWidth,
         scrollOverflow: bar.scrollWidth > bar.clientWidth };
```

Rules:

- **Assert `collisions.length === 0` AND `fitsInViewport`,** not just absence of
  scroll overflow. They fail on different bugs.
- **A geometry pass never replaces looking.** In this case the numbers said fine
  and one screenshot showed labels reading `cardsAdd tracksSettings`. Run both;
  the numbers localize the defect, the eyes find it.
- **…and when the two DISAGREE, measure before you patch.** The failure runs in
  both directions: a screenshot can also invent a defect the DOM does not have.
  Vision reported text "cut off at the right edge" on a mobile capture; three CSS
  fixes were applied before a CDP probe returned
  `{vw: 390, scrollW: 390, over: []}` — there had never been any overflow. The
  capture was taken with bare `--window-size` (no device emulation), so the media
  query never applied and the layout being photographed was not the layout that
  ships. **Resolution order: reproduce the claim as a number, then fix.** A
  reusable probe that enumerates every element whose `right` exceeds the viewport
  is in `references/headless-viewport-emulation.md`; run it against each route
  and each breakpoint rather than eyeballing a strip.
- **Check every auth/content state that changes item count.** Signed-out grew a
  "Sign in" button, which is what broke a bar that fit fine signed-in.
- **Check the narrowest real device (320px), not just your default.** And when
  you add a breakpoint that hides something, confirm the threshold — a 420px
  rule silently hid the wordmark on a 393px iPhone.
- **Bare `--window-size=390,844` is NOT mobile emulation** and will fake a
  clipping bug on a page that is perfectly fine. Measure `scrollWidth` vs
  `innerWidth` before you "fix" an overflow you only saw in a screenshot; capture
  capture with CDP `Emulation.setDeviceMetricsOverride` + `mobile: True`. Full
  recipe, the `--remote-allow-origins=*` websocket 403, and a worked case where
  three CSS fixes were applied to a non-bug:
  `references/headless-viewport-emulation.md`. Ready-to-run probe (exits non-zero
  on real overflow, so it works as a gate):
  `python3 scripts/overflow_probe.py <url> 390 844`.

  🚨 **This exact trap recurred 2026-08-26 despite being documented above** —
  worth understanding *why*, because knowing the rule was not enough to stop it.
  A vision pass reported "third column clipped at the right edge" on a
  `--window-size=430,1400` capture. Two rounds of CSS were shipped against it
  (fixed-column grid, then `min-width:0` + `overflow-wrap`) before anything was
  measured. The probe then returned `viewport 500 · scrollWidth 485 ·
  offenders: []` — **no overflow had ever existed**, and `vw` came back `500`,
  not the 430 that was requested, which is the tell that the flag never applied.

  The failure mode is that a *reported* defect feels like established fact, so
  the measure-first rule silently reclassifies as "already done". It is not:
  **the vision report IS the claim, not the evidence.** Enforce mechanically —
  when a capture-derived defect arrives, the first tool call afterwards must be
  the probe, before any edit. If the probe returns no offenders, say the defect
  did not reproduce and revert speculative fixes rather than keeping them
  "just in case" (they are unverified changes justified by a non-existent bug).
  Assert `innerWidth === requestedWidth` and `scrollWidth <= requestedWidth + 1` per route; mismatch may reflect bad emulation OR real content-driven viewport expansion.

## A screenshot is necessary but NOT sufficient — drive the interaction

The defect class this skill's screenshot loop cannot see: **the page renders
perfectly and does nothing.** If React never hydrates, the server-rendered HTML
is pixel-correct. Vision says "looks great." Every input accepts typing. Buttons
depress. Nothing is wired to anything.

Worked case (yoto-dash, Aug 2026) — cost three failed user logins and several
false "fixed" claims:

- User: *"i can save the client id and callback in the settings dont let me."*
- `curl -X PUT /api/settings` → **200 OK**, value persisted. API provably fine.
- Screenshot of the page → **flawless**. Form, labels, populated field, button.
- Actual cause: Next 16 blocks cross-origin dev assets by default. The app was
  reachable as *both* `localhost` and `127.0.0.1` (the OAuth callback needed
  either to work), so JS chunks returned **403** on the non-canonical host.
  React never hydrated. `onClick` was never attached. Save was a no-op with **no
  error anywhere** — not in the UI, not in the server log.

Testing the endpoint said "works" and was wrong. Screenshotting said "works" and
was wrong. Only a real browser, driving the control and reading the console,
found it.

**So: for any surface with a form, filter, toggle, or button, verify the
INTERACTION, not just the render.** Playwright, capturing console + failed
requests:

```js
const errs = [];
page.on("console", m => { if (m.type() === "error") errs.push(m.text()); });
page.on("pageerror", e => errs.push("PAGEERROR: " + e.message));
page.on("requestfailed", r => errs.push("REQFAIL: " + r.url() + " " + r.failure()?.errorText));

await page.goto(url, { waitUntil: "networkidle" });
await page.locator("#field").fill("value");
await page.getByRole("button", { name: /save/i }).click();
await page.waitForTimeout(1200);

// Assert the OUTCOME, not that the click happened.
console.log("success badge:", await page.locator("text=saved").count());
await page.reload({ waitUntil: "networkidle" });
console.log("persisted:", await page.locator("#field").inputValue());
console.log("console errors:", errs.length ? errs.slice(0, 5) : "none");
```

Rules that fall out of this:

- **`console errors: none` is part of the pass criteria.** A 403/404 on a
  `_next/static/chunks/*` asset means the page is inert regardless of how it
  looks. Treat any failed request for a JS chunk as a hard fail.
- **Assert a post-condition, never the click.** Reload and re-read the value.
  "The button was clickable" proves nothing; "the value survived a reload"
  proves the whole path.
- **Symptom→diagnosis shortcut:** user says a form/filter/button "does nothing"
  and shows no error → suspect dead hydration *before* application logic. Open a
  browser and read the console; do not re-read the handler.
- **`browser_navigate` cannot reach localhost** (blocks private addresses), so
  reach for Playwright or headless Chrome directly for local verification.
- Node-driven Playwright outside the project needs
  `NODE_PATH=<project>/node_modules node script.js`.

Corollary for multi-host apps: if your app is legitimately reachable at more
than one hostname (loopback aliases, a proxy FQDN), whatever framework setting
governs allowed dev/asset origins must list **all** of them. In Next 16 that is
`allowedDevOrigins: ["127.0.0.1", "localhost"]` in `next.config.ts`.

Multi-host apps are usually multi-host *because* of an OAuth callback. If that
is what you are chasing, load `oauth-pkce-web-login` — the same
`localhost` vs `127.0.0.1` split that kills hydration also silently breaks the
PKCE cookie round-trip, and that skill has the full diagnostic order.

## Before believing a fix failed: is your new code even running?

A verification loop is worthless against a stale process. Same session as the
hydration case above, this cost several cycles of re-fixing already-correct code
and two false "it's fixed" claims to the user.

Sequence: edited the file → restarted the dev server → old behaviour persisted →
concluded the fix was wrong → rewrote working code. The restart had died
silently with `EADDRINUSE` because **two** orphaned dev servers still held the
port, so every "restart" left the original stale process serving.

**The cheap tell: probe a route you JUST added.** If a brand-new endpoint 404s,
the running server predates your change — the problem is the process, not the
code.

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:PORT/api/health  # 404 = stale
lsof -ti tcp:PORT                       # often MORE than one PID
lsof -ti tcp:PORT | xargs -r kill -9
sleep 2; lsof -ti tcp:PORT >/dev/null && echo "STILL BOUND" || echo "PORT FREE"
rm -rf .next                            # drop the stale compile too
```

Also read the background process's own exit status instead of assuming it
started; a `status: exited` with `EADDRINUSE` in its log is the whole story.

**Companion tell — is the reported symptom even current?** If the user quotes an
error string that **no longer exists in your source**, they are looking at a
cached page or a stale query param in the address bar, not your code. Grep the
source for the literal text before debugging anything:

```bash
grep -rn "the exact error text the user pasted" src/ || echo "STALE — string is gone from source"
```

Order of operations when a fix "didn't work": (1) is the string still in source,
(2) is my new code running, (3) only then debug the logic.

## Single-file HTML artifacts — the bar is HIGHER, not lower

Explainers, decks, and reports delivered as one self-contained `.html` have no
build step, no type checker, and no tests. There is nothing to catch a typo'd
icon class or a miscounted grid row, so **the screenshot is not the last mile,
it is the only line of defence** — and a hash-routed page hides defects in the
tabs you skipped, so screenshot EVERY view.

- **`references/js-parse-check-before-visual-qa.md`** — parse-check inline
  `<script>` with `new Function()` BEFORE screenshotting. One syntax error means
  nothing runs, yet the page still serves 200 showing its static skeleton — and
  tag-balance, DOM-id audits and HTTP status all pass on a completely dead page.
  Includes the in-page bisect to find the offending line and the
  `${...}`-leaked-into-static-markup sibling bug.
- **`references/single-file-html-artifact-verification.md`**
headless loop (`--headless=new` + `--virtual-time-budget` so Alpine hydrates
before capture) and the silent-defect catalogue: icon-font prefix mismatches
that render as invisible glyphs with no console error, unscoped `sed` prefix
renames that also break the CDN `<link>`, `grid-template-rows` with fewer
entries than children producing a huge empty void, and ASCII/tree blocks needing
`white-space: pre`.

**`browser_navigate` will NOT reach your local server** — it blocks private and
internal addresses, so `http://127.0.0.1:PORT/...` returns
`"Blocked: URL targets a private or internal address"`. `computer_use` with
`app='screen'` also fails (cua-driver captures one window at a time, no desktop
surface). The working path for a static single-file artifact is headless Chrome
straight at the file's localhost URL:

```bash
# serve (terminal background=true — a bare '&' is rejected)
cd <dir> && python3 -m http.server 8931

# then, foreground, tall window so the whole one-pager lands in one shot
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --window-size=1440,2600 --hide-scrollbars \
  --screenshot=/tmp/x.png "http://127.0.0.1:8931/<file>.html"
vision_analyze(image_url="/tmp/x.png", question="layout, overlap, all sections visible?")
```

Ignore the `Trying to load the allocator multiple times` stderr line — the
screenshot still writes; check the reported byte count instead.

### Screenshotting via an already-attached Chrome (no headless launch)

When Chrome is already running with `--remote-debugging-port` (check:
`curl -s http://127.0.0.1:9222/json/version`), you can capture a file the user
just opened, without launching a second browser or fighting `browser_navigate`'s
private-address block. `open <file>.html` then find the tab and shoot it:

```
# 1. find the tab id (Target.getTargets, or the /json/list endpoint)
# 2. constrain the viewport FIRST — this is what keeps the payload small
browser_cdp(method="Emulation.setDeviceMetricsOverride", target_id=<id>,
            params={"width":1100,"height":1500,"deviceScaleFactor":1,"mobile":False})
browser_cdp(method="Page.captureScreenshot", target_id=<id>,
            params={"format":"jpeg","quality":55})
```

**A large CDP result gets persisted to a temp file and TRUNCATED**, which cuts
the base64 mid-string. Decoding then fails with
`binascii.Error: Invalid base64-encoded string: number of data characters ...
cannot be 1 more than a multiple of 4`. Do not conclude the capture failed —
extract with a regex, trim to a multiple of 4, and verify the JPEG EOI marker:

```python
b64 = re.search(r'"data":\s*"([A-Za-z0-9+/=]+)', open(path).read()).group(1)
b64 = b64[: len(b64) - (len(b64) % 4)]
img = base64.b64decode(b64)
assert img[-2:] == b"\xff\xd9", "truncated before end of image"
```

Prevention beats repair: `format=jpeg` + `quality≈55` + `deviceScaleFactor=1` at
~1100px wide lands around 85 KB, well inside the limit. PNG at
`deviceScaleFactor=2` with `captureBeyondViewport=True` produced 414 KB and was
truncated every time.

**`captureBeyondViewport` is a trap for tall documents.** Without it you capture
only the current scroll position — and if the user (or `open`) left the page
scrolled, you screenshot the middle of the document and can easily review a
report's footer while believing you saw its header. Either set it and pay the
size cost, or scroll to top first — and if you only saw part of the page, **say
which part** rather than implying you reviewed the whole thing.

### When capture tooling itself dies: measure pixels instead of photographing them

Screenshot stacks degrade. Verified 2026-08-19: headless Chrome began hanging
past 180s mid-session, then Playwright did too, on a machine where both had
worked minutes earlier — while the app itself answered `200` throughout. Two
delegated verification passes burned ~450s and returned nothing.

**Do not keep re-dispatching a hung capture.** For a threshold question — *does
A clear B*, *is anything drawn left of X* — a pixel scan over CDP against the
already-open browser is faster, cheaper, and strictly more precise than a
screenshot plus a vision opinion:

```js
// Does the leftmost drawn node clear the floating legend panel?
const cv  = document.querySelectorAll('canvas')[2];      // see layer trap below
const r   = cv.getBoundingClientRect();
const sx  = cv.width / r.width;                          // device pixel ratio
const ctx = cv.getContext('2d');
const legendRight = Math.round((LEGEND_RIGHT_CSS_PX - r.left) * sx);
let firstInk = null;
for (let x = 0; x < cv.width; x += 2) {
  const d = ctx.getImageData(x, top, 1, bot - top).data;
  for (let i = 0; i < d.length; i += 4)
    if (d[i+3] > 40 && (d[i] > 50 || d[i+1] > 50 || d[i+2] > 50)) { firstInk = x; break; }
  if (firstInk !== null) break;
}
return { clearsLegend: firstInk > legendRight,
         gapCssPx: Math.round((firstInk - legendRight) / sx) };
// -> {"clearsLegend": true, "gapCssPx": 171}
```

Scan whole columns for ink to count content bands and prove nothing ran off the
edge (`lastInkPx < canvasW - 20`) — that distinguishes *clipped* from *overlapping*,
which a screenshot reviewer routinely conflates.

🚨 **Canvas libraries stack MULTIPLE canvases, and the top one is usually empty.**
Cytoscape renders `layer0-selectbox`, `layer1-drag`, `layer2-node` — all the same
size, all at the same coordinates. `document.querySelector('canvas')` returns
layer0, which has no nodes on it, so the probe returns `firstInk: null` —
**indistinguishable from "the graph is empty"**. Enumerate first
(`[...document.querySelectorAll('canvas')].map(c => c.className)`) and target the
node layer by index. Getting this wrong sends you off "fixing" a non-existent
empty-canvas bug.

Two supporting notes: `canvas.className` on these elements is not a plain string
in every engine, so index rather than filter on it; and locate floating overlays
by geometry + class fragment (`w-[186px]`, `absolute left-3 top-3`) rather than
by text — a collapsible legend keeps its label inside a button and a naive
`textContent` match returns `NOT_FOUND`.

## When you GENERATE the HTML: the generator is a second failure surface

Rendering markdown/data to a self-contained HTML artifact adds defect classes that
neither the source nor the screenshot alone will show — the source is fine, the
renderer mangles it, and the output looks plausible enough to ship.

**A backtick inside CSS terminates the JS template literal the stylesheet lives
in.** Proven 2026-08-12: a CSS comment written as ``/* a `---` before an h2 ... */``
inside a `const html = \`...\`` template made the whole script fail with
`SyntaxError: Invalid left-hand side expression in postfix operation` pointing at
the template's opening line — nowhere near the comment. The first fix attempt
blamed a `+` in an adjacent-sibling selector and changed the wrong thing. Run
`node -c <script>` after any edit to embedded CSS, and never put a backtick in a
stylesheet that lives inside a template literal (say so in a comment, so the next
editor doesn't reintroduce it).

🚨 **This recurred 2026-08-28 despite being written down here** — while *fixing* that
same renderer, a new CSS comment quoting a property name in backticks killed the script
again. Knowing the rule did not prevent it, because the backtick arrived as ordinary
markdown-style emphasis inside prose, not as code.

The durable defence is mechanical, not attentional:

- **Put the warning IN the stylesheet**, at the top, as a comment the next editor
  cannot miss. A rule that lives only in a skill file is not in front of the person
  editing line 287.
- **`node -c <script>` after every edit to embedded CSS**, without exception. It is
  instant and it is the only thing that actually caught this — both times.
- **Write property names in CSS comments bare** (`a nowrap on a wide column`), never
  fenced. Reserve backticks for markdown, and treat any template-literal file as a
  backtick-free zone for prose.

**Emphasis regexes eat characters inside code spans.** `*` in a path
(`engagements/*/log/*.md`) is consumed by an `<em>` rule and renders as
`engagements//log/.md` — a *wrong file path* in a shipped document, with no error
anywhere. Extract code spans to placeholders BEFORE applying emphasis, then
restore them.

**A naive list parser truncates every wrapped bullet.** Matching only lines that
start with `- ` emits a half-sentence `<li>` plus a stray unindented `<p>` for the
continuation. Every real multi-line bullet is corrupted. Consume continuation
lines until the next list item, table, heading, rule, or blank.

**`white-space:nowrap` on a prose column CLIPS the text — it does not scroll it.**
Verified 2026-08-28: `td:nth-child(4){white-space:nowrap}` in a report renderer forced
every long line in a table's prose column onto one line, overflowed the fixed-width
sheet, and silently truncated the end of all 17 rows. The table renders, the rows are
all there, the sentences just stop. In a document whose entire integrity claim is
*nothing was dropped*, that is the worst possible defect class — and the user, not the
verification pass, is who noticed.

🚨 **The obvious fix — `table-layout:fixed` + explicit column widths — is ALSO wrong, and
it fails worse.** Tried 2026-08-28 and it moved the `nowrap` from column 4 to column 2,
which made a long figure in a *different* table on the same page render **directly on top
of** the column beside it. Clipping became overlap: text printed over text.

The root error is deeper than any single rule. **Wrapping keyed off column POSITION
(`td:nth-child(N)`) cannot be right, because position does not predict content.** In one
generated report: the source list's prose sat in column 4, the Evidence table's long figure
in column 2, and the Risk table's prose in column 3. Any `nth-child` rule is correct for one
table and wrong for the others — and a hard-coded width assumes every table has the same
shape, starving the prose column of every table that differs.

**Correct model: wrap by DEFAULT, opt IN to `nowrap` per cell, decided from the cell's own
content at render time.**

```js
const cls = s => {
  const t = s.replace(/[*_`]/g, '').trim();
  if (/^\d{4}-\d{2}-\d{2}$/.test(t)) return ' class="slug"';   // date
  if (t === '' || t === '—') return ' class="nw"';             // empty marker
  if (t.length <= 22 && !/\s/.test(t)) return ' class="slug"';  // single token
  if (t.length <= 22) return ' class="nw"';                     // short label
  return '';                                                    // prose → wraps
};
```

```css
td { white-space: normal; overflow-wrap: anywhere; }   /* default */
td.nw, td.slug { white-space: nowrap; }                /* opt-in */
@media (max-width: 800px) { td.nw, td.slug { white-space: normal; } }
```

**Sweep the responsive blocks for surviving positional rules.** The mobile breakpoint kept
its own `td:first-child,td:nth-child(2),td:nth-child(3){white-space:normal}` after the
desktop fix landed — same bug, dormant until someone opened it narrow.
`grep -n 'nth-child' <renderer>` and confirm every remaining hit is a comment.

**🚨 A page-level overflow check will certify a clipped table as clean.** The wrapper's
`overflow:hidden` contains the damage, so `documentElement.scrollWidth - clientWidth`
returns **0** while three columns are unreadable. Same failure family as
`scrollWidth > clientWidth` missing flex overlap: the metric cannot express the defect.
Probe **per cell, across every table** — `scripts/measure-table-clipping.js` returns a
PASS/FAIL verdict plus `clippedCells`, `maxOverflowPx`, and `overlaps` per table.

**And clipping is only half of it: `scrollWidth - clientWidth` returns 0 for OVERLAP,**
because text painted over the next column is not overflowing its own box. Overlap needs a
pairwise comparison of adjacent cell rects. The script does both — assert
`clippedCells === 0` **and** `overlaps === 0`. An earlier version of that script checked
only clipping and returned PASS over a table that was visibly printing text on text; the
user found it in a screenshot after the probe said clean.

**Then look anyway.** The numbers localize the defect; the eyes confirm the fix reads
right. Both directions of this session's bug were found by a human looking at a page that
measured clean under the metric being used at the time.

**Fixing the table the user screenshotted does not fix the others.** Same session: after
patching the reported table, the probe found **two more still broken** — one clipping at
427px, one rendering 1460px wide inside a 930px wrapper. The user's screenshot is a
sample, never the population. After any table/layout fix, re-measure **all** instances
and assert the verdict across the set, exactly as with the spacing-uniformity rule above.

🚨 **This recurred in the SAME session, twice, and the user had to say "bugs exist in
other tables" before it was done properly.** The pattern is worth naming because it is
seductive: the user reports a defect on one instance, you fix that instance, you verify
that instance, and you report success. Each step is locally reasonable and the whole is
wrong — the second round of feedback arrived because the "fix" had introduced a *new*
defect class (overlap) on tables the user had not screenshotted.

**When a user reports a rendering defect, treat the report as a sample from a class:**

1. **Classify before fixing.** Ask what *kind* of thing broke (a wrapping rule, a spacing
   token, a colour), then enumerate every element of that class in the document —
   `document.querySelectorAll('table').length` — before touching anything.
2. **Fix at the level of the class**, not the instance. A rule that names a position, an
   index, or one element's shape will be wrong for the siblings by construction.
3. **Assert the verdict across the whole set**, and report the denominator: "4 tables, 0
   clipped, 0 overlaps" — never "the table is fixed".
4. **Re-probe after the fix for the defect you may have just created.** A layout change
   that resolves one failure mode routinely opens another, and the probe you wrote for
   the first mode is usually blind to the second.

Same shape as "a spacing fix is verified by uniformity across the document", and as the
subagent n-of-N rule: a verdict without a population is not a result.

**A class the CSS depends on must be confirmed to have been EMITTED.** The fix keyed off
a `.wide` class gated on `head.length >= 4`; one qualifying table never received it and
kept overflowing. `grep -c 'class="wide"' out.html` and compare to the number of tables
you expected to tag — a stylesheet rule for a class nothing emits is silently inert.

**Verify the parse with greps, not by reading the source.** Cheap and specific:

```bash
grep -c 'class="bt"' out.html          # expect N beats
grep -o '<code>[^<]*</code>' out.html  # asterisks/paths intact?
python3 -c "...re.findall(r'<li>(.*?)</li>'...)"   # bullets complete, no stray <p>
```

### A verification script that matches NOTHING reports green

The most dangerous audit output is a clean one produced by a regex that found no
input. `UNMAPPED: none` and `MISSING: none` are printed identically whether you
checked 48 items or zero.

Verified 2026-08-26: an icon-coverage audit printed

```
symbols: 52 · foods: 0 · UNMAPPED ->generic: none · MAPPED TO MISSING SYMBOL: none
```

Three of those four lines are a pass. `foods: 0` is the only honest number in it
— the food-name regex had matched nothing, so both "none" verdicts were vacuous.
Had `foods` not been printed, the audit would have certified a mapping it never
looked at.

Rules:

- **Always print the denominator, and assert it is non-zero.** `assert len(names)
  > 0` turns a vacuous pass into a hard failure. Same shape as the four-bucket
  rule and the subagent n-of-N rule: a verdict without a population is not a
  result.
- **Cross-check two independently-derived counts.** `mapped entries: 48` /
  `distinct foods: 48` is evidence; either number alone is not.
- **A zero from a failed extraction is indistinguishable from a real zero** —
  the same trap as the empty-`$P` `grep -c` case in Pitfalls. Print the
  intermediate.

### A regex rewrite can silently DELETE the data it was editing

`re.sub` with `.*?` and `re.S` spans newlines, so a pattern meant to rewrite one
line will happily consume everything up to the next match — including unrelated
blocks below it.

Same session: `re.sub(r'window\.ICON = .*?;', ...)` with `re.S` was intended to
replace a one-line arrow function. The nearest following `;` was inside a data
structure far below, so the substitution **ate the entire `KIDS` object** — both
users' complete datasets — and left syntactically valid JavaScript. `node -e` on
the file did not complain; the loss only surfaced because the next audit crashed
on a missing key.

- **Anchor line-oriented edits to lines**: `flags=re.M` with `^...$`, never
  `re.S` with `.*?`.
- **Assert the edit did something AND that bystanders survived**, before writing:

  ```python
  s2 = re.sub(r'^window\.ICON = .*$', NEW, s, count=1, flags=re.M)
  assert s2 != s, "pattern did not match — edit silently no-op'd"
  assert 'window.KIDS' in s2, "KIDS block was destroyed!"
  assert s2.count('breakfast:') == 2, "kid blocks damaged"
  ```

- **`git checkout <file>` is the cheap recovery** — which is an argument for
  committing before any scripted bulk edit, not after.
- Scripted source edits are the intended tool here (see Pitfalls on heredocs),
  but they are unreviewed by construction. The assertions *are* the review.

### Fixing a spacing defect can create a NEW inconsistency — measure every instance

Same session: section gaps were ~90px where a thematic break preceded a heading
(the rule *and* the heading's own top border both applied) and 56px elsewhere.
The fix set the collapsed case to 34px — which removed the 90px outlier and
introduced a 34-vs-56 split across the same document. It looked fine in a
screenshot.

```js
// Measure ALL instances of the thing you "fixed", not the one you were looking at.
[...document.querySelectorAll('h2')].map(h => {
  let p = h.previousElementSibling;
  while (p && getComputedStyle(p).display === 'none') p = p.previousElementSibling;
  return p ? Math.round(h.getBoundingClientRect().top - p.getBoundingClientRect().bottom) : null;
}).filter(x => x !== null);
// assert new Set(gaps).size === 1
```

Skip hidden siblings when walking backwards, or a `display:none` rule makes the
measurement meaningless. General rule: **a spacing fix is verified by uniformity
across the document, not by the one gap you were staring at.**

### Same trap in the label/value split of a two-column text layout

`display:inline-block; min-width:82px` on a lead label works for `SITUATION` and
breaks for `STRATEGIC RELEVANCE` — the long label overflows its box and collides
with the prose while short labels leave a gap. Use
`display:grid; grid-template-columns:<fixed> 1fr` and wrap the value in its own
element, then assert every row's text starts at the same x:

```js
[...document.querySelectorAll('p.beat')].map(p => ({
  label: p.querySelector('.lead').innerText,
  textLeft: Math.round(p.querySelector('.bt').getBoundingClientRect().left),
}));   // every textLeft must be identical
```

### Emoji in body prose is a design defect in a document artifact

⚠️/🔴 render as full-color glyphs that break the typographic tone of an otherwise
restrained document and read as unintentional. Convert them in the renderer to
small styled tags (`<span class="unq">unquantified</span>`) or colored dots. This
is not pedantry — it is the difference between "generated" and "designed" to the
executive receiving it.

### Emoji used deliberately AS icons: ground them in the Unicode registry

Different case from the above — when emoji *are* the icon set (a kids' app, a
compact list, anywhere you want zero icon-font weight), picking from memory ships
two silent defects: a glyph depicting the wrong object, and tofu boxes ☐ on
devices whose font predates the emoji. Grep `unicode.org`'s `emoji-test.txt` for
candidates by name, pick on **shape** rather than category, and cap the
**E-version** (E14.0 is the safe default for consumer/school hardware). Verified
2026-08-26: `🥨 pretzel` for Bissli was wrong by category-matching — it is a fried
stick snack, so `🍟` (E0.6) is right. **And know when to stop:** branded/regional
items (Pringles, Bissli, Cheerios-vs-CTC) have no emoji at all, and further glyph
swaps only buy a less-wrong icon. That is the signal to hand-author an SVG
`<symbol>` sprite instead — OpenMoji is CC BY-SA (viral) and Twemoji is still
emoji-shaped, so neither solves it. Full method, version table, the
`\u{...}`-with-provenance-comment convention, the sprite recipe, and the
mapping-coverage audit: `references/emoji-icon-selection.md`.

### Print output is a SECOND layout your screenshots never saw

`@media print` rules are invisible to every screen capture, so a page verified
pixel-perfect can still print as five ragged pages. If the user asked for
"fits on one page", that is a falsifiable numeric claim — generate a real PDF and
count `/Type /Page` objects, then render page 1 and look at it. Build a dedicated
hidden print section rather than scaling the app down, and hook `onbeforeprint`
so Cmd-P works, not just your button. Recipe, density levers, and the
`id="print"`-shadows-`window.print()` trap:
`references/print-stylesheet-verification.md`.

### "Something opened on the right side of the page"

When the user reports an unexpected panel, check whether it is *outside the page's
own scrollbar*. If the page scrollbar sits to its left and the artifact defines no
such surface, it is browser chrome (a side panel / extension), not your output.
Confirm by asking them to open the file in a private window with extensions
disabled — do not start debugging CSS you never wrote.

## Authenticated surfaces: verify auth state BEFORE judging pixels

A settings or dashboard route can render its full shell while its data requests
return `401`. The screenshot then looks structurally real but contains fallback
values such as `0 users`, blank fields, or `toolchain missing`. Vision will
confidently critique those values even though they are not the signed-in product
state.

**Preflight every authenticated screenshot:**

1. Read `location.href` and the visible identity/nav state.
2. Call the app's own session endpoint (`/api/me`, `/api/session`, etc.) from page
   context and assert the signed-in flag. Do not infer auth because the route
   rendered.
3. Confirm the key data endpoint returns `200` and a non-placeholder payload.
4. Only then capture pixels and ask vision to evaluate them.

If an attached browser has a previously-authorized account but an expired app
session, starting the app's normal login route may return directly through the
callback without a consent prompt. It is safe to probe that route. **Stop if a
consent screen appears; never press Authorize merely to satisfy QA.** After the
callback, repeat the session and data preflight before screenshotting.

A useful failure signature: the nav says `Sign in` while a protected route such
as `/settings` is visible, and API-derived fields all read blank/missing. Treat
that screenshot as an unauthenticated-shell check only, not evidence about the
real settings state.

For the attached-Chrome CDP script, session/data assertion expression, and
consent-stop logic, see `references/authenticated-live-qa.md`.

## Authenticated surfaces: the consent wall is a legitimate STOP

Some UI cannot be reached without signing a real user into a real third-party
account. When local verification bounces `/` → `/signin` → the provider's login
→ an **OAuth consent screen already logged in as the user's live account**,
clicking *Authorize* grants durable scopes on that account (in yoto-dash, Aug
2026: "View, upload and edit your custom icons" on itay85@gmail.com).

**Do not click it.** Close the tab, report the surface as UNVERIFIED, and offer
the user two explicit paths: (a) they authorize and you screenshot + ship, or
(b) ship on green gates with the visual check deferred. Silently authorizing to
finish your own checklist is the wrong trade — the honest four-bucket report
(see "The core rule") exists for exactly this.

Cheap pre-check before you build a whole verification plan: `curl` an
authenticated API route. `401` means every visual path is gated and you will hit
consent.

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:PORT/api/<gated-route>  # 401 = consent wall ahead
```

### Reaching localhost when browser_navigate refuses

`browser_navigate` blocks private addresses, and so does CDP `Page.navigate`.
`Target.createTarget` with a localhost URL is **not** blocked, so an attached
Chrome (`curl -s http://127.0.0.1:9222/json/version` to confirm) can open the
page and `Runtime.evaluate` can read it:

```
browser_cdp(method="Target.createTarget", params={"url":"http://127.0.0.1:3737/"})
browser_cdp(method="Runtime.evaluate", target_id=<id>, params={
  "expression":"JSON.stringify({url:location.href,text:document.body.innerText.slice(0,600)})",
  "returnByValue":true})
browser_cdp(method="Target.closeTarget", params={"targetId":<id>})
```

Read `location.href` after any in-page click — that is how you discover you were
redirected to a provider consent screen instead of the view you wanted. Headless
Chrome `--screenshot` (above) remains the path for pixels; this is the path for
*where am I and what does it say*.

### Verifying a component behind an auth wall, without authorizing

When every route redirects to sign-in, you can still verify **CSS and layout**
honestly: load any page that ships the real stylesheet (`/signin` will do),
replace the body with markup that mirrors the component's rendered DOM, and
measure or screenshot that. You are testing the real cascade at a real viewport
— only the data is synthetic.

```python
# CDP over websocket; note suppress_origin=True or Chrome answers 403:
# "Rejected an incoming WebSocket connection from the ... origin"
ws = create_connection(target["webSocketDebuggerUrl"], timeout=30, suppress_origin=True)
send("Emulation.setDeviceMetricsOverride",
     {"width": 320, "height": 568, "deviceScaleFactor": 3, "mobile": True})
send("Page.navigate", {"url": "http://127.0.0.1:PORT/signin"})   # loads real globals.css
send("Runtime.evaluate", {"expression":
     "document.body.innerHTML='';var d=document.createElement('div');"
     "d.className='app';d.innerHTML=" + json.dumps(MARKUP) + ";document.body.appendChild(d)"})
send("Page.captureScreenshot", {"format": "png", "clip": {...}})  # -> base64, write to disk
```

Honesty boundaries — state these when reporting:

- This verifies **the stylesheet**, not the component's own JSX. Keep the
  injected markup byte-identical to what the component emits, or you have
  verified a fiction. If the component's classes change, this check goes stale
  silently.
- It cannot verify data binding, handlers, or the crop/upload round-trip.
- Report it as "verified locally against the real stylesheet", never as
  "verified in the app".

Cheap trap: a component hidden on the very route you picked (navs commonly
`return null` on `/signin`) will screenshot as a blank or as unrelated page
decoration. Assert the element exists before capturing —
`!!document.querySelector('.sidebar')` — or you will confidently analyze a
decorative blob.

## A REJECTED command runs NOTHING — including the setup steps bundled with it

Tool-policy rejections are not partial failures. When the terminal tool refuses a
command (bare `&` backgrounding, blocked heredoc, disallowed pattern), **no part
of that compound command executed** — including the innocuous `chmod`, `mkdir`,
or `cp` you chained ahead of the offending piece. The prerequisite is silently
missing, and the failure surfaces later somewhere unrelated.

Worked case (lgw exhibition site, Aug 2026):

```bash
# REJECTED for the trailing '&' — so chmod never ran either
chmod +x site/serve.sh && cd site && ./serve.sh > /tmp/serve.log 2>&1 &
```

Re-issued correctly as `terminal(background=true)`, the launch failed with
`zsh:1: permission denied: ./serve.sh`. Two cycles were spent suspecting the
script, the shebang, and the path — the actual cause was that the `chmod` had
been swallowed by the earlier rejection.

Rules:

- **Re-run the setup half separately after any rejection.** Do not assume the
  prefix of a rejected compound command took effect.
- **Read the background process's own log on failure** (`process(action='log')`).
  `permission denied` / `command not found` there means a prerequisite step is
  missing, not that the artifact is wrong.
- **Keep `chmod`/`mkdir` in their own call** when the next step is a policy-
  sensitive launch, so a rejection can never take them down with it.

## Generated vector geometry needs eyes — a plausible path can render wrong

Hand-authored SVG (logos, marks, diagram armatures) has no compiler, no test,
and no console error when the math is wrong. It renders *something*, and that
something is often confidently incorrect.

Worked case: a lemniscate (figure-eight) drawn as an inline `<path>` for a site's
threshold mark. The `d` attribute parsed fine, animated fine, and produced **two
tangent ovals that never crossed** — the control points looped back before
reaching the origin. Nothing failed; it just wasn't the figure. One screenshot
plus a falsifiable question ("does this render as a clean crossing figure-eight?")
caught it immediately.

- **Ask about the SHAPE, not the presence.** "Is the SVG visible" passes on a
  broken curve. "Do the two lobes cross at a single center point" does not.
- **Any symbol carrying meaning is a correctness surface**, not decoration. If
  the mark is load-bearing for the concept (an infinity loop, a specific
  topology, a brand glyph), verify it like a feature.
- Re-screenshot after the fix. A geometry patch is unverified until seen.

#### A silhouette can be a VALID drawing of the WRONG object

Harder than the broken-curve case, because nothing looks defective. Verified
2026-08-21 (newcars2026): five hand-authored car side-profiles — Model Y,
Model Y L, Santa Fe, Tucson, Palisade — were written as single `<path>` blobs
with the window glass drawn *inside* the body outline. Every one parsed, every
one rendered a clean recognisable car, and **all five rendered the same low
sedan/wagon**. The user asked for the SVGs specifically so they "could see
exactly what it is about"; three-row SUVs reading as sedans defeated the entire
purpose, and the deck of cards otherwise looked polished.

The structural cause is worth knowing, because it produces this every time:
composing a car as one merged silhouette makes the greenhouse a *hole in* the
body, which caps roof height at the body's own top edge. Draw the cabin as a
**separate element sitting on top of the body**, and the proportion becomes an
explicit, tunable number instead of an accident:

```jsx
{/* cabin FIRST, above the beltline — this is what makes an SUV an SUV */}
<path d="M44 44 L52 16 C53 13 56 12 59 12 L156 12 ... Z" fill={tone} />
<path d="M53 41 L59 19 ... Z" fill={GLASS} opacity="0.75" />   {/* glass inset */}
{/* body SECOND, from the beltline down */}
<path d="M12 68 ... L44 44 L168 44 ... Z" fill={tone} />
```

Rules:

- **Ask a COMPARATIVE, falsifiable question**, not a per-item one. "Does this
  look like a car?" passes on all five. **"Do the SUVs read as taller and boxier
  than the fastback, and is the largest visibly the largest?"** fails
  immediately. Whenever you generate a *set* of related shapes, the defect is
  usually in the relationships, so the question must be about the set.
- **Name the distinguishing feature per item before drawing**, then verify each
  one is present: fastback = roof slopes into the tail; long-wheelbase = flat
  roof + an extra window pillar; SUV = upright screen, flat high roof, squared
  tail, bigger wheels. Without that list you have no pass criteria and will
  accept anything car-shaped.
- **Ratios are the pass criteria.** Roof height, wheel radius and body length
  relative to the viewbox are what encode "SUV". Fix them numerically rather
  than nudging bezier control points and re-looking.

#### Screenshot BEFORE you deploy, not after

Same session, and the ordering error that made the above worse: the build was
clean, all routes returned `200`, `grep` confirmed all five `aria-label`s were
present in the HTML — so it was deployed, *then* screenshotted. The screenshot
is what revealed every SUV was a sedan, and by then the defect was live on the
URL handed to the user.

Every gate that passed was a **presence** check. `aria-label="Hyundai Palisade"`
being in the markup proves an SVG named Palisade shipped; it says nothing about
whether it is shaped like one. This is the §"green gates certify SHAPE, not
correctness" rule applied to your own greps: *presence of an element is not
correctness of that element*, and a `grep -c` over rendered HTML is the weakest
possible evidence about anything visual.

**Order of operations for any generated visual asset:** build → serve locally →
screenshot → vision with a comparative question → fix → re-screenshot → *then*
deploy. Deploying on green gates and verifying afterwards converts a private
defect into a public one for zero saved time.

#### 🚨 The INVERSE trap: a grep MISS is not evidence of a bug

The section above says a grep *hit* does not prove correctness. The mirror image
is more damaging and fired **twice in one session, the second time in a message
already sent to the user**:

```
curl https://site/page | grep '51%'     ->  0 matches
the actual rendered page                ->  displays "51%" perfectly
```

Component frameworks split `{value}` and its adjacent literal into separate text
nodes with hydration markers between them, so a value that renders correctly is
genuinely absent from the HTML as a contiguous string. Formatting helpers do the
same thing: `money(679.61)` renders `$680`, so grepping `679.61` returns nothing
on a page that is working exactly as intended.

Both false alarms this session had identical shape — a number was computed and
rendered correctly, a grep missed it, and the user was told a feature was broken.
The second one shipped before a screenshot disproved it.

**The rule, unconditionally:**

- **A grep MISS is a null result.** It is not evidence of anything.
- A grep HIT is weak positive evidence — fine for "did the deploy land", useless
  for "is it correct" (see the section above).
- **Before telling anyone a UI element is missing, broken, or blank, LOOK at it**
  — screenshot, or read `document.body.innerText` over CDP. Rendered text is the
  only authority on rendered text.
- If a grep miss makes you *suspect* a defect, that is a reason to open a
  screenshot, never a reason to write the words "there is a bug".

The cost asymmetry is what makes this hard rather than advisory: a wasted
screenshot costs one tool call, while a false bug report burns user trust and
sends them hunting for a defect that does not exist. This is the same
measure-before-you-claim discipline as the viewport-emulation trap above, applied
to your own greps instead of a vision report.

#### Stale persisted client state masks a corrected default

When a page seeds itself from `localStorage`/`sessionStorage`/IndexedDB, fixing a
default in the source does **not** change what a returning visitor sees. The code
is right, the build is clean, the deploy landed — and the page still renders the
old wrong numbers, because saved state wins on mount.

Verified 2026-08-26: a corrected preset was verified over CDP and came back with
a field reading `$0`. The value was correct in source and correct in the bundle;
a `v1` saved view was overriding it. A full verification cycle was spent on a
non-existent bug before bumping the storage key resolved it instantly.

- **Bump the storage key version whenever seeded defaults change** (`app.calc.v1`
  → `v2`). This is part of the fix, not cleanup afterwards.
- **Verify in a fresh profile or incognito**, or clear the key first — otherwise
  you are testing your own stale session, not the deploy.
- **Tell: the rendered value matches a PREVIOUS version of your code.** That is
  persisted state, not a rendering bug. Do not go debugging the component.

## Sticky elements: a layout that measures clean can still LOOK broken

Two distinct failure modes, and the DOM only reports one of them.

**Overlap that only exists while scrolling.** A `position: sticky` label sitting
in the same grid area as later content will pass a static bounds check — measure
`label.bottom` vs `nextSection.top` at scroll 0 and they do not intersect — while
visibly bleeding over that content mid-scroll, because the element's painted
position moves and its background is transparent. Fixes: give the sticky element
an **opaque background** matching the page surface, and assign explicit
`grid-row` / `grid-column` so it cannot share a track with what follows.

**Implicit grid placement silently stacks siblings.** Appending an element to a
two-column grid whose rows were never declared lets it flow into an occupied
area. Declare the rows and pin each child:

```css
.work { display: grid; grid-template-columns: minmax(0,1fr) 26rem;
        grid-template-rows: auto auto; }
.work__stage { grid-row: 1; grid-column: 1; }
.label       { grid-row: 1; grid-column: 2; }
.passage     { grid-row: 2; }
.index       { grid-row: 3; }
```

…and remember to **reset those assignments in the single-column media query**
(`grid-column: 1; grid-row: auto;`), or the mobile layout inherits desktop
placement and overlaps.

**An inline label + value pair needs a block label when the value can wrap.**
`<span class="k">TESTED</span>{value}` renders as `TESTEDWhat does the surface…`
with no space. Make the key `display: block` rather than hoping for a margin.

## Inline `style` beats every stylesheet — check it before debugging CSS

A media query that "doesn't apply" is often not a specificity or breakpoint
problem at all. An inline `style` attribute wins over any selector short of
`!important`, so a rule can be correct, shipped, and inert.

Worked case: a brand icon stayed misaligned on mobile no matter what the
`@media` block said, because the component rendered
`style={{ width: 32, height: 32 }}`. The mobile rule shrinking it never had a
chance. The fix is to move sizing into a class the media query can override —
not to escalate with `!important`, which just moves the fight.

```bash
# Before debugging a rule that "isn't applying", look for the inline style:
grep -n 'style={{' src/components/<Component>.tsx
```

Tell: computed style disagrees with your rule AND the element has a `style`
attribute in the DOM. `getComputedStyle(el).width` vs what the sheet says is the
one-line confirmation.

Corollary — **`!important` in a media query is a smell.** If you find yourself
adding it to beat your own markup, the sizing belongs in a class instead.

## A post-processed artifact is a DIFFERENT program — re-verify it

Any step that rewrites your build output after it is built — a minifier, a
scrubber that strips private code paths before publishing, a codemod over
`dist/`, an asset-root rewrite — produces bytes that were never verified. The
pre-transform verification does not carry, no matter how thorough it was.

Worked case (lgw public deploy, Aug 2026): a scrubber collapsed dual-mode
ternaries and removed internal fields from the deployed copy. Every route had
been screenshotted and console-checked *before* the scrub and was clean. After
the scrub, one route threw:

```
Uncaught TypeError: Cannot read properties of undefined (reading 'find')
  at work.html
```

The scrubber had removed a manifest key that page still read
(`data.inquiries.find(...)`). Nothing in the build reported it; the page rendered
its shell and died silently on one panel.

Rules:

- **Re-run the full route + console sweep against the transformed output**, from
  its own server, not the source tree. Treat `dist/` as an unverified build.
- **Fix defensively in the SOURCE** (`(data.inquiries || []).find(...)`) so both
  the pre- and post-transform programs are correct. Patching only the output
  means the next build reintroduces the break.
- **A transform that can delete data can delete content.** If the step has a
  denylist, read every hit before suppressing it — a token like `"not published"`
  will happily censor legitimate prose (*"the artist has not published a key"*).
  Scope patterns to the exact string you mean.
- **Make the transform fail loudly.** End it with an assertion that exits
  non-zero (leak gate, required-symbol check) rather than trusting it silently
  did the right thing. In the case above the gate fired four times on real
  defects before passing.

## What only a screenshot catches

Real case: 175/175 tests green, tsc clean, production build clean — and three
ship-blocking defects, none of which any assertion could have caught:

1. **Repetition.** An attention queue rendered the same sentence verbatim six
   times. Ranking, hrefs and timestamps were all individually correct. A wall of
   identical rows teaches nothing and the reader stops. Tests assert
   *correctness*, never *scannability*.
2. **A true statement that was a lie.** A KPI read `Failed (24h) 0` while 24 runs
   sat failed — all older than the window. Technically accurate, and it concealed
   the single most important fact on the page (a 48% failure rate). No test fails
   on a correct number. Prefer a total plus a rate over a window that can render
   a misleading zero.
3. **Build-time config ignoring runtime config.** A `DEMO MODE` badge showed
   despite the runtime env var being `0`, because the Dockerfile `ARG` defaulted
   to `1` and the framework inlines at build time.

Fixing (1) then exposed a design flaw the tests had encoded: the collapse helper
read the clock directly instead of taking an injected `now`, making its output
untestable. **The screenshot found the bug; the bug found the design flaw.**

Corollary: when you fix a display defect, expect to *rewrite tests that were
asserting the old wrong behaviour*. Rewrite the fixtures; do not weaken the code
to keep a bad test green.

## Always verify BOTH themes when a theme toggle exists

This is not cosmetic QA — it catches whole classes of frozen styling.

- A `.light` block that overrides **only surface tokens** leaves `--primary`,
  `--success` and every accent at dark-tuned values. `#0EA5E9` on `#FFF` is
  ~2.9:1 — a WCAG failure completely invisible while you test in dark mode. A
  light theme needs a darkened accent ramp *and* an `--on-primary` that flips.
- **Canvas graph libraries cannot resolve CSS custom properties.** Cytoscape and
  react-flow paint to `<canvas>`, so their stylesheets hard-code hex and stay
  black on a white page. Fix with a hook that reads tokens off the live DOM via
  `getComputedStyle(document.documentElement)`, re-reads on a `MutationObserver`
  watching the theme class on `<html>`/`<body>`, and a graph effect keyed on the
  resolved theme (`[elements, theme]`) so it repaints on switch.

For graph/canvas surfaces generally — asynchronous layout that makes `cy.fit()`
measure stale geometry, stale *container* measurement that sinks a graph to the
bottom of its panel, **viewport nudges that regress when the fixture grows**,
proving a graph has nodes at the data layer before spending a screenshot, and
reading node/edge vocabulary out of the builder rather than a design doc — see
[`references/graph-canvas-surface-verification.md`](references/graph-canvas-surface-verification.md).

**A constant you tuned by eye encodes the data volume you tuned it against.** A
pan offset, a zoom cap, or a fixed `vh` panel height verified good on a sparse
fixture becomes the defect when the data grows — so **re-run the visual pass
whenever the DATA changes, not only when the code changes.** A fixture swap is a
UI change. Worked cases in §9 of that reference.

**Convert contrast complaints into numbers before editing a token.**
`python3 scripts/contrast_ratio.py "#4A5D78" "#0B0F14"` prints the ratio, the
required threshold, and exits non-zero on failure. Reviewers say "subtle" at
2.86:1 and at 4.01:1 for different reasons — one is a real failure under the 3:1
UI-boundary bar, the other is line weight. Measure before you nudge, or you will
ship two rounds of guesses like this session did.

### Repeated identical feedback means the WRONG VARIABLE, not diminishing returns

A visual property has several independent inputs. Colour, weight, opacity, and
radius all read as "the border"; size, spacing, and hierarchy all read as "too
cramped". When you tune one input across several rounds and independent reviews
keep returning the *same word*, you are not approaching the limit of what is
worth fixing — you are refining the input that was never the problem.

Worked case (agentic-sdlc, Aug 2026): three consecutive reviews called a graph
container border "SUBTLE, not crisp". Colour was raised twice, ending at 4.01:1
— comfortably past the 3:1 UI-boundary bar. The fourth review still said SUBTLE
and answered the acceptability question **NO**. At that point it was closed as
"diminishing returns, your call" and handed back to the user.

That was wrong, and the answer was sitting in the reviewer's own sentence: *"a
thin, low-contrast line."* Colour had been measured and fixed; **width had never
been touched.** `border` → `border-2` produced CRISP on all three surfaces in one
round, explicitly not over-corrected.

Rules:

- **Treat a repeated adjective as an unexplored dimension, not noise.** List
  every input that produces that adjective and check which one you have never
  changed.
- **Mine the reviewer's exact wording.** "Thin" is a width report, not an
  intensity report. Independent observers describe the mechanism more precisely
  than the summary verdict does.
- **Do not spend a "your call" on something you have not diagnosed.** Handing a
  decision back is legitimate when the trade-off is genuinely subjective; it is
  rationalization when you simply have not found the cause. Ask which one you are
  doing before deferring.
- **When one dimension is now measured-good, that is evidence to look
  elsewhere** — not evidence the complaint is unreasonable.
- **Force a binary in the verification prompt.** Ask "acceptable: YES or NO" and
  "if NO, name the single change you would make". A free-text review returns
  adjectives you can rationalize; a forced NO plus a named fix ("3px", "brighter
  colour") is unignorable, and its stated mechanism is usually correct.

### Semantic typography: classify by the PRODUCER, not by how the string looks

Rules of the form "monospace = machine-generated, sans = human-authored" (or
colour-by-severity, icon-by-source, badge-by-origin) are semantic. They are
applied correctly only by reading **where the value comes from**, not by
eyeballing the rendered string.

Worked case (agentic-sdlc, Aug 2026): applying the mono rule to graph detail
modals, `{actorKind === "agent" ? "agent" : "human"}` was styled mono — it is
short, lowercase, and looks exactly like an enum. A review flagged that a
sibling view rendered the same concept in sans. The reflex was to make the
sibling mono for consistency; reading the builder proved the opposite:

```ts
// build-lineage.ts — this is an IDENTITY, not a token
role: actor.display_name ?? (actor.kind === "human" ? "Human" : "Agent")
```

It is a **person's name** whenever the ledger has one. Mono would typographically
claim a human was machine-generated the moment it renders `Sarah Chen` — the
exact confusion the rule exists to prevent. The correct fix was to revert the
over-application and split the header so the node-kind taxonomy value stays mono
while the actor beside it does not.

Rules:

- **Trace the field to its producer before styling it.** `grep` the builder for
  the key; an `?? "Fallback"` on a `display_name`/`title`/`label` field means the
  enum-looking string is a *fallback for human content*.
- **An inconsistency flagged by review can be correct in the other direction.**
  Before harmonising two surfaces, decide which one is right — do not assume the
  one you just changed.
- **A fallback that looks like an enum is the trap.** `"agent"`, `"unknown"`,
  `"none"` are frequently placeholders for user-supplied values.
- Same failure shape as tuning colour when the defect was width: pattern-matching
  the symptom instead of reading what the value *is*.

### Vision confirms RENDERING, never TRUTH — grep the source for any factual claim

A screenshot proves an artifact *displays* something. It cannot tell you whether
that something is **true about your own repo**. The vision loop is structurally
blind to this, and it is the defect class most likely to be checked by the
audience.

Worked case (agentic-sdlc demo deck, Aug 2026): a generated slide showed a policy
rule under a caption naming the real bundle path
`standards-bundles/security/v0.1.0/rules.yaml`, as a clean highlighted YAML block:

```yaml
- id: security/v0.1.0/PHI-001
  title: Classify PHI before any write        # invented
  applies_to: ["ledger","prompt","log"]       # invented
  severity: high                              # invented
```

Every field after the id was **fabricated**. The real rule carries
`title: Patient identifiers may not appear in cleartext logs`, `phi_locked: true`,
`blast_class: high`, `enforcement.pipeline_stages`. Two independent vision passes
called the slide OK — correctly, because it rendered perfectly. Anyone opening the
repo would have found different text, in a *governance* demo, in front of a CISO.

**Before shipping any artifact that quotes your own codebase, diff the quote
against the source:**

```bash
grep -oE '<pattern>/v[0-9.]+/[A-Z]+-[0-9]+' artifact.html | sort -u   # what it claims
grep -A6 'id: PHI-001' standards-bundles/security/v0.1.0/rules.yaml   # what is true
```

Rules:

- **A real file path in the caption makes it a quotation — it must be verbatim.**
  Paraphrasing under a real path is worse than inventing freely, because the path
  invites verification. Line-wrapping to fit a slide is fine; renaming fields is not.
- **Check asserted numbers against their generator**, not memory. ("29 nodes / 44
  edges" survived only because it came from a fixture that had been measured.)
- **Generated artifacts are the high-risk surface.** An LLM asked to render a
  config/policy/schema block will produce a *plausible* one, and plausible is
  exactly what survives a screenshot review.
- Applies beyond decks: READMEs, architecture docs, onboarding guides, any artifact
  that quotes a rule id, env var, endpoint, or schema field.

### A subagent that verified a SUBSET may report "no unresolved defects"

Same session: a build-and-verify delegation was asked to screenshot "3-4 slides" of
a 14-slide deck. It checked 4, found them clean, and closed with **"No unresolved
defects."** True of what it inspected; read as a verdict on the whole artifact. A
second pass over the remaining 10 was needed to actually clear it.

- **Read the coverage, not the verdict.** `n` of `N` checked is the finding; "no
  defects" without a denominator is not a pass.
- **Force the denominator in the goal**: "report one line per slide in the form
  `sN — OK | DEFECT: ...`" makes partial coverage impossible to hide. That is why
  the second pass was trustworthy.
- Same shape as the four-bucket rule at the top of this file, applied to a child
  agent's report rather than your own.

### A caption that disagrees with the picture is a correctness defect

Counts, scope lines, and summary chips rendered *beside* a visualisation are
claims about it. When they disagree with what is drawn, the artifact contradicts
itself in the one place a skeptical viewer will check first — and on an
audit/governance surface, where the entire product claim is *what you see is
what the record says*, that is worse than having no caption.

Verified 2026-08-19: a lineage legend read **"5 precedent chains in scope"** over
a canvas drawing **3**. The counter treated every root node as a chain; three of
the six roots had no reuses, so no fan was drawn for them. A reviewer counted the
hubs and caught it in seconds. Fixed by counting roots that actually have an
outbound edge, and surfacing the remainder honestly rather than hiding them:
`"3 precedent chains in scope · 10 nodes · 2 not yet reused"`.

- **Derive the caption from the same predicate the renderer uses.** This is the
  selector/renderer contract (`references/selector-renderer-contract.md`) applied
  to prose instead of a picker.
- **Verify the caption against the canvas, not against the data.** Both can be
  individually correct while disagreeing — the count was a true statement about
  the node list and a false statement about the image.
- **Prefer disclosing the remainder to shrinking the number.** "2 not yet reused"
  is more informative than silently excluding them, and it explains the gap a
  viewer would otherwise notice.

### A measurement proves exactly its own predicate — and nothing adjacent

A numeric check is more trustworthy than a screenshot *for the property it
measures*, and it is silent about everything else. The confidence it produces
leaks: having proven one thing rigorously, it is easy to report the surface as
verified.

Same session, both halves of the trap:

- The pixel probe above returned `clearsLegend: true, gapCssPx: 171` and the view
  was called done. It was — for occlusion. The caption two inches away was
  simultaneously wrong, and the probe had no opinion about it.
- Earlier, `scrollWidth > clientWidth` returned `false` over a bar whose children
  were overlapping (see "Pick a layout metric that can actually fail").

**Before reporting a measured pass, say out loud which predicate you proved and
name one property of that surface you did NOT check.** If you cannot name one,
you have not thought about the surface; if you can, decide whether it is cheap to
check now. A caption you wrote yourself in an earlier turn is the highest-risk
unchecked property — you will not re-read it, because you already believe it.

### A stale or wrong-verdict report can still carry a real observation

Async verification results arrive describing code you have already changed, and
the reflex is to discard the whole message as superseded. Read the *observations*
separately from the *verdict*.

Verified 2026-08-19: a delegated report's headline finding was superseded (it
described a pre-fix build) **and** its diagnosis was wrong — it claimed chains had
been "pushed out of view", when a pixel scan showed content ending 64px before the
canvas edge with nothing clipped. Buried in the same report was the legend/canvas
count mismatch above: a real, current, previously-unnoticed defect.

- **Discard by evidence, not by staleness.** A screenshot taken before your fix
  cannot settle whether the fix worked; it can still show something true about
  the artifact that your fix did not touch.
- **A wrong diagnosis attached to a correct observation is common** from
  reviewers who can see the surface but not the code. Keep the noticing, drop the
  explanation, and go measure the cause yourself.

### A test that asserts the bug will keep the bug alive

When you fix a logic defect, grep the test suite for a case that *encodes* the
old wrong behaviour. Verified 2026-08-18: a run-flow builder bucketed unstaged
rows by a second field, making one axis mean two things — and the existing test
was literally named `"buckets decisions by ambiguity_class when stage is null"`,
asserting the defect as intended behaviour. That is how it survived review, and
why the suite stayed green across the whole broken period.

A fix that leaves such a test standing either fails loudly (good) or, worse,
gets "fixed" by weakening the new code to satisfy it. Rewrite the test to assert
the correct behaviour and name it as a regression guard.

### Verifying UI inside a modal, and stale async verification reports

Two traps that generalise past graphs: a screenshot of a page whose detail
panel was never opened is not evidence about that panel (canvas nodes are not
DOM elements — look for an existing `?demo=`/deep-link hook before building a
click harness), and background verification batches arrive describing code you
have already changed. Both are written up with worked cases in
[`references/graph-canvas-surface-verification.md`](references/graph-canvas-surface-verification.md)
§8–§9.

## Empty surface? Derive from real fields — never seed fakes

### Prepping a surface for a DEMO is a different job — verify the DEFAULT state

Everything below diagnoses a surface that is broken. A demo surface can be entirely
healthy — 200s, real rows, correct code — and still open **empty for the audience**,
because what a viewer sees is `default filter state × current data` and nobody ever
verified that product.

Verified 2026-08-28: `/compliance` returned 200 and the ledger held 340 real entries,
but the view defaulted to **`PHI: high` · `Last 24h`** over data that was PHI
`low`/`none` and 9 days old — rendering *"No decisions match this query"* on the tab
the demo was going to close on. Separately, a narration script written from the API
aggregate ("some are human, some are the agent") contradicted the on-screen KPI strip
(`100% agent · 0% human`) for the default team scope.

Rules: **screenshot every tab in its DEFAULT state** (not the state you navigated into
while testing), compare each default filter against the data's real distribution,
derive narration from the rendered surface rather than the API, and judge each capture
as *a frame* — a correct-but-unreadable graph gets cut. Full checklist and worked
cases: [`references/pre-demo-surface-verification.md`](references/pre-demo-surface-verification.md).

A tab renders empty and the instinct is "seed some data." Usually wrong: the
relationships are already in the rows and the view is querying a field nobody
populates. See `references/empty-surface-derive-dont-seed.md` for the full
diagnostic recipe and a worked example (four "bugs", one root cause, zero writes).

Short version:

1. **Profile the live payload before touching UI code.** Do not reason from the
   TypeScript interface — it lies about what real rows carry. Count field
   population with a throwaway script.
2. **Find the field that IS populated.** A 100%-populated hash or a structured
   ref string usually encodes the relationship the empty view wanted.
3. **Never fabricate audit records.** If a signal genuinely does not exist
   (nobody has ever clicked Flag), say so and generate it through the real app
   path. Inventing history in a governance/audit product is the worst possible
   lie.
4. **Make empty states name the mechanism, not imply breakage.** "No X yet" reads
   like a broken feature; "no repo has been graduated past Tier C, so no loop has
   executed" is true and actionable.
5. **A feature flag being ON says nothing about coverage.** Fallbacks are
   per-consumer by construction. When one surface is empty and its siblings are
   fine, compare their data hooks — verified 2026-08-18, three graph routes
   rendered empty because `useDecisions()` was the single hook missing a demo
   guard its siblings all had, while demo mode was correctly enabled. One grep
   for the flag symbol across the hooks directory answers it.
6. **A component gated behind data is invisible, not broken.** Before debugging
   why new UI never appears, prove its precondition holds. A repeating
   `POST /api/... 401` in the server log is a complete diagnosis and costs one
   process poll — cheaper than any amount of component-level reasoning.
7. **Data flowing is not the same as data rich enough to demo.** Once the empty
   surface is fixed, check whether the fixture exercises the vocabulary the UI
   advertises — a legend decoding six edge kinds over a graph that uses two is a
   defect in the *fixture*, not the legend. Look for an existing seeder before
   authoring data (`find . -name '*seed*'`); most projects have one that writes
   to the live backend and looks unusable offline. Generate the richer fixture
   *from* it by swapping its write function, rather than hand-writing a second
   copy of the scenario that immediately drifts.
   See `references/demo-fixture-generation.md`.
8. **Chrome reporting a non-zero count over an empty content area is a
   DEFINITION MISMATCH, not missing data.** When a picker says "5 decisions"
   and the canvas draws nothing, the lister and the renderer disagree about
   what an item is — a genuine no-data case usually zeroes *both*. Verified
   2026-08-19: a run picker counted every entry carrying a `run_id` while the
   renderer drew only `stage_decision` rows, so the newest bucket (teaching
   signals) became the default and rendered empty. An option that cannot render
   must not be offerable. Filter the selector by the renderer's own predicate.
   Generalises to file-tree/preview, tab-bar/content, results/detail, and
   filter-chip counts: `references/selector-renderer-contract.md`.

## Legibility corrections that recur

`references/operator-legibility-corrections.md` collects the complaints that
sound like polish requests but mean "technically correct, practically unusable":
raw UUIDs where humans need labels + search; repeated identical rows; rolling
windows that render a misleading zero; nav grouped by your architecture instead
of the user's verbs; "demo mode" that fakes the backend instead of curating the
data (and silently disables the primary button). Apply these up front.

## Pitfalls

- **Deployed ≠ built.** A defect fixed locally still ships on the live URL until
  rebuild AND redeploy. Screenshot the *public* URL before saying "fixed" — a
  greyed-out button may be stale bytes rather than a live bug.
- **A successful image build is not a deployment.** `az acr build` succeeding
  only puts bytes in the registry. In one session three separate images
  (`0.1.8`, `0.1.9`, `0.2.0`) built green while production served `0.1.7`,
  because the `containerapp update` step was never run. Always close the loop:

  ```bash
  az containerapp show -n <app> -g <rg> \
    --query "{image:properties.template.containers[0].image,rev:properties.latestRevisionName}" -o tsv
  ```

  Treat build and deploy as **one** unit of work, and if you must report before
  rolling, say "built, not deployed" explicitly.
- **When the UI is auth-gated, grep the deployed bundle instead of guessing.**
  You cannot screenshot a signed-in page, but you can prove your CSS/JS actually
  shipped — this catches a stale revision immediately:

  ```bash
  P=$(curl -sL "$BASE/signin" | grep -oE '/_next/static/chunks/[^"]+\.css' | head -1)
  curl -sL "$BASE$P" | grep -c "my-new-class"        # want >= 1
  curl -sL "$BASE$P" | grep -c "overflow-x:auto"     # want 0 for a removed rule
  ```

  Assert on both a **added** marker and a **removed** one; presence alone can be
  satisfied by a coincidentally similar older build. And check the extraction
  worked — an empty `$P` makes `grep -c` return `0`, which reads exactly like a
  successful "rule is gone" result. A zero from a failed fetch and a zero from a
  real absence are indistinguishable unless you print the intermediate.
- **New API routes: `401` unauthenticated is a successful verification.** It
  proves the route exists and is guarded. A `404` means it never shipped.
- **Container registries pin by digest; reusing a tag will not repull.** Resolve
  the digest, update by `@sha256:...`, and confirm the new revision is
  sole-active at 100% traffic *before* screenshotting.
- **Shell heredocs (`python3 - <<'PY'`) get blocked by the command parser.** For
  bulk source edits, write a real `.py` file, run it, verify by grep + `tsc`,
  then delete it — and tell the user the edit was script-driven so the diff is
  not a surprise.
- **Stale LSP diagnostics after a patch.** Errors citing lines you just deleted
  are usually echoes. Confirm with a real `tsc --noEmit` before chasing them.
- **Before trusting a destructive-sounding button, read its implementation.** A
  user asking "is Clear X safe?" deserves the code path, not reassurance from
  memory — and if the label was ambiguous enough to prompt the question, tighten
  the label too.
- **Verify the function the UI actually calls, not a plausible sibling.** Stated
  confidently to the user 2026-08-19 that a run picker would default to a
  particular item; the claim came from reading `runIdsFrom()` (the graph
  builder's sort) while the picker used `buildRunOptions()` (a different sort
  over a wider entry set). The real default rendered an empty canvas. Codebases
  routinely carry two similarly-named functions with overlapping output and
  different filters — **trace from the component outward**
  (`grep -n 'buildRun\|useX(' page.tsx`), never from the library inward. Reading
  *a* code path and reporting it as *the* behaviour is the same error shape as
  quoting a rule from memory instead of from the bundle.

## Multi-perspective QA is a closed loop, not three reports

When the user asks for vision, product, and end-user perspectives, the output is
not a review document. The required loop is:

1. Get the current branch green and deploy one clearly-labeled **review
   candidate** when real authentication/data cannot be reproduced locally.
2. Capture authenticated pixels from that exact candidate.
3. Run independent vision, PM, and user reviews in parallel when their inputs do
   not depend on each other.
4. Consolidate overlap into a short prioritized change list. Contradictions are
   product decisions; resolve them explicitly rather than implementing both.
5. Implement the accepted feedback, add regression tests for observed defects,
   and repeat build/test/lint.
6. Drive the changed interactions and capture final pixels on the final build.
7. Commit/push, deploy by immutable digest, then verify revision health, traffic,
   auth state, data state, and the public URL.

Do not call the candidate deployment the release. Do not stop after the three
reviews, and do not present review findings as completion. Report only after the
feedback has been executed and the final deployed bytes have been inspected, or
state the exact external blocker.

### Interaction-model checks for the three-perspective cycle

These failures recur because each looks reasonable from one perspective and
breaks only when the full workflow is walked:

- **Global and local search are separate state.** A library query and a filter
  inside one selected item should not share one mutable parameter merely because
  it is convenient. Clearing the local filter must not erase the global search
  the user came from. Use separate URL params and seed the local one on entry
  when a nested match opened the item.
- **Explain why a nested match returned its parent.** If a song/child match
  surfaces a card/parent whose own title does not match, render the matching
  child text under the result. Otherwise correct search looks random.
- **Never advertise a dead touch interaction.** Native HTML drag-and-drop is not
  a mobile reorder control. On coarse pointers, hide the grip and drag copy and
  show controls that actually work.
- **Name the scope of a write before it happens.** If an icon or setting applies
  to a whole section rather than one row, label the control and picker copy at
  that scope. Place the control beside the object it modifies.
- **Separate similar visual artifacts.** A library/card cover and a tiny player
  display icon are different things; labels, previews, and success feedback must
  not let the user mistake one for the other.
- **A saved fallback credential is not a working fallback.** Proxy/route settings
  need an authenticated test action that reports each route without echoing
  secrets. Persistence-only success defers the real failure to a later task.

## Checklist

- [ ] Theme-token lint clean (`scripts/theme_token_contrast_lint.py`) — catches
      inverting `bg-` tokens behind fixed `text-white`, which no static hex-pair
      check can see. See `references/theme-inverting-token-contrast.md`.
- [ ] Production build run (not just dev server / type-check)
- [ ] Served against real data, not fixtures
- [ ] **Every background launch POLLED for `status: exited`** — never infer a server's health from a port answering
- [ ] **Any baseline-failure claim reproduced in an isolated exact-revision copy**, preserving dirty source and both reports
- [ ] Screenshot taken; PNG size sanity-checked
- [ ] Vision asked a specific, falsifiable question
- [ ] **A capture-derived defect was PROBED before any fix was written** — a vision report is a claim, not evidence; if the probe finds no offenders, revert the speculative fixes
- [ ] **Print output verified as a real PDF** (page-object count + rendered page 1) if any page-count promise was made
- [ ] **Emoji/icon glyphs checked for tofu boxes ☐ in a render**, and E-version capped for the target hardware
- [ ] **Any verification script printed its DENOMINATOR and asserted it non-zero** — a regex that matched nothing reports "none" exactly like a real pass
- [ ] **Scripted bulk edits asserted both that the pattern matched AND that neighbouring blocks survived** (`re.S` + `.*?` silently eats data)
- [ ] **For a SET of generated visuals, the question was COMPARATIVE** ("do the SUVs read taller than the fastback?"), not per-item — set defects live in the relationships
- [ ] **Screenshot taken BEFORE deploying**, not after — `grep`-ing an `aria-label` out of the HTML proves presence, never correctness
- [ ] **No bug reported on the strength of a grep MISS** — a missing literal in HTML is a null result (frameworks split text nodes; `money()` rounds), so LOOK before writing "it's broken"
- [ ] **Client-persisted state (localStorage) cleared or key-bumped** before concluding a corrected default did not take effect
- [ ] **Every TABLE probed per-cell for BOTH clipping and overlap** (`scripts/measure-table-clipping.js`; assert `clippedCells === 0` AND `overlaps === 0`) — page-level `scrollWidth` returns 0 over a truncated table, `scrollWidth` per cell returns 0 over an overlapping one, and fixing the one table the user screenshotted routinely leaves siblings broken
- [ ] **The probe re-run at every shipped breakpoint** (1440 / 820 / 390 via `Emulation.setDeviceMetricsOverride`) — responsive blocks carry their own positional rules that survive the desktop fix
- [ ] **No cell wrapping keyed off `nth-child`** — `grep -n 'nth-child' <renderer>`; position never predicts content, and the same document routinely has prose in a different column per table
- [ ] **Any class the new CSS depends on confirmed present in the output** (`grep -c 'class="wide"'`) — a rule for a class nothing emits is inert
- [ ] **JS actually EXECUTED, not just structurally parsed** — `new Function(<script body>)` returns OK, and a post-load probe shows real data plus a rendered element count matching an EXPECTED number. Tag-balance / DOM-id / function-defined checks pass identically over a page killed by a `SyntaxError`
- [ ] **No literal `${` surviving outside `<script>`** in the served HTML — template expressions in the static skeleton render as raw source
- [ ] **`old_string` in any patch to a JS literal included the `const NAME = {` declaration**, not just a property line — a fragment match silently deletes the declaration and leaves valid-looking, dead code
- [ ] **`node -c` run after every edit to CSS embedded in a JS template literal** — one backtick in a comment kills the whole script, and knowing this does not prevent it
- [ ] **Interactive controls actually driven** (fill, click, reload, re-read)
- [ ] **Modal/panel UI opened before claiming it was verified** (a closed-state capture proves nothing about it)
- [ ] **Every factual claim about the repo grepped against the source** (rule ids, schema fields, counts — vision cannot catch a fabricated quote)
- [ ] **Captions/counts/chips beside a visualisation checked against the PICTURE**, not just against the data
- [ ] **For any measured pass: predicate proved named, and one unchecked property of that surface named**
- [ ] **Subagent verification reports read for COVERAGE, not just verdict** (n-of-N, never a bare "no defects")
- [ ] **Async verification reports checked against dispatch time** before acting — and their OBSERVATIONS read separately from their verdict, since a superseded or misdiagnosed report can still be the only thing that noticed a live defect
- [ ] **Tests that assert the OLD wrong behaviour found and rewritten**
- [ ] **Browser console clean — zero failed JS chunk requests**
- [ ] Both light and dark verified if a toggle exists
- [ ] **Layout metric can express the actual failure** (overlap + viewport fit, not just scrollWidth)
- [ ] **Narrowest real viewport checked (320px), in every auth/content state**
- [ ] Public URL screenshotted if claiming "deployed"
- [ ] **Deployed asset bundle grepped for the change** when pixels are unreachable
- [ ] **Any capture destined for a DEMO checked in its DEFAULT filter state**, with the default compared against the data's real distribution — a healthy 200-returning route can still open on "no results" for the audience
- [ ] Status reported as live / local / unproven / blocked
- [ ] No OAuth consent granted on the user's real account to satisfy the checklist
