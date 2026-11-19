#!/usr/bin/env python3
"""
Probe candidate BI measures BEFORE building anything on them.

This is Step 3 of the extraction skill, automated. Point it at a CSV you pulled
with `pbi_direct.py csv` and it reports, per measure, whether the thing is a real
populated rate or a placeholder that will poison a ranking.

    python3 probe_measures.py extract.csv --key-cols 2

Reads nothing from the network — run it on any extract, from any BI tool.

WHAT IT CATCHES (each of these shipped into a real report before being caught):

  string-typed placeholder   a measure returning "TBD"/"N/A" for every row.
                             Looks like the metric everyone wants. Is not.
  empty at this grain        named measure, all null. Common: ~40% of the
                             plausible-sounding candidates in one model.
  bimodal flag               mass piled at exactly 0 and exactly max. That is a
                             FLAG (billing model, tier, boolean), not a rate.
                             A genuine rate is a smooth distribution.
  boolean-as-count           only ever 0/1 -> it is a per-row indicator, not a
                             population count, whatever the "# Acc ..." label says.
  out-of-range percent       a "%" measure exceeding 100 usually means the
                             denominator is not what the name implies.
  pre-formatted currency     values arrive as STRINGS ('$1,365,204'). Harmless
                             here because this script parses tolerantly — but a
                             consumer using bare float() gets an exception, and
                             one defaulting to 0.0 on failure silently zeroes the
                             ENTIRE column with no error. Flagged so you check the
                             consumer, not because the data is bad.

Exit code 1 if any measure is unusable, so it can gate a pipeline.
"""
import argparse
import collections
import csv
import io
import sys


def num(v):
    if v is None:
        return None
    s = str(v).replace(',', '').replace('$', '').replace('%', '').strip()
    if s == '':
        return None
    try:
        return float(s)
    except ValueError:
        return None


def classify(name, raw):
    """Return (verdict, note). verdict in {ok, WARN, UNUSABLE}."""
    n = len(raw)
    nonempty = [v for v in raw if str(v).strip() != '']
    nums = [num(v) for v in nonempty]
    numeric = [x for x in nums if x is not None]
    strings = [v for v, x in zip(nonempty, nums) if x is None]

    # Values that are numeric ONLY because num() strips $ , % — a consumer using
    # bare float() will raise on these, and one that swallows the error and
    # defaults to 0.0 zeroes the whole column silently. This shipped once and was
    # invisible for days: a real $133,253 read as 0 with no error anywhere.
    formatted = [v for v in nonempty
                 if any(c in str(v) for c in '$,%()') and num(v) is not None]

    if not nonempty:
        return 'UNUSABLE', f'all {n} rows empty/null — not populated at this grain'

    if strings and len(strings) == len(nonempty):
        vals = collections.Counter(strings).most_common(3)
        shown = ', '.join(f'{v!r}x{c}' for v, c in vals)
        return 'UNUSABLE', f'string-typed placeholder: {shown}'

    if strings:
        return 'WARN', (f'{len(strings)} of {len(nonempty)} rows non-numeric '
                        f'(e.g. {strings[0]!r}) — mixed type')

    fill = len(numeric) / n
    nonzero = [x for x in numeric if x != 0]
    if not nonzero:
        return 'UNUSABLE', f'populated but every value is 0 ({n} rows)'

    if set(numeric) <= {0.0, 1.0}:
        return 'WARN', ('only ever 0/1 — a per-row BOOLEAN flag, not a count. '
                        'Sum it yourself if you want a population figure.')

    lo, hi = min(numeric), max(numeric)
    at_lo = sum(1 for x in numeric if x == lo)
    at_hi = sum(1 for x in numeric if x == hi)
    if hi > lo and (at_lo + at_hi) / len(numeric) >= 0.80:
        return 'WARN', (f'BIMODAL: {at_lo/len(numeric):.0%} at {lo:g}, '
                        f'{at_hi/len(numeric):.0%} at {hi:g} — this is a FLAG '
                        f'(billing model / tier / boolean), not a rate')

    note = f'fill {fill:.0%} ({len(numeric)}/{n}), range {lo:,.2f}..{hi:,.2f}'
    if ('%' in name or 'pct' in name.lower() or 'penetration' in name.lower()
            or 'attach' in name.lower()) and hi > 100:
        return 'WARN', (note + ' — exceeds 100%: the denominator is probably '
                                'not what the name implies. Reverse-engineer it.')
    if formatted:
        return 'WARN', (note + f' — PRE-FORMATTED strings (e.g. {formatted[0]!r}). '
                        'bare float() RAISES on these; a consumer defaulting to '
                        '0.0 on failure zeroes this column silently. Strip $ , % '
                        'and return None (never 0.0) on failure.')
    return 'ok', note


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('csv_path')
    ap.add_argument('--key-cols', type=int, default=2,
                    help='leading identifier columns to skip (default 2)')
    args = ap.parse_args()

    raw = open(args.csv_path, encoding='utf-8-sig').read()
    rows = list(csv.reader(io.StringIO(raw)))
    if len(rows) < 2:
        print('no data rows', file=sys.stderr)
        return 1
    header, body = rows[0], rows[1:]

    print(f'{len(body)} rows, {len(header)} columns — {args.csv_path}\n')
    width = max(len(h) for h in header[args.key_cols:]) + 2
    bad = 0
    for i in range(args.key_cols, len(header)):
        verdict, note = classify(header[i], [r[i] if i < len(r) else '' for r in body])
        if verdict != 'ok':
            bad += 1
        print(f'  [{verdict:8}] {header[i]:<{width}} {note}')

    print()
    if bad:
        print(f'{bad} measure(s) need scrutiny before you build on them.')
        print('Do NOT quote a derived headline number from a WARN/UNUSABLE column.')
        return 1
    print('All measures look populated and plausibly typed. Still reverse-engineer')
    print('any formula you intend to rely on, and quote the fit ratio.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
