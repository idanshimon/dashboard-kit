# Operator legibility: what "make it real" actually means

A cluster of corrections that all sound like polish requests but are really the
same complaint: **the screen is technically correct and practically unusable.**
Encode these up front rather than waiting to be told.

## 1. Identifiers are for machines; labels are for people

> "runid is just uuid humans needs more filter or search options"

A `<select>` of raw UUIDs is unusable. Derive a label from what a person actually
remembers about a run — **when, who, how big, what about**:

```
just now  ·  cardiology  ·  2 decisions  ·  phi-classification  —  aaaaaaaa
3d ago    ·  oncology    ·  9 decisions  ·  auth-policy · sla-binding  —  bbbbbbbb
```

Rules that make this work:

- Keep a short id in the label so it stays anchored to the record.
- Strip internal prefixes (`team-cardiology` → `cardiology`) — say it how the
  operator says it.
- Pair the picker with free-text search over a lowercase haystack of
  **id + team + classes + decision text**, so a pasted UUID from a log still
  works alongside "cardiology phi".
- **AND the search terms**, so more words narrow rather than widen.
- When the filter hides the current selection, jump to the first visible option.
  Leaving a stale selection renders a blank canvas that looks like a crash.

## 2. Repetition is a bug, even when every row is correct

Six rows reading "A run is waiting on your decision at resolver" is six correct
rows and one unusable screen. Collapse identical items into one counted row —
"13 runs are waiting on your decision at resolver ×13" — and link it to the
filtered queue.

When collapsing, report the **oldest** member's age, not the newest. A group
labelled "just now" that contains a 22-day-old item is a fresh-looking lie.

## 3. A window that can render zero will eventually lie

`Failed (24h): 0` while 24 runs sat failed was technically true and hid a 48%
failure rate. Prefer a total plus a rate (`24 · 48% of all runs`) over a rolling
window whose empty state is indistinguishable from health.

## 4. Group navigation by the user's verbs, not your architecture

Nobody thinks "I need the Ledger Plane." Group by what they came to do —
Operate / Govern / Analyze / Configure. Internal structure (plane, subsystem,
ownership) can survive as a per-item colour accent; it should not dictate the
menu.

Views over **one dataset** are tabs, not sibling nav entries. Four nav rows named
Table / Map / Lineage / Run flow read as four destinations; as a tab strip under
the page title they read as four lenses on the same thing — and the nav gets four
slots back.

## 5. Mode flags describe DATA posture, not a fake backend

A "demo mode" that short-circuits the real pipeline and replays local fixtures
cannot demonstrate the product. Worse, it silently disables the primary action —
a greyed-out "Start run" button that no amount of typing enables, because the
disabled check was `!text.trim() || busy || demo`.

Correct shape:

- Demo mode = **curated sample inputs + guardrails**. Runs still hit the real
  backend, real gates, real persistence.
- Keep offline fixture replay only as a **fallback when the backend is
  unreachable**, and label it loudly as a recording, never as live telemetry.
- Badge it `DEMO DATA`, not `DEMO MODE` — the distinction is the whole point.
- Verify by submitting a real payload and confirming it reaches a real gate.

## 6. Read destructive-sounding controls before reassuring anyone

When a user asks "is Clear X safe — it shouldn't clear the database, right?",
open the function and answer from the code path. If the label was ambiguous
enough to prompt the question, tighten the label in the same pass:

> "Reset local demo state — clears locally replayed runs from THIS browser only.
> Never touches the ledger, the database, or real runs."

## 7. Theme support is not partial credit

A light theme that inverts surfaces but keeps dark-tuned accents ships a WCAG
failure that is invisible while you work in dark mode. And canvas-rendered
graphs, which cannot resolve CSS variables, stay black on white. See the parent
SKILL.md for the token-resolution hook pattern.

## 8. "Borders blend into the background" — compute the ratio, add a tier

This complaint is measurable, and the fix belongs in the token layer, not in the
component. Read both hex values and compare before picking anything.

Verified 2026-08-18: `--border-default #243042` on `--surface #11161D` is ≈**1.4:1**,
far below the 3:1 a UI boundary needs — which is why three independent screenshot
analyses each reported borders as invisible. The fix was a new semantic tier, not
a nudge to the existing token:

```css
--border-default: #243042;   /* structural, low-emphasis dividers */
--border-strong:  #3A4A61;   /* load-bearing: floating panels, legends, cards over canvas */
```

- **Add a tier; do not brighten the existing token.** `--border-default` is used
  in dozens of low-emphasis places where subtlety is correct. Raising it globally
  trades one legibility complaint for a noisier page everywhere else.
- **Define the counterpart in every theme block in the same edit** (`.light` got
  `#9CA3AF` here), or the token silently resolves to nothing in the theme you
  weren't looking at.
- **Name the tier by ROLE, not appearance.** `--border-strong` ("boundaries that
  must be seen") survives a palette change; `--border-blue-400` does not.

## 9. A decoder ring nobody can reach is the same as no decoder ring

Related to §4's tabs point, and it recurs wherever several views share one
dataset. Multiple graph views each encoded four node kinds and six edge kinds in
colour alone. A grep for `legend` appeared to show one view had a legend and the
others did not — the truth was worse: **three divergent hand-written legends,
each decoding only node colours, none decoding a single edge type**, and the most
complete one sat on a route the nav never linked.

- **Grep case-insensitively and for the markup, not the word.** The two "missing"
  legends were unlabelled `<div>`s; a `grep -ril legend` missed them and produced
  a confidently wrong diagnosis in a written audit.
- **Generate the legend from the same table the renderer styles from**, so it
  cannot drift. A hand-maintained legend is wrong the first time someone changes
  an edge colour.
- **Every view that encodes meaning in colour needs the key on it** — not on a
  sibling route, and not only on the one view that happened to get attention.
