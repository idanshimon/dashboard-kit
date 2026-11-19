# Vision Payload Budget — why a verification loop 413s its own session

Worked case: a UI verification pass on a 7-tab single-file HTML explainer killed
its own session with `Request payload too large (413). Cannot compress further.`

## The mechanism

Two different units are being compared, and nobody reconciles them.

| Layer | Unit it measures |
|---|---|
| Provider gateway (Copilot, others) | **serialized HTTP body bytes** |
| Agent-side context estimator | **tokens**, approximated as `len(text_content) / 4` |

A native-vision tool result is a multimodal envelope:

```json
{
  "_multimodal": true,
  "content": [
    {"type": "text",      "text": "Image loaded into your context..."},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
  ],
  "text_summary": "Image attached natively (412.3 KB)."
}
```

The transcript store persists only the **text placeholder** in the `content`
column. The base64 lives in a separate `api_content` sidecar, which frequently
reads 0 bytes for these rows.

Consequence: a session that is 505 KB of text on disk can be sending 4 MB over
the wire. The estimator sees ~505 KB and reports plenty of headroom. The gateway
sees 4 MB and returns 413.

## Why the retry loop cannot recover

The typical 413 handler:

1. Runs text compaction.
2. Re-estimates tokens (still text-only, so barely moves).
3. Gates the retry on a minimum reduction, e.g. `new < original * 0.95`.
4. Falls through to a last-resort "strip image parts from tool messages".
5. If that reports nothing stripped, goes terminal.

Steps 1-3 are compressing the wrong substance. Step 4 is the only mechanism that
could help, and it mutates the *prepared request array*, which is typically
rebuilt from the canonical message list at the top of the retry loop — so the
strip can be discarded before the next attempt. Net effect: every retry sends a
body of the same size and fails identically.

Observed symptom shape: heavy compaction visibly succeeded (most rows marked
`compacted=1`, `[CONTEXT COMPACTION — REFERENCE ONLY]` markers present) and the
session still 413'd. **Compaction succeeding and the 413 persisting is the
signature of an image-bytes problem, not a context-length problem.**

## Diagnosing it

Find which session and confirm images are the cause. Against a Hermes-style
SQLite transcript store:

```bash
# Total on-disk size vs message count
sqlite3 state.db "select count(*), sum(length(coalesce(api_content,content)))/1024 kb
                  from messages where session_id='<SID>';"

# Did compaction already run? (many compacted=1 rows + still 413 => images)
sqlite3 state.db "select active, compacted, count(*) from messages
                  where session_id='<SID>' group by active, compacted;"

# Count vision calls and recover the image paths from the tool_calls column
sqlite3 state.db "select id, tool_name, substr(content,1,120) from messages
                  where session_id='<SID>' and tool_name='vision_analyze';"
sqlite3 state.db "select substr(tool_calls,1,300) from messages
                  where session_id='<SID>' and tool_calls like '%vision_analyze%';"
```

Then size the real files:

```bash
ls -la /tmp/<prefix>_*.png
du -ch /tmp/<prefix>_*.png | tail -1
```

Rule of thumb: **>1.5 MB of PNG in one session is the danger zone**; base64 adds
~33% on top.

Key tell: `length(api_content)` reads 0 for the vision rows while the on-disk
PNGs are hundreds of KB each. That gap *is* the bug.

## Prevention

### Best option: delegate the screenshot+vision round-trip

**A subagent's images never enter your context at all.** It captures, looks, and
returns prose. You pay ~30 lines of text for a verdict that would otherwise cost
megabytes of base64 — and you can then run the loop five times in one session
instead of the one round the budget rules below allow.

```
delegate_task(
  goal="Screenshot <urls> with headless Chrome and visually verify <specific fix>. "
       "TEXT ONLY, max 25 lines. No base64, no HTML dumps. "
       "End with one line: is <X> CONFIRMED WORKING or STILL BROKEN?",
  context="Dev server ALREADY RUNNING at <url> — do NOT start one. "
          "Use --virtual-time-budget=12000; graphs need time to lay out. "
          "You must actually look at the images with vision_analyze — "
          "do not infer from the DOM or source.")
```

What separates a useful verdict from agreeable noise (verified 2026-08-18 across
five delegated passes on one UI):

- **Demand a binary verdict line.** "CONFIRMED WORKING or STILL BROKEN" resists
  the hedging vision models default to.
- **Quote the prior complaint verbatim** in the context ("previous review said
  nodes clustered in the right third"). The subagent then reports a *delta*
  rather than a fresh opinion — which is what tells you whether the fix moved.
- **Ask for percentages, not adjectives.** "Estimate what % of the panel is empty
  on the left and right" produced a measurable progression (55% → 30% → 5%)
  including the point where it was good enough to stop tuning.
- **Say "do NOT start a dev server."** Otherwise it starts a second one, hits the
  port conflict, and cheerfully verifies whatever was already listening.
- **Cap the line count and forbid base64/HTML in the goal itself**, or a
  truncated summary eats the budget you delegated to save.

Read the verdict from the saved summary file
(`~/.hermes/cache/delegation/subagent-summary-*`), not the live transcript — the
transcript truncates mid-verdict.

**Stale batches:** an async batch landing after you already fixed what it
inspected is reporting on a build that no longer exists. Check its dispatch
timestamp against your last edit before acting, and say so rather than re-fixing
a closed defect.

### If you must look yourself

```bash
sips -Z 1200 /tmp/*.png        # macOS, in place
```

Full-page retina captures run 320-450 KB each; at 1200px they land near 100 KB
and every defect this skill hunts for is still legible. Also: one verification
round per session, capture regions rather than full pages, and `/new` between
rounds.

## Do not expect an agent update to fix this

Checked directly on a Hermes checkout 3,256 commits behind `origin/main`: the
`* 0.95` retry gate, the image-strip fallback, and the terminal error string
were all **byte-identical** on main, and there was still no preflight
serialized-byte check anywhere in the agent path. The known issue proposing a
looser gate was open and unmerged.

Generalizable lesson: before recommending "just update", diff the specific
functions on the remote branch. An update being *available* is not evidence it
contains the fix. This same measurement gap is reported across every client that
talks to the Copilot gateway (VS Code, Visual Studio, third-party CLIs), which
is itself a signal that the fix is not sitting in any one client's changelog.
