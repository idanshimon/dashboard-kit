# Authenticated live-app QA preflight

Use this when the browser already has the user's third-party account/profile, but
the app session may be stale. The goal is to distinguish a real authenticated
screen from a shell populated by `401` fallbacks before vision sees it.

## Required assertions

Before screenshotting, collect one JSON object from page context:

```js
(async () => {
  const session = await fetch('/api/me', {cache: 'no-store'}).then(async r => ({
    status: r.status,
    body: await r.json().catch(() => null),
  }));
  const data = await fetch('/api/settings', {cache: 'no-store'}).then(async r => ({
    status: r.status,
    body: await r.json().catch(() => null),
  }));
  return {
    url: location.href,
    nav: document.body.innerText.slice(0, 300),
    session,
    data,
  };
})()
```

Pass criteria:

- session status is 200 and its signed-in indicator is true
- the key data endpoint is 200
- nav/identity shows the signed-in user, not `Sign in`
- payload contains real counts/records rather than component defaults

## Attached-Chrome CDP recipe

When browser tools cannot preserve the existing profile, use Chrome's existing
CDP tab. Never log cookies or tokens.

```python
import json, urllib.request
from websocket import create_connection

tabs = json.load(urllib.request.urlopen('http://127.0.0.1:9222/json/list'))
tab = next(t for t in tabs if 'the-app-host' in t.get('url', ''))
ws = create_connection(tab['webSocketDebuggerUrl'], timeout=30,
                       suppress_origin=True)
```

Send `Runtime.evaluate` with the assertion expression above. For screenshots,
set `Emulation.setDeviceMetricsOverride`, then `Page.captureScreenshot`; decode
the returned base64 to a local PNG and downscale before vision.

## Expired app session

If the browser profile previously authorized the app, navigate to the app's
normal login route and wait. Then inspect `location.href` and body text:

- returned to app callback/home: repeat the required assertions
- provider consent page: STOP; do not authorize
- password/MFA prompt: STOP; do not enter secrets

A direct callback without consent is only a session renewal. It does not make it
safe to skip the post-login assertions.

## Common false review

A protected route may render its layout while API calls are 401. Typical clues:

- nav says `Sign in`
- user count is a dash/zero
- generated fields are blank
- runtime/tool checks show `missing` despite a working deployed image

That screenshot is valid only for signed-out-shell layout. Do not use it to make
product claims about authenticated settings or data health.
