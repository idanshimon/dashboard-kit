#!/usr/bin/env python3
"""Measure real layout geometry in a live page over CDP, and capture honestly.

Use when a screenshot APPEARS to show clipped/overflowing/cut-off content.
Chrome's `--headless --screenshot` CLI flag can crop the image, so a vision
model will faithfully report truncation that does not exist in the page.
Measure before you patch CSS.

Setup (one process, reused):
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \\
        --headless=new --disable-gpu --no-sandbox \\
        --remote-debugging-port=9334 "http://localhost:PORT/"

Usage:
    python3 cdp-measure.py measure http://localhost:4200/finance "Rose from"
    python3 cdp-measure.py shot    http://localhost:4200/finance out.png 390 950

Requires: pip install websockets
"""
import asyncio, base64, json, sys, urllib.request

CDP_PORT = 9334


def ws_url(port=CDP_PORT):
    d = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list"))
    pages = [t["webSocketDebuggerUrl"] for t in d if t["type"] == "page"]
    if not pages:
        sys.exit("No page target. Is Chrome running with --remote-debugging-port?")
    return pages[0]


class CDP:
    def __init__(self, ws):
        self.ws, self.i = ws, 0

    async def send(self, method, params=None):
        self.i += 1
        mid = self.i
        await self.ws.send(json.dumps({"id": mid, "method": method,
                                       "params": params or {}}))
        while True:
            r = json.loads(await self.ws.recv())
            if r.get("id") == mid:
                return r

    async def evaluate(self, expr):
        r = await self.send("Runtime.evaluate",
                            {"expression": expr, "returnByValue": True})
        return r["result"]["result"].get("value")


# Walks the ancestor chain reporting scrollWidth vs clientWidth, and the
# per-line rects of the matched element. If scrollWidth == clientWidth all the
# way up AND the last line's right edge is inside the viewport, the page is
# fine and your SCREENSHOT is cropping.
MEASURE = r"""(()=>{
  const needle = %s;
  const el=[...document.querySelectorAll('p,div,td,span,h1,h2,h3')]
    .filter(e=>e.textContent.trim().startsWith(needle)).pop();
  if(!el) return JSON.stringify({err:'not found', needle});
  const chain=[]; let n=el;
  while(n && n!==document.documentElement){
    const r=n.getBoundingClientRect(), cs=getComputedStyle(n);
    chain.push({tag:n.tagName, cls:(n.className||'').toString().slice(0,44),
      w:Math.round(r.width), right:Math.round(r.right),
      scrollW:n.scrollWidth, clientW:n.clientWidth,
      overflows:n.scrollWidth>n.clientWidth,
      ov:cs.overflow, wrap:cs.overflowWrap, brk:cs.wordBreak, minW:cs.minWidth});
    n=n.parentElement;
  }
  const range=document.createRange(); range.selectNodeContents(el);
  const lines=[...range.getClientRects()]
    .map(x=>({w:Math.round(x.width), right:Math.round(x.right)}));
  const docW=document.documentElement.clientWidth;
  return JSON.stringify({
    text:el.textContent, docW, bodyScrollW:document.body.scrollWidth,
    lines, anyOverflow:chain.some(c=>c.overflows),
    maxLineRight:Math.max(...lines.map(l=>l.right)),
    escapesViewport:Math.max(...lines.map(l=>l.right))>docW,
    chain});
})()"""


async def measure(url, needle):
    import websockets
    async with websockets.connect(ws_url(), max_size=None) as ws:
        c = CDP(ws)
        await c.send("Page.enable")
        await c.send("Emulation.setDeviceMetricsOverride",
                     {"width": 390, "height": 950,
                      "deviceScaleFactor": 2, "mobile": True})
        await c.send("Page.navigate", {"url": url})
        await asyncio.sleep(3)
        d = json.loads(await c.evaluate(MEASURE % json.dumps(needle)))
        if d.get("err"):
            print("NOT FOUND:", d["needle"]); return
        print("TEXT:", d["text"])
        print(f"viewport={d['docW']}  bodyScrollW={d['bodyScrollW']}")
        print(f"lines={len(d['lines'])}  maxLineRight={d['maxLineRight']}")
        for i, l in enumerate(d["lines"], 1):
            print(f"   line {i}: width={l['w']:4} right={l['right']:4}")
        print()
        for c_ in d["chain"][:8]:
            flag = "  <-- OVERFLOWS" if c_["overflows"] else ""
            print(f"  {c_['tag']:6} w={c_['w']:4} scrollW={c_['scrollW']:4} "
                  f"clientW={c_['clientW']:4} ov={c_['ov']:8} "
                  f"wrap={c_['wrap']:8} minW={c_['minW']:5}{flag}")
        print()
        if not d["anyOverflow"] and not d["escapesViewport"]:
            print("VERDICT: no overflow, text inside viewport.")
            print("         If a screenshot shows it cut, the CAPTURE is")
            print("         cropping. Use `shot` below, not --screenshot.")
        else:
            print("VERDICT: real overflow. Fix with overflow-wrap:anywhere +")
            print("         min-width:0 on flex/grid children. NEVER")
            print("         overflow:hidden -- that clips, it does not wrap.")


async def shot(url, out, w, h):
    import websockets
    async with websockets.connect(ws_url(), max_size=None) as ws:
        c = CDP(ws)
        await c.send("Page.enable")
        await c.send("Emulation.setDeviceMetricsOverride",
                     {"width": w, "height": h, "deviceScaleFactor": 2,
                      "mobile": w < 900})
        await c.send("Page.navigate", {"url": url})
        await asyncio.sleep(3)
        r = await c.send("Page.captureScreenshot",
                         {"format": "png", "captureBeyondViewport": True})
        open(out, "wb").write(base64.b64decode(r["result"]["data"]))
        print("wrote", out)


# Flip theme through the app's OWN api so you exercise the real code path,
# then read the resulting computed background back out of the live DOM.
async def theme(url, setter="window.__theme.set('light')"):
    import websockets
    async with websockets.connect(ws_url(), max_size=None) as ws:
        c = CDP(ws)
        await c.send("Page.enable")
        await c.send("Page.navigate", {"url": url})
        await asyncio.sleep(2.5)
        await c.evaluate(setter)
        await asyncio.sleep(1)
        print("data-theme:", await c.evaluate("document.documentElement.dataset.theme"))
        print("body bg   :", await c.evaluate(
            "getComputedStyle(document.body).backgroundColor"))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "measure":
        asyncio.run(measure(sys.argv[2], sys.argv[3]))
    elif cmd == "shot":
        asyncio.run(shot(sys.argv[2], sys.argv[3],
                         int(sys.argv[4]), int(sys.argv[5])))
    elif cmd == "theme":
        asyncio.run(theme(sys.argv[2],
                          sys.argv[3] if len(sys.argv) > 3
                          else "window.__theme.set('light')"))
    else:
        sys.exit(__doc__)
