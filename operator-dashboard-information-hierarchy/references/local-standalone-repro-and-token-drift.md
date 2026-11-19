# Local standalone repro + design-token drift audit

Mechanical recipes supporting the main skill. Next.js/monorepo specific, but the
*shape* generalizes to any "run the real build locally against live backends."

## Running a monorepo Next.js standalone build locally

### The path trap

Building from the **monorepo root** puts the server at:

```
.next/standalone/server.js          ← correct
.next/standalone/apps/<app>/server.js   ← does NOT exist; guessing this yields MODULE_NOT_FOUND
```

Never assume the nested path mirrors the source tree. Always:

```bash
find .next/standalone -maxdepth 3 -name server.js
```

### Assets must be staged INTO the standalone tree

`next build` does not copy static assets into `standalone/`. Skip this and every
`_next/static/*` 404s — the page renders completely unstyled, which looks like a
CSS bug and is not.

```bash
mkdir -p .next/standalone/.next
cp -r .next/static .next/standalone/.next/
cp -r public .next/standalone/
```

### Run against LIVE backends so real render paths execute

The whole point is to exercise code paths that only run when real data arrives.
A local server with no backend auth returns 401, the query fails, the page shows
its empty state, and **the interesting render path never executes** — you learn
nothing. Pass real credentials:

```bash
HOSTNAME=127.0.0.1 PORT=3012 \
  API_URL=https://<live-backend> \
  SOME_TOKEN="$(fetch-from-secret-store)" \
  node .next/standalone/server.js
```

Read the token from the deployment's secret store rather than asking for it or
hardcoding it. Then treat commit time as a secret exercise: grep every changed
file for the token value before staging.

Launch it as a genuine background process (a long-lived server), then health-check
in a separate call — do not shell-background it inside a foreground command.

### Screenshotting localhost

Agent browser tools commonly block localhost/private IPs via an SSRF guard.
Don't fight it — use headless Chrome:

```bash
C="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$C" --headless --disable-gpu --no-sandbox --window-size=1600,1200 \
  --virtual-time-budget=18000 --screenshot=/tmp/shot.png "http://127.0.0.1:3012/"
```

Byte-size triage: ~17KB = framework error screen; >150KB = real content.
Check the size before spending a `vision_analyze` call.

### Build-time-inlined env vars do not respond to runtime flags

Framework public env vars (`NEXT_PUBLIC_*` and equivalents) are **inlined at
build time**. Setting one when *launching* the server changes nothing — a
"DEMO MODE" badge will keep showing even with the flag set to 0 at runtime,
because the value was frozen into the bundle. If a mode flag looks stuck, check
whether it was passed to the *build*, not the run. Flag this before any deploy
so the live stack doesn't silently regress into demo behavior.

## Design-token drift audit

Run when touching UI tokens, or as part of any "does the UI match its spec" pass.

```bash
grep -rEo "#[0-9A-Fa-f]{6}" src --include=*.tsx | sort | uniq -c | sort -rn
grep -rEo "#[0-9A-Fa-f]{6}" src --include=*.tsx -l    # which files
```

Triage the hits into three groups:

1. **Canvas-library hits (legitimate).** Cytoscape.js / react-flow style through
   a JS stylesheet drawn to `<canvas>`, which *cannot* resolve CSS custom
   properties. These files must hard-code hex. This is a real exception — but it
   MUST be written into the design spec as a named exception, with the rule that
   the values mirror the token block verbatim. Otherwise a palette change
   silently leaves those pages on the old theme.
2. **Invented values (violations).** A hex with no counterpart in the token set
   is drift even inside a canvas file. Flag by name.
3. **Ordinary component hits (violations).** A repeated literal is a missing
   token. Add it (`--on-primary`), swap every call site, and add a Don't line to
   the spec so it doesn't come back.

### Linter false positives on token-driven codebases

`npx -y @google/design.md lint DESIGN.md` (and similar) inspect only the
declared `components:` block. Tokens consumed as `bg-[var(--warning)]/15` in
Tailwind arbitrary values are invisible to them, producing a pile of
*"'x' is defined but never referenced by any component"* warnings.

**These are false positives. Do not delete those tokens.** Judge the lint by its
error count; read the warnings for real signal (broken references, duplicate
sections, WCAG contrast) and ignore the unused-token class.

## Verification ladder that actually caught things

In strict order, cheapest first — each catches a class the previous one cannot:

1. `tsc --noEmit`
2. full test suite (not just the new file — this is the regression check)
3. production build — catches prerender failures (e.g. `useSearchParams` outside
   `Suspense`) that both type-check and unit tests pass cleanly
4. design-spec lint, when tokens changed
5. **standalone server + headless screenshot + `vision_analyze`**
6. re-screenshot after fixing

Steps 1–4 were all green in a real session while two serious legibility defects
were live on screen. Step 5 is where product defects surface.
