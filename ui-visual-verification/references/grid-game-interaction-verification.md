# Grid-game verification

For retro Minesweeper and other browser grid games:

- Separate a pure immutable game engine from React presentation. Inject a seeded PRNG into board creation; arm the board only on first reveal and exclude its neighbors. Derive scores from revealed state so repeat reveals cannot award twice.
- Test every first-click index on every difficulty against hazard count, protected zone and clue consistency. Test correct/incorrect chording, flagged safe cells blocking flood-fill, exact helper counts, terminal freezes and hints.
- Use the real seeded engine as the browser-test oracle. Seed Math.random with an init script, not a production debug backdoor. Test complete wins/losses through actual UI clicks, compare displayed score, freeze timer and persist best win time (fixed win scores are not useful records).
- Never expose hidden mines/helpers in data attributes, aria labels or CSS classes. Helpers must retain their numeric clue alongside their icon, or the puzzle stops being solvable.
- Assert pairwise cell edges, not just page scrollWidth. A margin-left aisle shifts a full-width tile onto its next neighbor without causing page overflow. Use an explicit grid track for the aisle and explicit column placement.
- Bound desktop board width. A six-column 1fr grid in a wide panel can create 117px tiles and push the last row below1500px while every functional test passes. Measure first/last row Y and tile sizes.
- Put mobile reveal/flag controls BEFORE the board; use sticky top positioning inside the game. Shrink decorative headers so controls and first cells are initially visible. Test actual isMobile+hasTouch context with tap(), not viewport resizing alone.
- A modal-looking div is not an accessible dialog. Use native showModal(), assert focus lands inside, Escape dismisses, and a report button can reopen it for inspection after a game ends.
- Reset transient flag mode and share feedback on new game. Otherwise a player's first tap after restart silently flags instead of starting.
- Exercise clipboard sharing through actual permissions and readback; navigator.share can exist on desktop Chrome and bypass expected clipboard feedback. Prefer native sharing on coarse-pointer devices and clipboard on desktop; handle AbortError as a user cancellation without fallback copying.
- Deploy from source and rerun the same browser suite on the exact public alias. Verify final asset hashes in served HTML; initial deploy success is not evidence for later local polish.
