# Headless viewport traps — when the screenshot lies about your layout

## The trap: `--window-size` does NOT emulate a mobile device

```bash
# LOOKS like a 390px iPhone. IS NOT.
chrome --headless --window-size=390,844 --screenshot=/tmp/m.png "$URL"
```

This sets the **window** to 390px. It does not set the layout viewport, does not
set `deviceScaleFactor`, and — critically — **does not make `<meta name=viewport>`
take effect**. The page lays out at desktop width and gets cropped to 390px in
the image.

The resulting screenshot looks exactly like a horizontal-overflow bug: text
sheared off at the right edge, labels clipped mid-word. It is an artifact of the
capture, not a defect in the page.

Worked case (lgw exhibition site, Aug 2026): a mobile work view screenshotted as
badly clipped. Three CSS fixes were applied to a page that was **already
correct** — `overflow-x: hidden`, `minmax(0, 1fr)` on grid columns,
`overflow-wrap: anywhere`, `min-width: 0` on grid children. Each fix
re-screenshotted identically clipped, because the capture method never changed.
The page had never overflowed.

## Measure before you fix

Never conclude "it overflows" from pixels alone. Ask the DOM:

```js
(() => {
  const o = [];
  document.querySelectorAll('*').forEach(el => {
    const r = el.getBoundingClientRect();
    if (r.right > window.innerWidth + 1)
      o.push(el.tagName + '.' + (el.className || '') +
             ' right=' + Math.round(r.right) + ' w=' + Math.round(r.width));
  });
  return JSON.stringify({ vw: innerWidth,
                          scrollW: document.documentElement.scrollWidth,
                          over: o.slice(0, 12) }, null, 1);
})()
```

Compare both measurements to the **requested emulated width** before concluding anything. `scrollW === vw` and `over: []` can still hide a real defect: an intrinsically wide table can expand the mobile layout viewport so both values agree at a width larger than requested. Equality alone does not prove the layout is fine or the capture is wrong.

With Playwright, assert the requested width explicitly after each route and reload:

```js
const requestedWidth = 390;
const context = await browser.newContext({
  viewport: { width: requestedWidth, height: 844 },
  isMobile: true,
  deviceScaleFactor: 1,
});
const page = await context.newPage();
await page.goto(url);
await page.locator('h1').waitFor();
const dimensions = await page.evaluate(() => ({
  layout: innerWidth,
  content: document.documentElement.scrollWidth,
}));
assert.equal(dimensions.layout, requestedWidth);
assert(dimensions.content <= requestedWidth + 1);
```

When the emulation is correct but the layout expands, inspect intrinsic widths, non-wrapping badges and source identifiers. For dense mobile dossier tables, stack each row's labeled fields at the mobile breakpoint and allow long identifiers to wrap; keep intentional comparison-table scrolling inside its own container rather than hiding overflow on the document. Re-run the same route/width assertion after the fix.

Note this complements the pairwise-overlap check in SKILL.md — `scrollWidth`
catches things extending past the viewport, the collision loop catches things
overlapping inside it. Neither sees the other's bug.

## The correct mobile capture: CDP with real device metrics

```python
import subprocess, time, json, urllib.request, base64, websocket

CH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
p = subprocess.Popen(
    [CH, "--headless", "--disable-gpu",
     "--remote-allow-origins=*",              # REQUIRED — see below
     "--remote-debugging-port=9336", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(3)
try:
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9336/json"))
    ws = websocket.create_connection(
        [t for t in tabs if t["type"] == "page"][0]["webSocketDebuggerUrl"])
    n = [0]
    def cmd(m, pr=None):
        n[0] += 1
        ws.send(json.dumps({"id": n[0], "method": m, "params": pr or {}}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == n[0]:
                return r

    # THIS is what makes it a phone.
    cmd("Emulation.setDeviceMetricsOverride",
        {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
    cmd("Page.navigate", {"url": URL})
    time.sleep(4)
    shot = cmd("Page.captureScreenshot", {"captureBeyondViewport": True})
    open(OUT, "wb").write(base64.b64decode(shot["result"]["data"]))
finally:
    p.terminate()
```

`mobile: True` is the flag that activates the viewport meta tag and the mobile
media queries. Without it you are still screenshotting a narrow desktop.

## `--remote-allow-origins=*` or the websocket 403s

Chrome ≥111 rejects CDP websocket handshakes that carry an `Origin` header:

