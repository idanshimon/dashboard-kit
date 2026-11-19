# Getting a local Next.js build actually SERVED so you can look at it

`npm run build` succeeding is not seeing the page. Between a green build and a
rendered screenshot sit several **repo-structural** traps — properties of the
project's own config, not one-off environment breakage. Each one produces a
launch that dies while something else keeps answering, or a server that never
binds, and all of them read as "the page is broken" if you don't poll the
process.

Verified 2026-08-20 against `agentic-sdlc/apps/ledger-insights-ui`
(Next 16, pnpm workspace, `output: standalone`). Four traps in a single session.

---

## 1. Use the package manager the LOCKFILE names

If `tsc` reports `Cannot find module '<declared dep>'`, check whether the dep is
merely **uninstalled** before believing the type errors are real:

```bash
ls node_modules/<scope>          # missing?
ls pnpm-lock.yaml package-lock.json yarn.lock 2>/dev/null   # who owns this tree?
```

A pnpm workspace (`pnpm-lock.yaml`, no `package-lock.json`) will not
necessarily install with npm. In this repo `npm install` fails outright:

```
npm error Cannot read properties of null (reading 'matches')
```

`pnpm install` succeeds, and afterwards `tsc --noEmit` went from 3 errors to
**0** — the errors were all the missing package. **Match the lockfile before
concluding anything about the code.**

## 2. A `prestart`/`predev` hook can abort your launch on a port you didn't ask for

`npm run start -- --port 3737` ran a `prestart` script
(`node scripts/check-port.cjs`) that checks a **hardcoded** `PORT=3005`,
found it held by an unrelated process, and exited before Next ever started:

```
> PORT=3005 node scripts/check-port.cjs
✗ port 3005 is already in use
```

The `--port` you passed is irrelevant to the hook. Invoke the binary directly
(`npx next start`, or the standalone `server.js`) to bypass it, or free the port
the hook actually checks. Read `package.json`'s `pre*` scripts when a launch
exits instantly.

## 3. `next start` does NOT work with `output: standalone`

It says so and exits:

```
⚠ "next start" does not work with "output: standalone" configuration.
  Use "node .next/standalone/server.js" instead.
```

Check `next.config.*` for `output: "standalone"` before reaching for
`next start`. Note this warning arrives *after* "✓ Ready", so the server looks
like it came up.

## 4. Monorepo standalone output is NESTED — find it, don't assume it

This is the one that most often gets assumed wrong. In a workspace build the
server is **not** at `.next/standalone/server.js`. Next reproduces the workspace
path from the inferred root:

```
.next/standalone/projects/msft/agentic-sdlc/apps/ledger-insights-ui/server.js
```

Guessing the flat path gives `Error: Cannot find module '.../server.js'`.
**Always locate it:**

```bash
find .next/standalone -name server.js -not -path '*/node_modules/*'
```

Depth depends on where Next inferred the workspace root — it warns about this
("We detected multiple lockfiles and selected ... as the root directory"), and a
stray lockfile in `$HOME` will push the nesting deeper than the repo layout
suggests. Never hardcode the depth; always `find`.

`.next/static` and `public` must be copied in **beside that server.js**, not
beside the standalone root, or the page renders unstyled.

---

## Working recipe

```bash
# 0. backend the UI proxies to (this one fails closed without storage settings;
#    dummies are fine for read-only inspection)
STORAGE_ACCOUNT_URL=https://example.invalid COSMOS_ENDPOINT=https://example.invalid \
AUTH_MODE=disabled python -m uvicorn apps.orchestrator.main:app --port 8099 &
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8099/api/<new-route>   # 200, and
                                                                                 # 404 => stale build

# 1. build
pnpm install && npm run build

# 2. serve the standalone output (LOCATE server.js, stage assets beside it)
SA=$(dirname "$(find .next/standalone -name server.js -not -path '*/node_modules/*' | head -1)")
cp -r .next/static "$SA/.next/" ; cp -r public "$SA/"
(cd "$SA" && PORT=3737 HOSTNAME=127.0.0.1 \
   NEXT_PUBLIC_<BACKEND>_URL=http://127.0.0.1:8099 node server.js &)

# 3. confirm, then look
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3737/<route>
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --disable-gpu \
  --no-sandbox --window-size=1600,1400 --virtual-time-budget=9000 \
  --screenshot=/tmp/page.png "http://127.0.0.1:3737/<route>?tab=<tab>"
sips -Z 1200 /tmp/page.png >/dev/null      # budget the vision payload
```

Free a held port between attempts — expect more than one orphan:

```bash
lsof -nP -iTCP:3737 -sTCP:LISTEN -t | xargs -r kill -9
sleep 2; lsof -nP -iTCP:3737 -sTCP:LISTEN -t >/dev/null && echo STILL BOUND || echo FREE
```

**Poll every background launch.** All four traps above presented identically
from the outside (`curl` → `000` or a stale `200`); each was diagnosed in one
`process(action='poll')` showing `status: exited` plus the real error. Do not
infer a server's health from its port.

---

## Verify the DATA PATH, not just the page's 200

A `200` on the route proves the shell rendered. Curl the app's own proxy route
and read the payload to prove browser → proxy → backend → loader end-to-end:

```bash
curl -s http://127.0.0.1:3737/api/<proxy-route> | head -c 400
# {"loaded":true,...,"credential_present":true,"status":"configured","verified":false,...}
```

That one line proved the registry loaded from the real template, that a
present credential still reported `configured` rather than `verified`, and that
the token was absent from the response — none of which the page's status code
says anything about.

---

## `useSearchParams()` breaks `next build` without a Suspense boundary

Any client page putting view-state in the URL (tabs, filters — which most house
styles require) fails **at prerender**, not at type-check:

```
useSearchParams() should be wrapped in a suspense boundary at page "/settings"
Error occurred prerendering page "/settings". Export encountered an error, exiting.
```

`tsc --noEmit` passes clean; only `next build` catches it. Split the component —
the default export becomes a thin wrapper:

```tsx
export default function SettingsPage() {
  return (
    <Suspense fallback={<Card className="p-6 text-sm text-[var(--text-secondary)]">Reading posture…</Card>}>
      <SettingsView />
    </Suspense>
  );
}
function SettingsView() {
  const params = useSearchParams();   // now legal
  ...
}
```

Make the fallback match the page's own loading state so the boundary is
invisible in normal use.
