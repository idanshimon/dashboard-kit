# When a real browser does and does not defeat a block

Field notes, verified 2026-08-30 while raising scraper coverage from 8.5% to
67% across 40 dealer sites. Complements the bundled `blocked-page-recovery`
skill, whose ladder ends at "real browser as last resort" without saying when
that step actually works.

## The core distinction

A headless browser succeeds for exactly **one** reason — client-side rendering
— and fails against determined bot management. Diagnose which you face before
spending the effort:

| Symptom | Browser fixes it? |
|---|---|
| 200, large body, but the data is absent from the HTML (rendered by React/Vue after load) | **Yes.** This is the browser's actual job. |
| 200 + tiny interstitial body, or 403 on every path including the homepage | **No.** |

### Case that a browser DID fix

DealerOn sites returned 600KB of markup containing **zero dollar amounts**.
VINs shipped in a `dealeron_tagging_data` script block; every price rendered
client-side via Vue. No JSON endpoint existed (`/api/inventory/search`,
`/apis/widget/...`, `?output=json` — all 404). No text parser could ever have
worked. Playwright reading the DOM recovered 7 sites and 233 records.

The tell: `curl` body is *large* and well-formed, but stripping `<script>` tags
leaves none of the values you want.

```bash
# Cheap diagnostic — is the data server-rendered at all?
curl -s "$URL" | sed 's/<script[^>]*>.*//' | grep -c '\$[0-9,]\{4,\}'
# 0 with a 600KB body  =>  client-rendered, browser will help
```

### Case that a browser did NOT fix

Two sites behind **Akamai Bot Manager** returned *Access Denied / 333 bytes /
0 records* through headless Chrome **and** through a headed, real-profile
Chrome window. A cold session with cookie jar, `Referer`, and full `Sec-Ch-Ua`
client hints made no difference.

Do not promise "a real browser will solve this" before testing it. I did, and
had to retract it.

## Bot challenges arrive with HTTP 200

The most dangerous fake success, because every status-code check passes. Akamai
answers with **200** and a ~2.5KB body holding `sec-if-cpt-container` plus an
obfuscated script — no content, no error. A scraper recorded this as
`parse_failure`, i.e. "our parser is broken", when the truth was "we were never
served the page". That misattribution sends you hunting through adapter code
for a bug that does not exist.

```ts
export function isBotChallenge(html: string): boolean {
  if (html.length > 40_000) return false;   // real pages are far larger
  return (
    html.includes("sec-if-cpt-container") ||   // Akamai Bot Manager
    html.includes("_Incapsula_Resource") ||    // Imperva
    html.includes("Just a moment...") ||       // Cloudflare
    /Access Denied/i.test(html)
  );
}
```

Verify both directions: it must flag the 6.8KB challenge **and** not flag a
real 808KB page.

## Check your own headers before concluding "blocked"

A whole tier of "blocked" sites is really "we sent thin headers". Same URL,
403 with `User-Agent` alone, **200** with the full set:

```
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: none
Upgrade-Insecure-Requests: 1
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.9
```

## Enforcement is per-site, not per-platform

Two dealers on the **same platform** behaved differently:

| Host | `ddc_akam_bot` cookie | Result |
|---|---|---|
| A | `BOT-BROWSER-IMPERSONATOR` | served the page |
| B | `BOT-ANOMALY-SCRAPER` | Access Denied |

Never generalize from one host to the platform. Probe each.

## Stop escalating — report unreachable honestly

When the browser fails this way, the honest remedy is residential proxies or a
stealth-patched driver: a different and more invasive class of tooling, and a
**decision for the user**, not a bug to fix. Report the source as genuinely
unreachable rather than leaving it looking like a defect awaiting a patch.

## The rung above "real browser": the USER'S browser over CDP

A freshly-launched automated browser is still an automated browser. The user's
**already-running** Chrome — real profile, real cookies, real history, launched
by a human — is a different lane, and it defeats blocks that beat rungs 1-5.

Verified: `tesla.com` returned Access Denied to curl, headless Chrome, **and**
headed Playwright. The same URL in the user's own Chrome loaded fully — even
personalized to their ZIP — and its computed styles were then readable over
CDP.

