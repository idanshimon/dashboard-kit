# Free-text search over a filtered list, without lying

Worked recipe from adding `?q=` to a 2,512-row inventory table that already had
a facet sidebar, sortable headers, and deep links (2026-08-31).

Covers the two defects that ride along with any "let me search this list"
request. Both are the same class as a KPI reporting a comfortable zero: the
surface answers confidently and the answer is wrong.

---

## 1. Identifier fragments and words need DIFFERENT predicates

The request was *"search by VIN for example and maybe other key words"* — one
box, two genuinely different matching problems.

People read the **last 6 characters** of an identifier off a window sticker or
a dealer's text message. That needs positional matching. But running the same
`LIKE` across a concatenation of every column also matches trims, colours and
descriptions that happen to contain those characters, and hands back confident
junk.

Route on the **shape of the input**:

```ts
// >=5 alphanumerics containing at least one digit => identifier-shaped
const idish = /^[A-Za-z0-9]{5,17}$/.test(raw) && /\d/.test(raw);

if (idish) {
  // ONLY the identifier column.
  where.push(sql`upper(l.vin) like ${"%" + raw.toUpperCase() + "%"}`);
} else {
  // Concatenate FIRST, then AND the terms. Each term is checked against the
  // whole haystack, so a multi-word query may satisfy different terms from
  // different columns.
  const hay = sql`lower(concat_ws(' ',
    l.vin, l.model_year::text, l.model, l.trim, l.body_style,
    l.drivetrain, l.fuel, l.exterior_color, l.interior_color, d.name))`;
  for (const term of raw.toLowerCase().split(/\s+/).filter(Boolean)) {
    where.push(sql`${hay} like ${"%" + term + "%"}`);
  }
}
```

Concatenating before matching is what makes `santa fe calligraphy maxon` work.
Requiring any single field to contain the whole phrase returns nothing, because
the model, trim and dealer live in three different columns.

`concat_ws` (not `||`) so a NULL trim doesn't null the entire haystack.

**Check the columns exist before writing the predicate.** I drafted a haystack
including a stock number the table never had. One `grep` of the schema is
cheaper than a runtime error on a deployed page.

### Assert the ROUTING, not just the row counts

A test that only checks counts passes even if every query takes the identifier
path. Assert the classifier directly:

```
routing: "calligraphy" idish=false   (must be false)
routing: "137546"      idish=true    (must be true)
```

### Regression bar

| Query | Expect | Catches |
|---|---|---|
| full identifier | exactly 1 | over-broad matching |
| last 6 chars | ≥ 1 | fragment support |
| a trim word | many | word path reachable |
| a dealer name | many | joined column searchable |
| two words, different columns | non-zero | concatenate-then-AND |
| MIXED case | same as lowercase | case folding |
| `zzzznotathing` | **0, not everything** | predicate degrading to no-op |

The last row is the important one. A broken predicate usually fails *open* —
returning the unfiltered corpus — and every other assertion still passes.

---

## 2. Facet counts must honour the search

The sidebar is derived from the same corpus by a **separate query** that keeps
its own WHERE clause. Add search to the main query only, and searching `maxon`
still advertises `Towne Hyundai (333)` in the sidebar: counts contradicting the
result set on the same screen.

Two traps when adding the predicate to a facet builder:

**The facet query may not have your join.** The per-column facet query selected
`from listing l` with no `dealer` table, while the search haystack referenced
`d.name`. Adding a join there changes its `GROUP BY` semantics. Use a
correlated subquery instead:

```sql
(select name from dealer where dealer_code = l.dealer_code)
```

**Facet builders take a `skip` key** so a facet doesn't filter itself (the Model
facet must ignore the Model selection, or it always reports 1 option). Search is
**not** self-filtering — pass it under its own key so it applies to every facet.

---

## UX details that matter

- **Preserve active facets.** Carry them as hidden inputs in the search form so
  search NARROWS the current view instead of resetting it.
- **Drop `?page`.** Results change, so page 7 is meaningless — same rule as
  sorting.
- Put the box next to the sort control, not floating above the table; they are
  the same class of "reshape this view" control.

---

## Verify against the LIVE page, through any auth gate

Local SQL passing is not the deliverable. Drive the deployed URL, and if the
app is password-gated, capture the cookie once and reuse it:

```bash
curl -s -o /dev/null -c /tmp/jar "$B/listings?key=$PW"
curl -s -b /tmp/jar "$B/listings?q=137546" -o /tmp/s.html
```

Then parse the rendered count. **Strip `<!-- -->` comments before stripping
tags** — React splits interpolated text, so `2,512` can arrive severed from the
word `vehicles` and a naive regex reports the feature missing.
