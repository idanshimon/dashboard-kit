# Verifying a LIVE surface: proving data moves, not just renders

Most UI verification asks *"does this render correctly?"* — a screenshot answers it.
A live surface (SSE stream, websocket feed, polling dashboard, ticker, real-time
chart) needs a second, harder question: **does it CHANGE?**

A screenshot cannot answer that. One frame of a frozen feed and one frame of a
healthy feed are pixel-identical. This is the failure mode the whole class exists
to catch — and it is the one users notice fastest, because a dashboard that quietly
stopped updating still looks authoritative.

Verified 2026-09-03.

## The two claims, and why they need different proof

| Claim | Proof |
|---|---|
| "The page renders" | Screenshot, DOM measurement, HTTP 200 |
| "The data is live" | **Two or more samples, compared, differing** |

A single sample can never establish movement. Capture N frames, extract the same
field from each, and assert the set of distinct values is greater than one. That
assertion is the entire point:

```
frames: 9  distinct scores: 9  -> MOVING
frames: 9  distinct scores: 1  -> STATIC (this is the bug)
```

## Prefer an in-repo integration test over a throwaway harness

The instinct is to write a quick script in `/tmp` that loads the page and pokes it.
Resist it. **Write the check as a test inside the repo instead.**

Why it wins on every axis:

- It runs in CI forever, instead of proving the point once and evaporating
- It fails loudly when someone renames a wire field months later
- Reviewers can read it; a `/tmp` script is invisible in the PR
- No headless-browser stack to fight

Verified: a jsdom+EventSource harness in `/tmp` burned several attempts — it wrote
the framework bundle straight to the process file descriptor, so redirection and
virtual-console suppression both failed to isolate the assertions, and it exited
nonzero with no diagnostics. Replacing it with a vitest file in the repo produced a
passing, readable, permanent check in one pass. **When a throwaway harness needs a
second debugging round, stop and move the check into the repo.**

## Test against the REAL server — mocking the transport proves nothing

Mocking `EventSource` or `WebSocket` only demonstrates that the component
re-renders when handed data, which was never in doubt. The failure this class of
test must catch is a **contract mismatch between two shipped artifacts**: the
client's parser and the server's emitter, drifting apart.

So point the test at a running server and read the actual bytes.

Reading SSE frames with plain `fetch` — no `EventSource`, works under any test
runner:

```ts
async function readFrames(count: number, timeoutMs = 20000) {
  const res = await fetch(`${BASE}/api/stream`, { signal: AbortSignal.timeout(timeoutMs) });
  const reader = res.body!.getReader();
  const dec = new TextDecoder();
  const frames: any[] = [];
  let buf = "";
  while (frames.length < count) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i: number;
    while ((i = buf.indexOf("\n\n")) !== -1) {           // frames end on a blank line
      const chunk = buf.slice(0, i); buf = buf.slice(i + 2);
      const line = chunk.split("\n").find(l => l.startsWith("data: "));
      if (chunk.includes("event: cohort") && line) frames.push(JSON.parse(line.slice(6)));
    }
  }
  await reader.cancel().catch(() => {});
  return frames;
}
```

## What to assert (four tests, not one)

1. **Health/shape** — the endpoint the header renders from returns what it claims.
2. **Every field the UI destructures exists on the wire.** Loop the field names
   explicitly with a message naming the missing one. A renamed field here is a
   blank column there, and a blank column is the hardest defect to trace back.
   ```ts
   for (const k of ["id", "score", "stage", "criteriaMet"])
     expect(row, `row is missing '${k}'`).toHaveProperty(k);
   ```
3. **It MOVES** — `expect(new Set(series).size).toBeGreaterThan(1)`.
4. **State machines actually block.** If the flow has a gate, assert the negative:
   no step past the gate exists before approval, and the post-gate step is
   attributed to whoever released it. Asserting only that approval *works* would
   pass on a system with no gate at all.

## Skip loudly when the dependency is absent — never fail, never silently pass

An integration test that needs a live server must not redden CI on a machine that
isn't running one, and must not quietly no-op either.

```ts
beforeAll(async () => {
  reachable = Boolean(await health());
  if (!reachable) console.warn(
    `\n  SKIPPING live tests: no server at ${BASE}.` +
    `\n  Start it with: <the exact command>\n`);
});

it("MOVES", async () => { if (!reachable) return; /* ... */ });
```

The warning must contain **the exact command to start the dependency**. "Skipped"
with no remedy trains people to ignore skips. Verify both paths before committing:
point the base URL at a dead port and confirm it skips cleanly, then at the live
one and confirm it actually asserts.

## Conditional UI is correctly ABSENT from static HTML

When grepping a built page for expected strings, text inside data-conditional
branches will be missing — correctly. A row rendered per live record, or a gate
banner shown only while awaiting approval, cannot appear in prerendered output
because no data has arrived.

Verified: a build check reported `FOUND` for static chrome ("Watch list",
"Consumption") and `MISSING` for two conditional strings. Neither was a defect.

**Do not chase these as bugs, and do not treat their absence as proof either.**
Split the check: grep the static shell for chrome, and let the live test prove the
conditional branches.

## Pitfalls

- **A single sample cannot prove liveness.** Two identical frames may mean a frozen
  feed; you need distinct values across N samples.
- **A stale background job's output can arrive later and look like a current
  result.** When a long-running build/test completes after you've already moved on,
  its numbers describe an earlier tree. Check the timestamp and the counts against
  what you last ran before quoting it.
- **Don't seed the client with fake movement.** If the surface has no feed yet, say
  so; animating placeholder numbers is worse than an honest empty state.
- **An offline feed must SAY it is offline.** A dashboard that freezes on its last
  values still looks live and authoritative. Render a connection state, and put the
  start command in the offline message.

## Acceptance

- [ ] Movement asserted from ≥3 samples with distinct values — never one screenshot
- [ ] The check lives in the repo and runs in CI, not in `/tmp`
- [ ] Test hits a REAL server; transport not mocked
- [ ] Every field the UI reads is asserted present on the wire, by name
- [ ] Gates asserted negatively (nothing past the gate exists before release)
- [ ] Skip path verified against a dead port, and the skip message names the exact
      start command
- [ ] Conditional-UI strings checked via the live test, not by grepping static HTML