```
1. curl / fetch                         cheapest
2. archives / Jina / API pivot
3. headless browser                     defeats client-side rendering
4. headed automated browser
5. USER'S OWN BROWSER over CDP          defeats bot management
```

**Procedure**

```bash
# 1. Open the page in the user's real browser (does not steal focus badly)
open -a "Google Chrome" "https://target.example/page"

# 2. Confirm a CDP endpoint is exposed
curl -s --max-time 5 http://127.0.0.1:9222/json/version
```

Then use the **`browser_cdp` tool**, not a hand-rolled WebSocket client:

- `Target.getTargets` → find the entry whose `type == "page"` and whose `url`
  matches the site; take its `targetId`.
- `Runtime.evaluate` with `target_id` set and `returnByValue: true`.

**Pitfalls, all hit in one session:**

- **A raw `websocket-client` connection is rejected**: `Handshake status 403`,
  "Rejected an incoming WebSocket connection from the http://127.0.0.1:9222
  origin." Chrome enforces an origin check that `browser_cdp` already handles.
  Do not go add `--remote-allow-origins=*` to the user's browser flags.
- **`Target.getTargets` output is huge** (100KB+; every extension service
  worker and tab). It will be persisted to a file rather than returned inline.
  Parse that file for the one page target instead of eyeballing it.
- **Extract in ONE `Runtime.evaluate`.** Each stateless CDP call is
  independent, so a chatty sequence is both slow and fragile. Build a single
  IIFE that returns the whole object.
- The browser tool's own `browser_navigate` may time out on such sites; going
  through the user's already-loaded tab sidesteps that entirely.

Only do this against a page the user asked you to look at, and read state —
don't drive their session around.

## This applies to design reconnaissance too

Reading a well-known site's computed styles to imitate its design is the same
fetch problem, and it has a decisive advantage: the answer is *in the DOM*, so
CDP against the user's browser yields exact values rather than an approximation.

**Design tokens live in CSS custom properties.** Enumerate them instead of
guessing:

```js
const r = getComputedStyle(document.documentElement);
const vars = {};
for (let i = 0; i < r.length; i++) {
  const p = r[i];
  if (p.startsWith("--")) vars[p] = r.getPropertyValue(p).trim();
}
// Tesla exposed 486 `--tds-*` variables this way.
```

Also read `getComputedStyle` on `body`, `h1`, and the primary CTA, plus
`Array.from(document.fonts)` for the real family/weight set.

**Why this matters more than it sounds: designing from memory is reliably
wrong.** Every *structural* guess made about Tesla's current design system was
wrong by a generation:

| Guessed (from memory) | Measured (from TDS) |
|---|---|
| `border-radius: 9999px` (pill) | `4px` |
| `text-transform: uppercase` | `none` |
| `letter-spacing: 0.12em` | `normal` |
| h1 weight 300 (hairline) | weight 500 @ 40px/48px |
| body 16px | 14px |

Brand *colors* survive in memory; brand *geometry and type* do not. Shipping
the guess would have produced a confidently dated pastiche.

If every rung fails, **do not invent measurements and present them as
scraped.** Ask the user for a screenshot (vision reads it fine) or build from
the brand's publicly documented language — and state in the artifact itself
which one you did, so the next reader knows the provenance.

## Playwright operational notes

- **`waitUntil: "networkidle"` never settles** on ad/analytics-heavy pages; it
  just times out. Wait for the real signal instead:
  ```ts
  await page.waitForFunction(() => /\$[\d,]{4,}/.test(document.body.innerText),
                             { timeout: 25000 }).catch(() => {});
  ```
- **Block images/fonts/media** via `page.route` — you want markup, not MBs.
- **Cards lazy-load.** Without scrolling, ~3 of 12 rendered. Scroll in a loop
  with a short wait between.
- **Close the singleton browser** or the process never exits. A "hang" that
  ends in a 500s timeout is usually this, not a slow scrape.
- **`server-only` throws in CLI scripts.** Any module a script drives must not
  import it.
- **`page.evaluate(() => {...})` under `tsx`** throws
  `ReferenceError: __name is not defined` — the transpiler injects a helper
  absent from the browser context. Pass the script as a **plain string**.
- Gate the browser tier behind a flag (`--browser`). It costs seconds per page
  where plain fetch costs milliseconds; most sources do not need it.
