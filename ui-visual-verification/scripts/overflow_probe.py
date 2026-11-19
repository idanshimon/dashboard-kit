#!/usr/bin/env python3
"""Measure real horizontal overflow at a given viewport, with true device emulation.

Bare `--window-size=390,844` on headless Chrome does NOT apply mobile media
queries, so screenshots taken that way can show a "clipping bug" that does not
exist in the shipping layout. This drives CDP with
Emulation.setDeviceMetricsOverride(mobile=True) and reports the DOM's own
numbers, so you can reproduce a vision-reported defect as a measurement before
patching CSS.

Usage:
    python3 overflow_probe.py <url> [width] [height]
    python3 overflow_probe.py http://localhost:3737/site/work.html 390 844

Output:
    {"vw": 390, "scrollW": 390, "over": []}          <- clean
    {"vw": 390, "scrollW": 812, "over": ["DIV.label right=812 w=420", ...]}

Requires: websocket-client (pip install websocket-client), Chrome/Chromium.

Gotcha this encodes: without --remote-allow-origins=* the websocket handshake
returns "403 Rejected an incoming WebSocket connection from the ... origin".
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request

import websocket  # type: ignore

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
PORT = 9335


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    url = sys.argv[1]
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 390
    h = int(sys.argv[3]) if len(sys.argv) > 3 else 844

    proc = subprocess.Popen(
        [CHROME, "--headless", "--disable-gpu", "--remote-allow-origins=*",
         f"--remote-debugging-port={PORT}", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(3)
    try:
        tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
        page = [t for t in tabs if t["type"] == "page"][0]
        ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=30)
        n = [0]

        def cmd(method, params=None):
            n[0] += 1
            ws.send(json.dumps({"id": n[0], "method": method, "params": params or {}}))
            while True:
                r = json.loads(ws.recv())
                if r.get("id") == n[0]:
                    return r

        # mobile=True is the whole point — this is what applies the media query.
        cmd("Emulation.setDeviceMetricsOverride",
            {"width": w, "height": h, "deviceScaleFactor": 2, "mobile": True})
        cmd("Page.navigate", {"url": url})
        time.sleep(4)

        js = """(()=>{const o=[];document.querySelectorAll('*').forEach(el=>{
        const r=el.getBoundingClientRect();
        if(r.right>window.innerWidth+1)
          o.push(el.tagName+'.'+(el.className||'')+' right='+Math.round(r.right)
                 +' w='+Math.round(r.width));});
        return JSON.stringify({vw:window.innerWidth,
                               scrollW:document.documentElement.scrollWidth,
                               over:o.slice(0,12)},null,1)})()"""
        out = cmd("Runtime.evaluate", {"expression": js, "returnByValue": True})
        print(out["result"]["result"]["value"])
        data = json.loads(out["result"]["result"]["value"])
        return 0 if not data["over"] and data["scrollW"] == data["vw"] else 1
    finally:
        proc.terminate()


if __name__ == "__main__":
    sys.exit(main())