```
websocket._exceptions.WebSocketBadStatusException: Handshake status 403 Forbidden
Rejected an incoming WebSocket connection from the http://127.0.0.1:9335 origin.
Use the command line flag --remote-allow-origins=...
```

Two independent fixes, both work:

- launch Chrome with `--remote-allow-origins=*`
- connect with `create_connection(url, suppress_origin=True)`

Belt and braces is fine. This is a handshake rejection, **not** a sign that the
debugging port is wrong or that Chrome failed to start.

## `websocket` import fails inside `execute_code`

`execute_code` runs in its own sandbox interpreter that lacks `websocket-client`
even when the system Python has it. Write the probe to a real `.py` file and run
it with `terminal()` instead of inlining it.

## Capturing a tab that is ALREADY OPEN (no headless launch)

Different situation from everything above: the user has the artifact open in their normal
Chrome and you want to inspect *that*. Launching a second headless browser is wasteful and
gives you a different profile.

`browser_navigate` refuses `file://` and loopback URLs (`"Blocked: URL targets a private or
internal address"`), and serving over `http://127.0.0.1:PORT` does not help — the block is on
the address class, not the scheme. Drive the existing tab over CDP by `targetId` instead.

```python
import json, urllib.request, base64, websocket, time

d = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/list"))
# match on the file/URL you opened; note the key is "id", NOT "targetId", on /json/list
tid = [t for t in d if t.get("type") == "page" and "myreport" in t.get("url", "")][0]
ws = websocket.create_connection(tid["webSocketDebuggerUrl"],
                                 timeout=30, max_size=None, suppress_origin=True)
n = [0]
def cmd(m, p=None):
    n[0] += 1
    ws.send(json.dumps({"id": n[0], "method": m, "params": p or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == n[0]:
            return r

cmd("Page.reload", {"ignoreCache": True}); time.sleep(1.5)
# scroll to the section you changed — a full-page thumbnail is unreadable
cmd("Runtime.evaluate", {"expression":
    "[...document.querySelectorAll('h2')].find(h=>h.textContent.includes('Evidence'))"
    ".scrollIntoView({block:'start'});'ok'"})
time.sleep(0.6)
r = cmd("Page.captureScreenshot", {"format": "png"})
open("/tmp/shot.png", "wb").write(base64.b64decode(r["result"]["data"]))
```

Gotchas, each of which cost a cycle:

- **`max_size=None`** on `create_connection`, or a full-page PNG exceeds the default frame
  limit and the recv truncates.
- **`suppress_origin=True`** — same 403 handshake rejection documented above, and it applies
  to an attached browser you did not launch, so you cannot fix it with a flag.
- **A stateless one-shot `Page.captureScreenshot` gets persisted and TRUNCATED** past
  ~300KB of base64, and `b64decode` then fails with *"number of data characters cannot be 1
  more than a multiple of 4"*. This is a transport limit, not a capture failure. The
  persistent websocket above avoids it entirely; if you are stuck with the one-shot path,
  see the regex-trim recipe in SKILL.md under "Screenshotting via an already-attached
  Chrome".
- **`/json/list` returns `id`; `Target.getTargets` returns `targetId`.** Mixing them up
  raises `KeyError: 'targetId'`. `/json/list` is also far smaller — `Target.getTargets` on a
  busy browser returns every service worker and can itself blow the result limit.

### Sweeping breakpoints on that same tab

Once connected, loop the emulation override rather than relaunching:

```python
for w, label in [(1440, "desktop"), (820, "tablet"), (390, "mobile")]:
    cmd("Emulation.setDeviceMetricsOverride",
        {"width": w, "height": 900, "deviceScaleFactor": 1, "mobile": w < 500})
    time.sleep(0.8)
    print(label, cmd("Runtime.evaluate",
                     {"expression": PROBE, "returnByValue": True})
                 ["result"]["result"]["value"])
cmd("Emulation.clearDeviceMetricsOverride")   # don't leave the user's tab emulated
```

Always clear the override at the end — otherwise you hand the user back a browser tab stuck
at 390px and they will report it as a new bug.

## Checklist for any mobile/responsive claim

- [ ] Captured with `Emulation.setDeviceMetricsOverride` + `mobile: True`,
      not bare `--window-size`
- [ ] `innerWidth === requestedWidth` AND `scrollWidth <= requestedWidth + 1` asserted after each route/reload, not merely equality between two potentially expanded measurements
- [ ] Overflowing-element list is empty (name the elements if not)
- [ ] Pairwise overlap check run (see SKILL.md — different bug class)
- [ ] Narrowest real device checked (320px), in every auth/content state
