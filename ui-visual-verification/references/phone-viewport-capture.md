# Phone-viewport capture and overflow proof

Use when a page must work on a phone (the user often checks from the phone first).

## Procedure
1. **Never trust headless Chrome `--window-size=390,...` for phone proof.** Desktop headless clamps the window to ~500 CSS px, so the page lays out at 500 and the 390 screenshot shows fake right-edge clipping. Check with `--dump-dom "data:text/html,<script>document.write(innerWidth)</script>"` if in doubt.
2. **Emulate in a persistent CDP session** (browser_exec with a named `session`): `cdp('Emulation.setDeviceMetricsOverride', width=390, height=844, deviceScaleFactor=3, mobile=True)`, then navigate. Stateless one-shot CDP calls drop the override between calls.
3. **Prove no horizontal overflow numerically** before looking at pixels: `innerWidth` vs `document.documentElement.scrollWidth`, then list elements whose `getBoundingClientRect().right > innerWidth` that are not inside an `overflow-x:auto|hidden` ancestor (skip off-canvas drawers).
4. **Capture every screen top to bottom**: loop `scrollTo(0, y)` in steps of the viewport height and copy each `capture_screenshot()` to its own file (the helper overwrites one path).
5. **Review each screen with vision** asking for real bugs only (clipping, overlap, broken data text like stray `}`/`?`, dangling separators), then fix and re-shoot. Repeat in light AND dark theme.

## Fix patterns that hold up
- Grid/flex children need `min-width:0`; wide tables and charts go inside their own `overflow-x:auto` wrapper with a visible "swipe" hint, and get a compact phone summary list above them.
- Stack label/value/bar vertically on phones instead of three squeezed columns.
- Hide desktop-only controls (density, lane filters, long sub-identifiers) under 700px; keep tap targets >= 36px.
- Keep `·` separators glued to the preceding word (`\u00a0· `) so a wrap never starts a line with one; use `text-wrap: pretty` on prose.
- Strip label prefixes from status text only with a plain-word regex (`^[A-Za-z][A-Za-z &/+.()-]{1,40}:\s+`); a greedy `^[^:]*:` cuts inside data like `{'succeeded': 1}` and leaves `2}`.
- Hide panels that are empty on this host instead of showing the same empty message twice.
