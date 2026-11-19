# Leadership activity dashboards: scope before judgement

## User correction

The user asked for a small filterable dashboard approached as an SE leader, rather than a
long page ranking colleagues by documentation score. The previous artifact was roughly
5,700px high with no input/select/button controls. The redesign therefore moved toward
review signals, composable filters, full-record inspection and transparent denominators.

## Findings that changed the design

A saved snapshot held 314 unique activity IDs. Its lower-bound date query also included
21 activity dates after the pull date. Restricting to the pull window through snapshot date
returned 293 records; an August window returned 105. These are snapshot facts, not reusable
benchmarks. 'Since June' was not synonymous with 'work delivered through September.'

The user's August subset held five records, all Not Started, four created more than seven
days after the activity date. Two were same-day design records with similar HCA self-hosting
subjects. This establishes a lifecycle and possible-duplication review, not proof of five
distinct engagements or proof that delivery did not happen. Earlier arithmetic that added
newly-created backfills onto a corpus already containing them double-counted the work.

A roster's aliases had resolved to distinct GUIDs. That only proved no collision among those
lookups; it did NOT prove they belonged to the named people. Zero results must stay
'unverified lookup coverage' until identity, query scope, paging and permissions are checked.
No 'silent SE' ranking is justified from that evidence.

## Metric design

- Default retrospective dates: source lower bound through snapshot day. Do not use today's
  clock for a historical snapshot. Include future plans only by explicit range/preset.
- Completed and open status are separate from event date. Completion flags still are not
  independent verification of customer outcomes.
- Repetition signal: exact normalized substantive description, same mapped identity, at
  least 40 characters. A repeated prefix is not equality. Repeated boilerplate or multi-
  milestone fan-out may be legitimate; show records before drawing a conclusion.
- Same-day/category cluster: retain every distinct activity ID and label possible overlap.
  Never deduplicate distinct IDs solely because subjects resemble one another.
- Capture lag: created day minus activity day. A >7-day review threshold is a chosen
  heuristic, not an organizational SLA. Exclude negative lag (planned dates) from a
  nonnegative capture-lag median and preserve unknown dates as null.
- Score is an experimental text signal. Word count, capitalized name matches and outcome
  verbs can reward verbose templates and miss concise real findings. Strip scaffolding for
  text analysis but preserve the raw record in the detail view. No 'value' or performance
  conclusion follows from this score.
- Team rates must name their denominator: recorded contributors versus roster members are
  different populations. Mark small samples and provisional cohort scope.

## Projection tests exercised

Thirteen node:test cases failed for the missing API, then passed after implementation:
API availability; ID deduplication with absent-ID UI keys; snapshot-relative future flags;
exact-body repetitions versus shared prefixes; same-day/category clustering by person;
empty HTML/template signals; null versus genuine zero scores; intersection of all filters
with inclusive date bounds and search; outcome wording separate from lifecycle status;
consistent filtered cohort/category/person/month totals; honest empty result; capture-lag
threshold and unknown durations; full-text CSV with quoting and formula-prefix protection.

## Completed browser acceptance and what it caught

The delegated UI arrived after the first checkpoint. Independent parent verification then
found real defects despite the child's successful build and self-reported checks:

- KPI cards were static `div`s, not actionable controls. Converted to buttons and verified
  each destination against its displayed cohort count.
- Reset cleared all dates, admitting future tasks. Changed to restore source-since through
  snapshot date; kept the separately labelled full-source preset.
- The signal selector had two empty 'Any' options, and 'Empty / template' selected only
  empty descriptions. Removed the duplicate and gave each signal an exact label.
- Filter labels were visually adjacent but not associated with their inputs. Used native
  label association; interactive rows/headers also gained keyboard activation.
- A same-day-cluster record count was described as 'record pairs.' Corrected the unit.
- A 'Share' bar divided by the largest category rather than all filtered records. Corrected
  the denominator; cohort rates now explicitly say per reporter, not per full-team member.
- A no-outcome-word signal was stated as no result in the note. Corrected to a detector
  limitation. Zero duration became unknown/not recorded; missing source IDs do not inherit
  a local UI key in the Activity ID field.
- Search updated after a debounce. The test typed a query then exported immediately: the
  CSV contained 293 rows while the intended search narrowed to three. Removed the delay
  for this small local corpus and restored focus/caret after synchronous rerender. The
  repeated test proved the exported blob matched the filtered projection exactly.

Final evidence: 13 model tests and 18 saved browser interaction checks passed against the
built, self-contained HTML. Tests covered snapshot and August presets, future-only views,
label association, KPI drill-through, person selection, persistent filters across tabs,
untruncated detail, empty intersections, pagination, immediate search/export and reset.
Additional checks exercised category/team/status intersections and dialog Escape behavior.

Desktop first-fold and narrow detail screenshots were visually inspected. At a 390px
viewport the page remained 390px wide; the wide People table scrolled inside its own
container, and the detail dialog fit at 358px with no observed text overlap. These prove
local runtime/layout behavior, not publication or commit status; those were separate and
not completed at that checkpoint.

## Reusable browser regression pattern

Run assertions against the generated HTML, not only source helpers:

1. Record the current KPI count and filter state.
2. Click the KPI; assert the record list represents exactly that subset.
3. Set intersecting filters and switch tabs; assert filters persist and page resets.
4. Enter search and immediately invoke export. Capture the actual Blob passed to
   `URL.createObjectURL`; compare its text with the CSV derived from the current rows.
   Restore the original browser function afterward. Also test actual download delivery.
5. Assert no-match produces an explicit empty view, not zero quality or fabricated rows.
6. Reset and assert the default upper bound returned.
7. Inspect mobile page width separately from table overflow: a wide scrollable table is
   acceptable; a horizontally scrolling page or clipped dialog is not.

Export must preserve full text and escape quotes/newlines while neutralizing spreadsheet
formula prefixes. Raw descriptions and embedded JSON are untrusted display data: escape
markup and script-closing sequences rather than executing them.

## Leadership recommendation shape

Prefer: 'Review these records for missing context, planned/open status, capture timing or
possible overlap; verify the underlying work before changing reporting.' Avoid: 'Increase
our count to beat another team.' Better numbers come from distinct, supported work recorded
accurately, not splitting one session, duplicating backfills or polishing boilerplate.
