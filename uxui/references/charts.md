# Charts — selection procedure, data semantics, presets
*(v2.1 — smoothing/axis/alpha bugs fixed; deterministic procedure added)*

## 1. Answer these BEFORE choosing a chart

v2.0 picked a chart family and stopped. Family is the easy part; these decide whether the chart
*lies*:

1. What comparison is being made?
2. What is the unit? (rate, count, cumulative, percent, or percentage points?)
3. What is the baseline / target?
4. Can values be negative?
5. Is category order meaningful?
6. Are time intervals regular?
7. **Is interpolation between points valid?** -> decides `smooth`, and line vs step
8. Does the composition sum to a real whole? -> decides whether stacking is honest
9. Is uncertainty material? -> bands, not a bare line
10. **What does missing mean?** -> gap, not zero

## 2. Family selection

| The question | Use | Never |
|---|---|---|
| How did this change over time? | Line | Bar with many buckets |
| Discrete state changes over time | **Step line** | Smoothed line |
| How do a few categories compare? | Horizontal bar, sorted desc | Donut |
| Composition, <=4 parts | Donut + center total | Pie with labels |
| Composition, >4 parts | Stacked horizontal bar | Donut |
| Part-to-whole over time (real total) | Stacked area | Multi-line |
| Distribution | Histogram / box plot | Line |
| Relationship between two variables | Scatter | Dual-axis line |
| Density across 2 dimensions | Heatmap | 3D anything |
| Trend inside a KPI card | Sparkline, no axes/grid | Full chart |
| A single number | **Big number** | Gauge, 1-bar chart |

**Hard rules:** no dual y-axis, no 3D, no pie >4 slices, max 5 series per chart (else small
multiples), and **the quantitative/value axis of a bar chart starts at zero** — that is the
x-axis on a horizontal bar (v2.0 said "y-axis", wrong for horizontal bars). Line charts may use
a non-zero value axis.

**Dual-axis replacements** (v2.0 banned it without offering one): indexed lines (both series
rebased to 100), aligned small multiples with a shared time axis, or two stacked charts with
synchronized `axisPointer`.

## 3. Smoothing

**Default `smooth: false`.** Smoothing is a *semantic* decision, not a density one — v2.0's
"smooth off for sparse, on for dense" was wrong. Curvature invents values never measured and can
overshoot below zero. Enable only when the quantity is genuinely continuous and overshoot is
bounded. Operational, financial and clinical series stay unsmoothed.

## 4. Data semantics — the errors that actually matter

- **Missing != zero.** Render gaps as `null` (ECharts breaks the line); never `0`, never
  interpolate across. A dropped telemetry feed drawn as zero reads as healthy silence.
- **Partial periods** (today, current quarter) marked distinctly — dashed, hatched, or labeled.
- **Stale data**: show `last updated` only if you actually have that timestamp; if data is older
  than the declared `stale_after`, say so visibly.
- **Percent vs percentage points** — label explicitly; never mix on one axis.
- Timezone stated (UTC or local), declared once, applied everywhere.
- Units on every axis and value. Rounding stated where it changes meaning.
- Estimated/provisional values visually distinguished from final.

## 5. ECharts presets

```js
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

// Robust alpha: hex-3/6, rgb(), hsl(), and CSS-var output.
// v2.0 used `color + '40'`, which only works for 6-digit hex — and its own brand
// tokens were HSL, so the preset was incompatible with its own token system.
const alpha = (c, a) => {
  const ctx = document.createElement('canvas').getContext('2d');
  ctx.fillStyle = c;                      // normalizes anything the browser accepts
  const h = ctx.fillStyle;
  if (h[0] === '#') {
    const n = parseInt(h.slice(1), 16);
    return `rgba(${n>>16&255},${n>>8&255},${n&255},${a})`;
  }
  return h.replace(/rgba?\(([^)]+)\)/, (_, p) =>
    `rgba(${p.split(',').slice(0,3).map(s=>s.trim()).join(',')},${a})`);
};

const base = () => ({
  textStyle:{ fontFamily: css('--font-sans'), color: css('--text-secondary') },
  grid:{ left:8, right:8, top:24, bottom:8, containLabel:true },
  tooltip:{ trigger:'axis', backgroundColor: css('--bg-elevated'),
    borderColor: css('--border-default'),
    textStyle:{ color: css('--text-primary'), fontSize:12 },
    axisPointer:{ type:'line', lineStyle:{ color: css('--border-default') } } },
  xAxis:{ axisLine:{lineStyle:{color:css('--border-default')}}, axisTick:{show:false},
    splitLine:{show:false},
    axisLabel:{ color: css('--text-secondary'), fontSize:12 } },  // 11px+tertiary failed contrast
  yAxis:{ axisLine:{show:false}, axisTick:{show:false},
    splitLine:{lineStyle:{color:css('--border-muted')}},
    axisLabel:{ color: css('--text-secondary'), fontSize:12 } }
});

const areaSeries = (data, color) => ({
  type:'line', data, smooth:false, showSymbol:false, connectNulls:false,
  lineStyle:{ width:2, color },
  areaStyle:{ color:{ type:'linear', x:0,y:0,x2:0,y2:1,
    colorStops:[{offset:0,color:alpha(color,.25)},{offset:1,color:alpha(color,0)}] } }
});

const barSeries = (data, color) => ({ type:'bar', data, barMaxWidth:28,
  itemStyle:{ color, borderRadius:[4,4,0,0] } });
```

**Resize** — one `ResizeObserver` per container, not a window listener per chart (window
listeners miss sidebar/tab/font-driven container changes and scale badly):

```js
const ro = new ResizeObserver(es => es.forEach(e => e.target.__chart?.resize()));
function mount(el, build) { const c = echarts.init(el); el.__chart = c;
  c.setOption(build()); ro.observe(el); charts.push({inst:c, build}); return c; }
```

## 6. States — only the REACHABLE ones

Implement the states this artifact's data lifecycle can actually reach. Generating unreachable
loading skeletons and dead retry buttons for inlined data is a defect, not thoroughness.

| Data lifecycle | Required states |
|---|---|
| Bundled/static | rendered, filtered-empty |
| Fetched once | loading, rendered, empty, error+retry |
| Live/polling | + stale, partial-failure, reconnecting |

Empty states name *why* it is empty and the action that fills it. Never the string "No data".
A panel that silently renders empty reads as broken — treat it as a bug.
