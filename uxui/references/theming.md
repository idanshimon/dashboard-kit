# Theming — Light/Dark + Brand Palettes
*(v2.1 — rewritten after GPT-5.6-sol review; every bug below was a real defect in v2.0)*

## 1. Two-layer token model

- **Layer 1 — primitives**: raw ramps. NEVER referenced in component CSS.
- **Layer 2 — semantic**: `--bg-primary`, `--text-secondary`, `--color-accent`. Components use ONLY these.

Honest scope note: this is a *hybrid* model. Some semantic values are theme-specific literals
(no single primitive is correct in both themes). The invariant that matters is one-directional:
**component CSS never contains a raw color**. Layer 2 may.

```css
:root {
  /* Layer 1 — neutral ramp */
  --gray-0:#ffffff; --gray-50:#f6f8fa; --gray-100:#eaeef2; --gray-200:#d0d7de;
  --gray-400:#8b949e; --gray-500:#6e7681; --gray-600:#59636e; --gray-700:#30363d;
  --gray-800:#21262d; --gray-850:#161b22; --gray-900:#0d1117;

  /* Theme-independent primitives */
  --space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px; --space-5:20px;
  --space-6:24px; --space-8:32px; --space-10:40px; --space-12:48px; --space-16:64px;
  --radius-sm:4px; --radius-md:6px; --radius-lg:8px; --radius-xl:12px; --radius-full:9999px;
  --transition-fast:150ms cubic-bezier(.4,0,.2,1);
  --transition-normal:250ms cubic-bezier(.4,0,.2,1);
}
```

## 2. Brand palettes — per-preset ramps, NOT one hue

**v2.0 claimed "swap ONE number to rebrand". That was false.** Equal HSL lightness is not equal
perceived brightness, so a single `--brand-h` cannot guarantee contrast. Each preset ships its
own contrast-checked ramp.

```css
:root, [data-brand="github"] {
  --brand-400:#58a6ff; --brand-600:#0969da;
  --brand-bg-d:rgba(88,166,255,.12); --brand-bg-l:rgba(9,105,218,.08);
}
[data-brand="aurora"] { --brand-400:#b98cff; --brand-600:#6639ba;
  --brand-bg-d:rgba(185,140,255,.12); --brand-bg-l:rgba(102,57,186,.08); }
[data-brand="teal"]   { --brand-400:#39c5bb; --brand-600:#0f766e;
  --brand-bg-d:rgba(57,197,187,.12); --brand-bg-l:rgba(15,118,110,.08); }
[data-brand="ember"]  { --brand-400:#ff9457; --brand-600:#bc4c00;
  --brand-bg-d:rgba(255,148,87,.12); --brand-bg-l:rgba(188,76,0,.08); }
[data-brand="mono"]   { --brand-400:#adbac7; --brand-600:#424a53;
  --brand-bg-d:rgba(173,186,199,.12); --brand-bg-l:rgba(66,74,83,.08); }
```

Brand hue is an **input**, not a domain inference. Do NOT pick teal because the artifact is
clinical — that is stereotyping, not design. Default `github` unless the user supplies a brand.

## 3. Semantic layer — both themes

```css
:root, [data-theme="dark"] {
  color-scheme: dark;                       /* binds native controls — the meta tag does NOT */
  --bg-primary: var(--gray-900);
  --bg-surface: var(--gray-850);
  --bg-elevated:#1c2128;
  --border-default: var(--gray-700);
  --border-muted: var(--gray-800);
  --text-primary:#e6edf3;
  --text-secondary: var(--gray-400);
  --text-tertiary: var(--gray-500);
  --color-accent: var(--brand-400);
  --accent-bg: var(--brand-bg-d);
  --color-success:#3fb950; --color-warning:#d29922; --color-danger:#f85149;
  --shadow-sm:0 1px 2px rgba(0,0,0,.3);
  --shadow-md:0 4px 12px rgba(0,0,0,.4);
  --shadow-lg:0 8px 24px rgba(0,0,0,.5);
}

[data-theme="light"] {
  color-scheme: light;
  /* Page recedes (grey), surfaces advance (white). Matches the prose —
     v2.0 shipped the inverse and contradicted its own doc. */
  --bg-primary: var(--gray-50);
  --bg-surface: var(--gray-0);
  --bg-elevated: var(--gray-0);
  --border-default: var(--gray-200);
  --border-muted: var(--gray-100);
  --text-primary:#1f2328;
  --text-secondary: var(--gray-600);
  --text-tertiary:#6a737d;   /* 4.6:1 on #fff — #818b98 FAILED at small sizes */
  --color-accent: var(--brand-600);
  --accent-bg: var(--brand-bg-l);
  --color-success:#1a7f37; --color-warning:#9a6700; --color-danger:#cf222e;
  --shadow-sm:0 1px 2px rgba(31,35,40,.06);
  --shadow-md:0 4px 12px rgba(31,35,40,.10);
  --shadow-lg:0 8px 24px rgba(31,35,40,.14);
}
```

Light is **not** an inversion: accents darken (400 to 600), semantic colors darken, shadows take
over separation duty from borders.

## 4. Theme resolution — synchronous, no flash, real auto mode

v2.0's Alpine-init approach flashed the wrong theme and persisted the detected system theme as a
user choice. Correct pattern — **in `<head>`, before any body markup**:

```html
<script>
(function () {
  var pref = localStorage.getItem('theme') || 'auto';           // 'auto' | 'dark' | 'light'
  var mq = window.matchMedia('(prefers-color-scheme: light)');
  function resolve() {
    document.documentElement.dataset.theme =
      pref === 'auto' ? (mq.matches ? 'light' : 'dark') : pref;
  }
  resolve();
  mq.addEventListener('change', function () { if (pref === 'auto') resolve(); });
  window.__theme = {
    get pref() { return pref; },
    set: function (p) { pref = p; localStorage.setItem('theme', p); resolve();
                        window.dispatchEvent(new CustomEvent('themechange')); },
    cycle: function () { this.set({auto:'dark', dark:'light', light:'auto'}[pref]); }
  };
})();
</script>
```

Three states, not two. `auto` stays live-bound to the OS; only an explicit choice persists.
Alpine (deferred) may drive `window.__theme` for UI but must not own resolution.

## 5. Charts must re-theme on `themechange`

ECharts does not read CSS variables, and `setOption` **merges** by default — reapplying a partial
option leaves stale colors in series, legends, labels and markLines. Rebuild and replace:

```js
const charts = [];                       // {inst, build}
window.addEventListener('themechange', () => {
  charts.forEach(c => c.inst.setOption(c.build(), { notMerge: true }));
});
```
