# MSXI-embedded reports: extract via the embed, not Fabric

MSXI (msxinsights.microsoft.com) embeds Power BI under its own identity. The real report id
(`window.powerbi.embeds[0].getId()`, synchronous) returns 404 ArtifactNotFound from Fabric MCP for
the user, and Fabric `DiscoverArtifacts` may return unrelated results for every query. Use the page:

1. Catalog: POST `/Report/GetReportsForUserView` with body
   `{areaId: window.top.userAreaId, roleId: window.top.userRoleId, isBAGrid: 0}` (empty body = Bad Request).
   Save it; filter by name/description/owner in Python to find candidate reports.
2. Open `/User/report/<msxi-guid>`; Page.navigate often times out on heavy reports. Swallow the
   timeout, then poll until `window.powerbi.embeds.length` is non-zero and wait ~10s more.
   Close the notifications modal if present.
3. Async JS must store results in `window.__x` and be polled: the harness evaluate times out after 5s.
   If `getPages()` never resolves, the report did not render; screenshot to confirm and move on
   rather than retrying the same call.
4. `page.getVisuals()` then `visual.exportData()` gives CSV per visual. Switch pages with
   `page.setActive()` and wait before listing visuals. Scope with
   `embed.updateFilters(2 /*Add*/, [advanced filter])`; read `getFilters()` + slicer states first,
   because the default scope is often worldwide. Probe candidate filter columns by applying a
   Contains filter and checking that a card value changes; an unknown column errors.
   US HLS: `Account[SalesUnit]` contains "Health" or "HLS" in ME7-style models; OU tables carry
   `Field Accountability Unit = US HLS` directly.
5. Table visuals repeat rows per entity: SUM all rows; deduping or taking the max undercounts.
   Reconcile against the report's own card visuals before using any total; show the check on the
   output, and label tables that do not reconcile as directional instead of guessing a cause.
6. Check whether budget/target cards move with your filter; if they don't, attainment % is invalid.
7. Account-grain tables can silently drop entities: columns built on "(RLS)" measures return blank
   for some accounts and Power BI hides all-blank rows, while cards still count them. Find the
   missing IDs by diffing against a finer table (deals), and close the gap with an explicit
   remainder row (card minus table) instead of presenting a total that doesn't add up.
7. Number formats lie in exports: some reports append a literal `K`/`M` to raw counts
   (`53292K` = 53,292 seats). Sanity-check one account-level value before scaling.
8. Read the report's own refresh-stamp visual and print it on the output; MSXI reports can be
   months stale while the portal looks live.
9. Derive metric definitions from the export before quoting them, and verify the identity on two
   slices. In ME7-style models DBF = billed actual + scheduled + Committed/Committed-at-Risk
   qualified pipeline (upside/uncommitted excluded). Label as derived; ask the data owner to confirm.
10. MSXI totals are not raw MSX: sales-excellence recon applies manual scrubs (revenue landed but
   opp still open, credit rebuilds). A rebuild from raw MSX will not match the official number
   until those scrub rules are applied; plan for "match on recon dates, gap shown with reason".
