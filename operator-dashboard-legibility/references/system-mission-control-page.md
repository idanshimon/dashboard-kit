# System mission-control page (pipeline + autonomous SDLC cockpit)

For an operator console that unifies a scheduled data pipeline (sources → scheduler → jobs → repo data → release gate → live site) with an autonomous agentic SDLC loop (detect/retry → triage → memory recall → coding agent → policy gate → owner gate → live verify). The user rejects plain lanes-of-boxes diagrams and split multi-page status views; unify real-time telemetry, in-place decisions, and system explainability on one root cockpit while keeping deep subviews one click away.

## Layout, top to bottom
1. **Verdict hero + coverage meter + 4 chart-bearing KPI tiles**:
   - One sentence naming human decisions needed + user-visible impact (`N decisions need you · site is behind repo`), counting blockers and warnings separately.
   - Reconciled host-watched health bar: when local-only/unmonitored nodes are excluded from the numerator (`ok / hostWatched`), divide bar segment widths by `hostWatched` rather than `nodes.length` so the visual fill matches the printed fraction without an unexplained empty gap.
   - 4 navigational KPI tiles (autonomy/queue ratio, public site vs repo parity, scheduled slot on-time %, 14d release pass rate), each carrying an SVG bar or sparkline and scrolling/opening its detailed section on click. Use proportional sans with `font-variant-numeric: tabular-nums` on multi-word KPI values (`4 need you`, `Behind repo`) — full monospace creates wide inter-word gaps on narrow cards.
2. **Split Decision & Autonomy Console**:
   - **Left — Needs Your Decision**: ranked triage questions ahead of gate-escalated PRs, newest-first within each band. Render generic option labels with their concise effect (`★ Option A — <summary>`) on primary choice buttons, keep auxiliary links (`Evidence & timeline`, `Issue ↗`, `PR ↗`) on a separate row below, and wire inline confirmation + note submission directly to the write-dispatch endpoint (`POST /owner/decide`) while preserving focused inputs during SSE ticks.
   - **Right — Agent Decisions & Loop State**: tabs for `Coding & Verify` (active agent PRs + gate-merged PRs awaiting live release verification, with a causal callout when a failing release stage blocks verification), `Home Brain` (watcher auto-reruns and gate dispatches from the mounted agent ledger), and `Done & Feed`.
3. **Dual-Loop Cybernetic Circuit + Hover Mental-Model ("Dreamlens")**:
   - **Track A**: production pipeline stage columns (Sources → Scheduler → Runner Jobs → Repo Data → Release Gate → Public Site), clickable into an evidence drawer.
   - **Synaptic Bridge Rails**: explicit connectors between bands (`Track A → B1` failure + 1× auto-retry routing; `Memory ↔ B2–B5` scoped `D-NN`/`L-NN` recall + mandatory PR citation gate; `B6–B7 → Track A` owner answers minting `D-NN` precedents + live SWA verification).
   - **Neural Memory Spine**: active `D-NN` decisions, `L-NN` lessons, auto-with-notice precedents, and hard STOP/forbidden-path guards.
   - **Track B**: 7-beat SDLC loop (`Detect & Retry → Triage → Memory Recall → Copilot Fix → Policy Gate → Owner Gate → Verify & Learn`) with live issue/PR tokens docked on their current beat.
   - **Hover/focus Dreamlens**: hovering or keyboard-focusing any node, rule chip, bridge, beat, or KPI fades in a floating card explaining what it does right now, live evidence bullets, and upstream/downstream links while illuminating connected `[data-link-key]` elements across the board. Anchor strictly above or below the trigger's `getBoundingClientRect()` (never covering the hovered target) and cap summary prose at ~230 chars on a clean boundary (`Click for full record` opens the drawer).
