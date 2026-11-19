# Verifying canvas-chart INTERACTIONS (drag/zoom/pan) with real synthetic input

DOM assertions cannot verify a canvas chart. There is no element to query — the
whole chart is pixels. "The handler is attached" and "the option is set" both pass
while the gesture does nothing. The only honest proof is: **dispatch real input,
then read the chart's own internal scale state before and after.**

## The pattern (Chart.js, but generalises to any canvas chart with a JS API)
Drive Chrome over CDP and diff the scale bounds around a synthetic drag:

```python
# 1. read state BEFORE
#    Chart.getChart(canvas).scales.y.min / .max  (and .x)
# 2. dispatch a REAL drag: mousePressed -> N x mouseMoved -> mouseReleased
#    (a single jump-move often won't trigger drag logic; step it ~8 times)
cmd("Input.dispatchMouseEvent", {"type":"mousePressed", "x":X,"y":Y,
                                 "button":"left","clickCount":1,"buttons":1})
for i in range(1, steps+1):
    cmd("Input.dispatchMouseEvent", {"type":"mouseMoved",
         "x":X+dx*i/steps, "y":Y+dy*i/steps, "button":"left", "buttons":1})
    time.sleep(0.03)
cmd("Input.dispatchMouseEvent", {"type":"mouseReleased", "x":X+dx,"y":Y+dy,
                                 "button":"left","buttons":0})
# 3. read state AFTER and assert it CHANGED in the expected axis only
```

A passing result looks like this (axis-drag scaling, verified 2026-09-03):
- drag price bar down 90px → `y 100–450` → `168.86–381.14`, **x unchanged**
- drag time bar left 120px → `x 0–126` → `31–95`, **y unchanged**

Asserting the *other* axis is unchanged is what proves the axes are independent
rather than both being dragged by a catch-all handler.

## Coordinates: derive hit zones from the chart, never eyeball them
`chart.chartArea` gives the plot rectangle; the axis bars are the gap between it
and the canvas edge. Read both and compute:
```js
const a = chart.chartArea, r = canvas.getBoundingClientRect();
// e.g. canvas w=1016, a.right=982  -> ~34px price bar on the right
//      canvas h=300,  a.bottom=275 -> ~25px time bar at the bottom
```
Then add the canvas's viewport offset (`r.left`/`r.top`) before dispatching — CDP
coordinates are viewport-absolute, `chartArea` is canvas-relative. Mixing them up
silently clicks empty space and the test "fails" for the wrong reason.

## ⚠️ Read the PLUGIN SOURCE before depending on its callback contract
Biggest trap of the session. `chartjs-plugin-zoom@2` invokes a function-valued
`mode` as **`mode({chart})`** — there is **no event** in that context. Code that
did `ctx.event.native.shiftKey` to switch axes therefore always read `undefined`,
so shift+scroll silently did nothing *while plain scroll kept working* — i.e. it
looked fine. Fix: track modifier state on a separate `window` keydown/keyup flag.

Verify the contract cheaply by fetching the bundle and grepping it:
```bash
curl -s "https://cdn.jsdelivr.net/npm/<plugin>@2" -o /tmp/p.js
grep -o 'zoomScale' /tmp/p.js | head          # does the API you plan to call exist?
# find how an option is invoked, e.g.:
#   function c(t,n){return"function"==typeof t&&(t=t({chart:n})), ...}
```
**Rule: any option you pass as a function — confirm what arguments it actually
receives.** A wrong assumption here degrades to a no-op, not an error, which is
the hardest failure mode to notice.

## Teardown is part of correctness for modal/re-rendered charts
Handlers attached to a shared canvas STACK every time the modal reopens — the
chart gets progressively more sensitive with each open. Always return an
unsubscribe closure from the attach function and call it in the chart's destroy
path (alongside `chart.destroy()`), removing every listener and any `window`-level
modifier listeners too.

## CDP connection gotchas (cost real time)
- **WebSocket handshake 403**: Chrome rejects the CDP socket when an `Origin`
  header is present. Use `websocket.create_connection(url, suppress_origin=True)`
  (or launch with `--remote-allow-origins=*`).
- **`localhost` may be blocked by the agent's browser helper** — attach to an
  already-running debug Chrome (`curl 127.0.0.1:9222/json/version`) and open the
  tab with `PUT /json/new?<url>` instead.
- **SPA lazy-loads pages**: `BT.pages` / route modules register asynchronously.
  Checking immediately after navigation shows a route "missing" that loads a
  moment later — set the hash, sleep, then assert. A deep link may also need the
  base route visited first before the `?param=` form opens the modal.
