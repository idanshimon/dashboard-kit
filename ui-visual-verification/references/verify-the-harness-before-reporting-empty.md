# Don't report a page "empty" when your EXTRACTION is what's broken

A verification harness has two independent failure surfaces, exactly like an
alerting system:

1. **The page** — did the server render real content?
2. **Your reading of it** — did your curl/sed/regex pipeline preserve it?

Failure (2) is indistinguishable from failure (1) at a glance, and it produces
the most damaging kind of false report: telling the user their working app is
broken. Doing that costs their trust and sends them debugging a non-bug.

Happened twice in one session, on the same app, before catching it.

## The specific trap: naive tag-stripping on a React/Next page

```bash
# WRONG -- returned an empty string on a fully working page
curl -s "$URL/listings" | sed 's/<script[^>]*>.*$//' | sed 's/<[^>]*>/ /g'
```

`sed` is line-oriented and greedy. On a Next.js page the entire RSC payload and
inlined scripts frequently sit on **one enormous line** with the real markup, so
`s/<script[^>]*>.*$//` deletes the rest of the document — including the content
you were looking for. A second variant swallowed everything after the first tag.

The page was fine. `size_download` proved it:

```bash
curl -s -o /dev/null -w "http=%{http_code} size=%{size_download}\n" "$URL/listings"
# http=200 size=201225      <- 201 KB is not an empty page
```

## Cheap tell before you believe an empty result

**Check the byte size first.** It costs one flag and instantly separates the two
failure modes:

| Observation | Meaning |
|---|---|
| `size` large, your extract empty | **your pipeline is broken** |
| `size` small (a few KB) + shell only | genuinely empty view |
| `http` 3xx/4xx/5xx | not an empty-view problem at all |

## Working extraction

Use a real parse in Python, stripping `<script>`/`<style>` with `re.S` so it
crosses newlines, then unescape entities:

```python
import re, html
h = open('/tmp/page.html').read()
h = re.sub(r'<script.*?</script>', '', h, flags=re.S)
h = re.sub(r'<style.*?</style>',  '', h, flags=re.S)
t = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', h)))
print(t[:1500])
```

This turned "empty page" into the actual rendered content — facet counts, VINs,
dealer names, and the app's own honest empty-state copy.

Better still when the goal is *seeing* the page: screenshot it and look, rather
than reasoning about extracted text at all. Text extraction is for asserting on
specific strings in a script, not for judging whether a UI works.

## The same class of error, other forms

- **Port collision** — you curl `localhost:3000` and get a *different app's*
  HTML because that port belongs to something else. Confirm the response body
  is yours before drawing conclusions (`EADDRINUSE` in the server log is the
  giveaway; poll the process).
- **Grepping for a string the framework renders differently** — entity-encoded
  (`&amp;`), split across elements, or client-rendered after hydration so it is
  absent from the initial HTML.

## Reporting rule

If you already told the user something was broken and then discover your
harness caused it, **correct it explicitly and plainly** — "I was wrong earlier,
that was my extraction, not your app." Do not let a false finding stand
uncorrected, and do not bury the correction in a summary. An uncorrected false
alarm is worse than never having checked.

## Verification

- [ ] `size_download` (or content length) checked before believing any empty
      extraction result.
- [ ] Script/style stripping done with a multiline-aware parse, not line-oriented
      `sed`, on framework-rendered pages.
- [ ] Response confirmed to belong to the app under test (right port, right
      title) before reporting a defect.
- [ ] Any earlier false "it's broken" claim retracted in plain language.
