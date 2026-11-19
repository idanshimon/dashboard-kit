// Per-CELL clipping AND overlap probe for rendered tables.
//
// WHY THIS EXISTS: page-level `documentElement.scrollWidth - clientWidth` returns
// 0 when a table overflows inside its own wrapper (`overflow:hidden` on the
// wrapper contains the damage). The page looks fine, every row is present, and
// the prose in the widest column is silently TRUNCATED. Nothing errors.
//
// 🚨 CLIPPING AND OVERLAP ARE DIFFERENT FAILURES AND NEED DIFFERENT METRICS.
// `scrollWidth - clientWidth` finds clipped cells and returns **0 for overlap**,
// because text printed on top of the next column is not overflowing its OWN box.
// Verified 2026-08-28: an earlier version of this script returned PASS on a table
// whose figure column was rendering directly over the column beside it -- the
// user caught it in a screenshot after the probe said clean. Overlap needs a
// pairwise comparison of adjacent cell rects; that is what `overlaps` below is.
//
// Paste into Runtime.evaluate (CDP) or browser_console(expression=...).
// Returns JSON. PASS is: every table has clippedCells === 0 AND overlaps === 0.
//
//   browser_cdp(method="Runtime.evaluate", target_id=<id>,
//               params={"expression": <this file>, "returnByValue": true})
//
// Run it at EVERY breakpoint you ship (1440 / 820 / 390), not just the width your
// window happens to be -- a responsive block can carry its own broken rule that
// survives the desktop fix. Loop Emulation.setDeviceMetricsOverride between runs.

(() => {
  const tables = [];
  document.querySelectorAll('table').forEach((t, i) => {
    const wrap = t.parentElement;
    let clipped = 0, maxOver = 0, overlaps = 0;
    const samples = [];
    const overlapSamples = [];

    t.querySelectorAll('td,th').forEach(cell => {
      // scrollWidth > clientWidth means the cell's content does not fit and is
      // being cut off. Reliable for TRUNCATION only -- getBoundingClientRect()
      // reports the BOX, which is happily correct while the text inside is clipped.
      const over = cell.scrollWidth - cell.clientWidth;
      if (over > 1) {
        clipped++;
        if (over > maxOver) maxOver = over;
        if (samples.length < 3) {
          samples.push({
            col: cell.cellIndex,
            overflowPx: over,
            text: (cell.textContent || '').trim().slice(0, 60)
          });
        }
      }
    });

    // OVERLAP: compare each cell's right edge against its next sibling's left.
    // This is the check that catches a nowrap cell painting over the column
    // beside it -- invisible to every scrollWidth-based metric.
    t.querySelectorAll('tr').forEach(tr => {
      const cells = [...tr.querySelectorAll('td,th')];
      cells.forEach((cell, idx) => {
        const next = cells[idx + 1];
        if (!next) return;
        const a = cell.getBoundingClientRect();
        const b = next.getBoundingClientRect();
        const bleed = a.right - b.left;
        if (bleed > 1.5) {
          overlaps++;
          if (overlapSamples.length < 3) {
            overlapSamples.push({
              col: cell.cellIndex,
              bleedPx: Math.round(bleed),
              text: (cell.textContent || '').trim().slice(0, 50),
              onto: (next.textContent || '').trim().slice(0, 30)
            });
          }
        }
      });
    });

    const tRect = t.getBoundingClientRect();
    const wRect = wrap ? wrap.getBoundingClientRect() : tRect;

    tables.push({
      index: i,
      classes: t.className || '(none)',
      cols: t.querySelectorAll('thead th').length,
      rows: t.querySelectorAll('tbody tr').length,
      tableWidth: Math.round(tRect.width),
      wrapperWidth: Math.round(wRect.width),
      // A table WIDER than its wrapper is overflowing even if no single cell
      // reports clipping -- catches the case where the whole table is cut.
      tableExceedsWrapper: Math.round(tRect.width - wRect.width) > 1,
      clippedCells: clipped,
      maxOverflowPx: maxOver,
      overlaps,
      samples,
      overlapSamples
    });
  });

  const de = document.documentElement;
  const bad = tables.filter(
    t => t.clippedCells > 0 || t.overlaps > 0 || t.tableExceedsWrapper
  );

  return JSON.stringify({
    verdict: bad.length === 0 ? 'PASS' : 'FAIL',
    failingTables: bad.map(t => t.index),
    // The population. A verdict without this is not a result -- if tableCount is
    // 0 the probe found nothing and PASS is vacuous.
    tableCount: tables.length,
    viewportWidth: de.clientWidth,
    tables,
    // Deliberately reported LAST and labelled: this number is ~always 0 even
    // when tables are badly clipped. Do not use it as the pass criterion.
    pageHorizontalOverflow_DO_NOT_TRUST: de.scrollWidth - de.clientWidth
  }, null, 1);
})()