4. **"Did jobs run when they should?" swimlanes** — the single most useful operational chart:
   - expected slots computed server-side from the scheduler config + market calendar;
   - actual runs shaped by trigger (platform ◆, cron ●, manual ▲), failures hollow red;
   - match each slot to the first unused run of the same workflow in `[slot-3m, next slot)`;
     >15 min = late (draw a line slot→run), none = never ran;
   - cluster runs closer than ~12px into one mark with a `×N` badge (worst result wins);
   - when a lane has too many slots to draw (<14px each), draw only the misses;
   - leave a right margin (~56 of 1460 viewBox units) so the "now" band is not clipped, and suppress the day's `open` header label when `X(now) - X(open) < 145px` so `"Wed, Nov 11 · open"` never collides with `"now"` on the top axis.
5. **14-day production release chart + Freshness vs SLA + Searchable Memory Vault + Strategy strip**:
   - Exclude PR previews and superseded cancellations from production release pass-rate bars; print run count above each bar, 0/50/100% Y-axis gridlines, and 7d failed-stage breakdown (`prepare: N`) below.
   - Freshness bullets (age vs market-hours/after-hours SLA), recent Brain slot ledger, filterable `D-NN`/`L-NN` memory cards, and L3-locked paper-trader summary.

## Parser, telemetry & deploy pitfalls
- **Match all active LLM comment heading variants when deriving queues.** Prompt revisions (e.g. `**What I need from you:**` → `**Decision for you**`) silently drop live escalations from regex/substring extractors while leaving issues open. Normalize headings and test the projection against real exported issue comments before trusting queue counts.
- **Color header stream pills by telemetry freshness, not downstream job failures.** Painting the `stream` or `loop` pill red because a monitored pipeline job failed makes operators think SSE collection itself is broken. Use green/amber/red on stream pills strictly for collector/export age, and keep pipeline failures in the verdict and node cards.
- **Strip trailing periods/ellipses before truncating parsed text.** Upstream builders often cap strings with `...`; slicing again and appending `…` renders `....` unless trailing `[.…]+` is stripped first.
- **Mount sibling watcher state read-only (`:ro`) into the console container.** Without mounting the autonomous watcher's state volume (e.g. `/var/lib/bt-agent`), auto-retry counts and active failure episodes remain invisible on the UI.
- **Volume-cached projections outrank image-baked fallbacks on redeploy.** When the server serves `/var/cache/...` ahead of `/app/...`, rebuilding the container image still serves pre-edit HTML and JSON until the background refresher finishes its next cycle. Whenever generator templates (`styles.py`, `pipeline_control.py`, `mission_control.py`, `data_story.py`) or spec builders change, re-bake from the warm cache and copy the rendered views into `/var/cache/.../views/` inside the container (or trigger an immediate refresh) and verify the live HTTPS response carries the new markup/fields.

## Display text hygiene (node summaries, cards)
- Strip a "Label: " prefix only with a plain-word pattern
  (`/^[A-Za-z][A-Za-z &\/+.()-]{1,40}:\s+/`). A greedy `^[^:]*:` cuts inside data such as a
  dict repr and leaves junk like `2}` on screen.
- Never render `?` placeholders: say what is true ("run log not on this host") and give that
  node `unknown` status, not `warn` — a missing local source is not a fault.
- Format money with the sign before the currency (`−$1,930`), and don't repeat the node's
  label inside its own detail line.
- Glue `·` separators to the preceding word with a no-break space so a wrap never starts a
  line with `·`; add `text-wrap: pretty` to paragraphs and captions.

## Phone layout (≤700px)
- Every grid child gets `min-width:0`; wide tables/charts live in their own
  `overflow-x:auto` wrapper (chart `min-width` ~880px with a "swipe →" hint).
- Lead the schedule section with a per-job summary list (name · on time/late/missed · small
  stacked bar); the full timeline is secondary on phones.
- Pipeline → one column; header compact (theme/range only, 36px+ tap targets, hide density
  and lane filters); freshness rows stacked (label + value line, bar below); hide long
  slot-key sublines in the run log; keep ledger keys `nowrap` at 11px.
