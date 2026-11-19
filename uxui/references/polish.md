# Polish Primitives
*(v2.1 — a11y selectors, reduced-motion, and print corrected; glass demoted)*

## Skeleton loaders
```css
.skeleton { background: linear-gradient(90deg, var(--bg-surface) 25%, var(--bg-elevated) 37%, var(--bg-surface) 63%);
  background-size:400% 100%; animation: shimmer 1.4s ease infinite; border-radius: var(--radius-md); }
@keyframes shimmer { 0%{background-position:100% 0} 100%{background-position:-100% 0} }
```
Skeleton box must match the final element exactly — same height, radius, grid slot. Mismatched
skeletons cause layout shift, which reads worse than no skeleton. Only for `fetched`/`live`
lifecycles; never for bundled data.

## Focus & accessibility
```css
:where(a[href], button, input, select, textarea,
       [tabindex]:not([tabindex^="-"])):focus-visible {
  outline:2px solid var(--color-accent); outline-offset:2px; border-radius:var(--radius-sm);
}
```
`[tabindex^="-"]` is excluded — `tabindex="-1"` marks programmatically focused headings, dialogs
and containers, which must not get a control outline (v2.0 outlined all of them).

- Prefer a native `<button>`. Styling `[role=button]` does **not** make it keyboard-operable —
  if unavoidable, add `tabindex="0"` plus Enter/Space handlers.
- Contrast: **4.5:1** body text, **3:1** large text and *essential* UI boundaries — controls,
  state indicators, meaningful graphics. Decorative dividers and card edges are exempt (v2.0
  required 3:1 on all borders, contradicting its own muted-border aesthetic).
- Verify contrast in **both** themes.
- Never encode state in color alone — pair with icon, text, or position.
- Icon-only buttons need `aria-label`. Charts need a text summary or accessible table fallback.
- Touch targets >= 44px.

## Micro-interactions
- Hover: background one elevation step + `border-color` to `--border-accent`. Never scale a card.
- Press: `transform: translateY(1px)`.
- Dense table rows: background only, 100ms; never border change (1px jitter).
- Value changes: fade. No count-up on operational data.

## Reduced motion (MANDATORY)
```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation: none !important;
    transition: none !important;
    scroll-behavior: auto !important;
  }
}
```
v2.0 used `animation-duration:.01ms`, which leaves infinite animations technically running and
ignores smooth scrolling. If a transition carries meaning, add a narrow explicit exception rather
than weakening the blanket rule.

## Decorative effects — optional appendix, OFF by default
Glass/blur is **not** core. Only if explicitly requested:
```css
.glass { background: color-mix(in srgb, var(--bg-surface) 72%, transparent);
  backdrop-filter: blur(12px) saturate(140%); border:1px solid var(--border-muted); }
```
Permitted on sticky headers, floating toolbars, modal scrims — never content cards (kills text
contrast, tanks scroll perf). At most one gradient accent per page.

## Print / export
Override at the **token layer** — overriding `body` alone leaves every card dark (v2.0's bug):
```css
@media print {
  :root, [data-theme="dark"], [data-theme="light"] {
    --bg-primary:#fff; --bg-surface:#fff; --bg-elevated:#fff;
    --text-primary:#000; --text-secondary:#333; --text-tertiary:#555;
    --border-default:#bbb; --border-muted:#ddd;
    --shadow-sm:none; --shadow-md:none; --shadow-lg:none;
  }
  nav, .sidebar, .filters, .no-print { display:none !important; }
  .card { break-inside: avoid; box-shadow:none; border:1px solid var(--border-default); }
  a[href^="http"]::after { content:" (" attr(href) ")"; font-size:10px; color:#555; }
}
```
Charts: `getDataURL()` only *returns a string* — it does not make a canvas printable. Swap in an
`<img>` before print, restore after:
```js
window.addEventListener('beforeprint', () => charts.forEach(c => {
  const img = new Image();
  img.src = c.inst.getDataURL({pixelRatio:2, backgroundColor:'#fff'});
  img.className='print-chart'; img.style.width='100%';
  c.inst.getDom().appendChild(img); c.inst.getDom().classList.add('printing');
}));
window.addEventListener('afterprint', () => document.querySelectorAll('.print-chart')
  .forEach(n => { n.parentElement.classList.remove('printing'); n.remove(); }));
```
```css
.printing > canvas, .printing > div:first-child { display:none; }
```
