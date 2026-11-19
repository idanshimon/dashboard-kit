/* uxui v2.1 core JS — theme resolution goes in <head> (see theming.md).
   This file holds chart plumbing + print swap. Load with defer, after ECharts. */

const charts = [];
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

/* Robust alpha for any CSS color format the browser accepts (hex3/6, rgb, hsl, color-mix). */
const alpha = (c, a) => {
  const ctx = document.createElement('canvas').getContext('2d');
  ctx.fillStyle = c;
  const h = ctx.fillStyle;
  if (h[0] === '#') {
    const n = parseInt(h.slice(1), 16);
    return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`;
  }
  return h.replace(/rgba?\(([^)]+)\)/, (_, p) =>
    `rgba(${p.split(',').slice(0, 3).map(s => s.trim()).join(',')},${a})`);
};

const base = () => ({
  textStyle: { fontFamily: css('--font-sans'), color: css('--text-secondary') },
  grid: { left: 8, right: 8, top: 24, bottom: 8, containLabel: true },
  tooltip: { trigger: 'axis', backgroundColor: css('--bg-elevated'),
    borderColor: css('--border-default'),
    textStyle: { color: css('--text-primary'), fontSize: 12 },
    axisPointer: { type: 'line', lineStyle: { color: css('--border-default') } } },
  xAxis: { axisLine: { lineStyle: { color: css('--border-default') } }, axisTick: { show: false },
    splitLine: { show: false }, axisLabel: { color: css('--text-secondary'), fontSize: 12 } },
  yAxis: { axisLine: { show: false }, axisTick: { show: false },
    splitLine: { lineStyle: { color: css('--border-muted') } },
    axisLabel: { color: css('--text-secondary'), fontSize: 12 } }
});

/* smooth:false by default — smoothing invents values that were never measured.
   connectNulls:false — missing must render as a GAP, never bridged or zeroed. */
const lineSeries = (data, color, opts = {}) => ({
  type: 'line', data, smooth: false, showSymbol: false, connectNulls: false,
  lineStyle: { width: 2, color }, ...opts
});
const areaSeries = (data, color) => ({
  ...lineSeries(data, color),
  areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
    colorStops: [{ offset: 0, color: alpha(color, .25) }, { offset: 1, color: alpha(color, 0) }] } }
});
const stepSeries = (data, color) => ({ ...lineSeries(data, color), step: 'end' });
const barSeries = (data, color) => ({ type: 'bar', data, barMaxWidth: 28,
  itemStyle: { color, borderRadius: [4, 4, 0, 0] } });

/* One ResizeObserver for all charts — window listeners miss container-driven resizes. */
const ro = new ResizeObserver(es => es.forEach(e => e.target.__chart && e.target.__chart.resize()));
function mount(el, build) {
  const inst = echarts.init(el);
  el.__chart = inst;
  inst.setOption(build(), { notMerge: true });
  ro.observe(el);
  charts.push({ inst, build });
  return inst;
}

/* notMerge is REQUIRED: partial setOption leaves stale colors in series/legend/markLine. */
window.addEventListener('themechange', () =>
  charts.forEach(c => c.inst.setOption(c.build(), { notMerge: true })));

/* getDataURL only returns a string — swap a real <img> in for printing. */
window.addEventListener('beforeprint', () => charts.forEach(c => {
  const img = new Image();
  img.src = c.inst.getDataURL({ pixelRatio: 2, backgroundColor: '#fff' });
  img.className = 'print-chart'; img.style.width = '100%';
  c.inst.getDom().appendChild(img);
  c.inst.getDom().classList.add('printing');
}));
window.addEventListener('afterprint', () => document.querySelectorAll('.print-chart')
  .forEach(n => { n.parentElement.classList.remove('printing'); n.remove(); }));
