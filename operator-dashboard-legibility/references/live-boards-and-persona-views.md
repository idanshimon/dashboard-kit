# Live boards and persona views

## Silent refresh: morph, don't rebuild

```js
function quietRender(host, html, key) {          // key = `${persona}|${recordId}`
  if (host.dataset.key !== key || !host.firstElementChild) {
    host.innerHTML = html; host.dataset.key = key;
    host.firstElementChild?.classList.add("enter"); return;   // entry animation only here
  }
  const t = document.createElement("div"); t.innerHTML = html;
  morph(host.firstElementChild, t.firstElementChild);
}
function morph(cur, nxt) {
  if (cur.nodeType !== nxt.nodeType || cur.nodeName !== nxt.nodeName) return cur.replaceWith(nxt.cloneNode(true));
  if (cur.nodeType === 3) { if (cur.nodeValue !== nxt.nodeValue) { tick(cur.parentElement, cur.nodeValue, nxt.nodeValue); cur.nodeValue = nxt.nodeValue; } return; }
  if (cur.nodeType !== 1) return;
  // copy attrs except class; merge class keeping transient tick-* classes
  // ... then recurse children by index, append extras, remove surplus
}
```

- Use `setAttribute("class", …)`, never `el.className = …`: on SVG elements
  `className` is a read-only `SVGAnimatedString` and throws on every tick.
- CSS: `.board.enter{animation:rise .35s}` (NOT on `.board` itself, or every
  class rewrite replays it). Tick: `@keyframes` from a faint `text-shadow` +
  `brightness(1.18)` back to none, 1.4 s; restart via remove class, read
  `offsetWidth`, add class.

## Calm-refresh test (Playwright in real Chrome)

Inside one `page.evaluate`: grab `board`, a mid gauge, its `top`; attach a
`MutationObserver` (characterData + class attrs); wait 12 s of real ticks;
return `sameBoard`, `sameGauge`, `visibleShiftPx`, text-change count, and a
count of `.enter` re-adds. Pass = same nodes, shift 0, changes > 0, re-enters 0,
and switching persona DOES add `.enter` once.

## Spatial / 3D cohort views (ring of pods, map of beds)

- **Seat each entity by a STABLE key (sorted id), never by the stream's list
  order.** Watch lists usually arrive sorted by score, so index-based placement
  swaps two entities every time their scores cross. Users read that as "it keeps
  switching spots — is it sorting by urgency?". Urgency belongs in height and
  colour, not position.
- **Heat map = one continuous ramp** (blue → cyan → yellow → orange → red)
  driven by the SAME metric as height for the active persona, applied to the
  object plus a soft floor glow (disc with a radial-gradient opacity texture).
  Ease colour and height toward targets every frame (`Color3.Lerp`, k≈dt·4)
  so a tick never flips anything. A binary palette (gold vs blue) is not a heat
  map. Show a legend naming what heat means per persona.
- **Centre the scene in the FREE area, not with a fixed screen offset.** Set the
  camera viewport to the strip between side panels (Babylon:
  `camera.viewport = new Viewport(left/w, 0, (w-left-right)/w, 1)`) and recompute
  when a panel opens/closes or the window resizes. A hardcoded
  `targetScreenOffset` is only right at one width. Do not re-target the camera
  on selection; show selection by glow/satellites instead.
- Verify numerically: project world origin with
  `Vector3.Project(origin, Identity, scene.getTransformMatrix(), viewport.toGlobal(w,h))`,
  divide by device-pixel ratio, compare with `(missionRight + panelLeft)/2`
  (tolerance ~25 px, panel open AND closed); record every seat, wait several
  ticks, assert 0 seats moved.

## Entity search on a live board

Operators always ask for it once there are more than ~15 entities; add it up
front. One input (`/` shortcut) matching id with and without prefix, initials,
condition, device, setting, stage (normalise: lowercase, strip non-alphanumerics).
Results ranked by score, refreshed on ticks while open; dim non-matches in the
scene; arrows / Enter / click select in the active persona; Escape clears and
restores visibility; explicit "No patient matches …" row. Use `mousedown` +
`preventDefault` on result rows so input blur doesn't eat the click.

## Persona boards over one clinical/ops dataset

| Persona | Leads with | Must show |
|---|---|---|
| Physician | score + session trend | every measure vs normal/concerning, plain-words state, share of score it drives (sorted biggest first), missing ≠ 0, thresholds labelled if demo values |
| Nurse | ranked queue | pending approval → truly-missing readings → score; "what changed since I started watching" marked worse/better; one next step |
| Finance | exposure if escalated | per-day cost, days until cost exceeds expected payment, cohort exposure; every rate with its source; "no sourced rate" instead of a guess; no savings/outcome figures; finance never approves clinical actions |

- "Not applicable" is not "missing": a reading the record cannot have (no
  device → no device-flow) must not flag the patient as missing data.
- Trends only from frames received this session, labelled so; never back-fill.
- When the action gate is open, move Approve/Reject to the top of the panel and
  hide the launch button, or vision review reports "no decision control".
- A vendor/platform framing strip (which product each loop step represents)
  carries an honest status per step (planned / stand-in / real / stub).

## Test-harness pitfalls on a shared live demo server

- Repeated end-to-end runs mutate server state (tripped patients sit in the
  top band, so the rule declines). Pick the candidate dynamically (loop over
  non-critical entities until one reaches the gate) instead of hardcoding an id.
- If the loop never reaches the gate after many runs, restart the local server
  before debugging the UI change; re-run to confirm.
- Guard optional DOM in assertions (`?.textContent`): n/a cards lack footers.
