# The page can be 100% structurally valid and 100% dead

Verified the hard way 2026-08-28 building a single-file dashboard
(`displacement-signals/dashboard/index.html`, ~70KB, vanilla JS, no build step).

## What happened

A patch to a chart-colour map matched the wrong block and deleted a single line —
the `const KC={` declaration — leaving a bare object literal in the middle of the
script:

```js
  A.forEach(a=>a.anomalies.forEach(x=>kinds[x.kind]=(kinds[x.kind]||0)+1));
  seat_churn:'var(--bad)',consumption_anomaly:'var(--warn)',   // <- orphaned
```

One `SyntaxError: Unexpected token ':'` at parse time meant **the entire script
never executed**. No render, no data, no event handlers. The page served 200 and
showed its static skeleton, so it looked like a styling problem, not a fatal one.

**It was reported as "verified" three separate times before anyone looked at it.**

## Why every check passed

These all passed while the page was dead, because **none of them execute JS**:

| Check | Why it passed |
|---|---|
| HTMLParser tag balance | markup was fine; the bug was inside `<script>` |
| every `getElementById('x')` has a matching `id="x"` | ids existed, they were just never filled |
| every called function is defined | definitions existed, they were never reached |
| `curl -w %{http_code}` | server returns 200 for a broken page |
| file size / `</html>` present | irrelevant to runtime |

Static analysis of a document that *contains* a program is not analysis of the
program. This generalises beyond HTML: linting a YAML that embeds a shell script,
tag-checking an SVG with an `onload`, etc.

## The check that actually catches it

One call, sub-second, run **before every reload**:

```js
// in the page context, over CDP or devtools console
(async () => {
  const t = await (await fetch('index.html?x=' + Date.now())).text();
  const js = t.match(/<script>([\s\S]*)<\/script>/)[1];
  try { new Function(js); return 'SYNTAX OK'; }
  catch (e) { return 'SYNTAX ERR: ' + e.message; }
})()
```

`new Function()` parses without executing — safe, and it reports the same error
the browser would. Cache-bust the fetch or you will validate the previous version
and conclude the fix worked.

Prefer this over `node --check`: extracting the script to a temp file and shelling
out to node hung for 120s on a 70KB file in one session, while the in-page check
returned instantly.

## Bisecting to the offending line

The error message carries no line number once the script is inlined. Binary-search
the line count in-page:

```js
const L = js.split('\n');
let lo = 1, hi = L.length;
while (lo < hi) {
  const mid = (lo + hi) >> 1;
  try { new Function(L.slice(0, mid).join('\n')); lo = mid + 1; }
  catch (e) { /Unexpected token/.test(e.message) ? hi = mid : lo = mid + 1; }
}
// hi = first line that cannot parse; print L.slice(hi-4, hi+2) for context
```

Filter on the *specific* error text. Truncating a script mid-function throws
`Unexpected end of input` on almost every prefix, which drowns the real signal.

## Sibling bug: template-literal syntax in static markup

```html
<!-- in the static skeleton, NOT inside a JS template literal -->
<h2>${ex('cls','Risk distribution')}</h2>
```

Renders the literal characters `${ex('cls','Risk distribution')}` to the user.
No error anywhere — it is just text. Silent, and it looks like a data problem.

Sweep for it directly:

```python
body = src[src.index('<body'):src.index('<script>')]
leaks = re.findall(r'\$\{[^}]*\}', body)   # must be empty
```

Fix by giving the element an id and assigning `innerHTML` from JS.

## Add to the standard sweep

After any edit to a single-file HTML artifact, before claiming it works:

1. `new Function(scriptText)` parse check — cache-busted
2. `${...}` leak scan of the static body
3. reload, then assert a **runtime** fact: `window.S && S.data.accounts.length`,
   a rendered KPI value, a non-zero `.ex`/`svg`/`tbody tr` count
4. click every tab and open one drawer/modal, asserting content after each

Step 3 is the one that distinguishes "served" from "working". Pick a value that
can only exist if the script ran.