- **Verify at a real 390px viewport.** Headless Chrome on macOS clamps `--window-size` to a
  500px minimum, so its "390px" screenshots show false clipping. Use a persistent browser
  session with `Emulation.setDeviceMetricsOverride(width=390, mobile=true)` (it resets on a
  stateless CDP call), assert `document.documentElement.scrollWidth == innerWidth`, then
  capture each scroll position to its own file and vision-review per screen in both themes.

## Mechanics
- Server collects every 60s in a thread; SSE push; `POST /api/refresh` wakes the loop
  (rate-limit ~10s); `/healthz` fails when the snapshot is >3 periods old. Report unreadable
  sources as alerts — never a fake green.
- Hand-rolled SVG, no chart lib, CSP `script-src 'self'` with JS in separate files.
- **Themes**: put every colour in CSS variables (`[data-theme=light]` overrides), and have
  charts and 2D canvases read them via `getComputedStyle` at each render — SVG presentation
  attributes and `<canvas>` strokes do not resolve `var()`. Across multi-screen suites, align
  every vendored renderer's native palette (`styles.py` `NATIVE` + `SEMANTIC`) 1:1 with the
  cockpit's Dark and Light tokens instead of leaving sub-routes on a generator default (such as
  a warm-beige preset), and enforce WCAG AA (`>= 7.0:1` primary ink, `>= 4.5:1` muted/accent on
  every surface) in a unit test. Inject a synchronous pre-paint `<head>` script resolving
  `?theme=dark|light|auto` → shared `localStorage` key → OS preference before stylesheets paint,
  render a single `Dark / Light / Auto` segmented pill in the shared top nav with a solid accent
  fill + white text on `[aria-pressed="true"]`, dispatch a `CustomEvent` on switch (forwarded to
  same-origin iframes), and suppress per-page theme buttons under `body:has(> .mc-nav)` so no
  route shows two theme toggles. Light theme needs darkened secondary slate tokens (`#334155` /
  `#475569`) so muted metadata and grid labels stay crisp on white cards.
- **Controls** (range, theme dark/light/auto, density, live/pause, refresh, lane filters)
  persist in localStorage; apply `?theme=&range=` query params BEFORE initialising the
  segmented controls, or the toolbar shows the wrong selected state.
- Missing optional deps (e.g. PyYAML for the schedule file) must raise into `source_errors`,
  not return an empty list — an empty expected-slots list silently renders "0/0".
- Clamp heartbeat ages at 0: small clock skew between containers renders negative ages.
- Keep the rejected version at `/v1` when redesigning.
- When asked how the page stays current, answer with: collection interval, push mechanism,
  reconnect, self-health, which host runs it and whether that process survives restarts.

## LAN / remote exposure on a Windows + WSL2 + Docker Desktop host
- Separate bind vars per service: read-only page on `0.0.0.0`, admin UIs stay `127.0.0.1`
  until they have their own auth. SSH `-L` tunnels are the zero-change way to reach them.
- Windows firewall from WSL: call PowerShell by full path
  (`/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe`) and scope the rule
  `-RemoteAddress <lan>/24`.
- If one phone browser fails while another works on the same LAN, the server is fine —
  it is that browser (HTTPS-only mode, managed profile, VPN). Prove with a second client.
- A site's existing certificate cannot be reused for a LAN host (no private key, different
  name). Run `dig +short NS <zone>` before planning DNS work — the registrar's API is useless
  when the zone is hosted elsewhere (e.g. Cloudflare).
- **Cloudflare Tunnel without an API token**: `cloudflared tunnel login` prints an authorize
  URL the user can approve from their phone; then `tunnel create` + `tunnel route dns`.
  In compose: reference the tunnel by **UUID** (by name needs the account cert inside the
  container), mount the credentials JSON from the secrets dir, and run as the host uid so
  the 0600 file is readable.
- That login does not grant Access policies, so gate in the app: requests with
  `Cf-Connecting-IP` are allowed only from the home public IP (refreshed every ~10 min) or
  with a password file; otherwise 401/403, fail closed. Direct LAN requests (no header) pass.
  Verify with an off-network fetch (must fail) and a spoofed header (must be refused).
