# Grounded in-app assistant, version skew, and action→view deep links

## Grounded read-only assistant panel
1. **Do the grounding on the server.** Collect the current view plus live sources: records, runs, rules, specs, and repo activity. Put every source in a numbered list with its kind and a link. Label derived aggregates as computed. Narrow to the viewed entity *before* keyword ranking.
2. **Rank carefully.** Use a stoplist that includes domain-generic words ("rule", "run", "many"). Drop single-term tail matches scoring below about 60% of the best match, because otherwise unrelated records ride in on a filler word.
3. **Guard sensitive data where it leaves for the model.** Classify excerpts and withhold sensitive ones. Show the operator how many were withheld and under which rule. If the classifier fails, withhold (fail closed).
4. **Show what the model saw.** Each reply gets a "What I looked at" drawer: source counts, computed facts, withheld count, warnings. Add clickable `[n]` citations that highlight their source. Show a citation number with no matching source as flagged plain text. Offer a context preview and a grounding toggle.
5. **Fall back honestly.** If no model is configured, or the call fails, answer with the deterministic composer and label the reply as such. Show the model name, latency, and tokens only on live replies.
6. **Keep the panel docked and non-modal.** Use no overlay or blur, and let outside clicks pass through, because the operator is asking about the page behind the panel. The dialog title must be required by the type (rendered visually hidden), so a missing title fails typecheck instead of raising a runtime accessibility error.
7. **Render model output safely.** Turn it into React nodes, never `dangerouslySetInnerHTML`. Drop any reply that arrives after the view or chat was reset (use a request-id counter).

## UI ahead of backend (version skew)
- When a page fails, check the live API schema (`/openapi.json` path list) for the endpoint before debugging the UI.
- If the endpoint returns 404, rebuild the page from the older endpoints and label it as assembled. Mark any section without a source as unavailable with an "upgrade" reason, never as empty-and-ok. Any other failure should show as an error.

## About / version
- Put it in a low-prominence spot such as the last settings tab or a sidebar tooltip.
- Embed version, commit, dirty flag, and build time at build time. Container builds have no `.git`, so pass the SHA in as a build arg, otherwise production reads "unknown".
- Probe each backend live (health, API version, endpoint count, whether it supports the UI's newest endpoint). Add a "copy for bug report" button. Show "unknown" for anything a backend does not report.

## Action → explanatory view
After a user action (approve, decide), the success toast carries an action that opens the view showing how that action connects to the rest. Make the toast last longer than the default so there is time to click.
- Link by stable natural keys (`?run=&card=`), because the write response usually lacks the persisted record id.
- The target resolves the link with a pure, tested function. Pick the latest matching record written by the *user*, never an automated one. Keep three states distinct: found, parent exists but record not yet landed, and nothing found. Re-poll briefly while waiting, then say the record was not found.
- Pin the focused record, its parent, and its siblings so they survive any render budget or cap. Turn on the relationship layer that shows the connection. Select the record, widen the selection one hop, fit the view, open its detail, and show a banner that states the connection in counts. Provide "Clear focus".
- Verify the link end to end with a real record from live data: confirm the banner text and check a screenshot.
