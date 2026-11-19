/**
 * Contrast/token source lint for themed Tailwind apps.
 *
 *   npx tsx scripts/check-contrast-tokens.ts
 *
 * WHY A SOURCE LINT AND NOT A UNIT TEST
 * -------------------------------------
 * The bug this catches is invisible to any DOM-free assertion, and a
 * screenshot only catches the ONE theme you happened to render:
 *
 *   <a class="bg-[color:var(--color-ink)] text-white">Calculate</a>
 *
 * `--color-ink` INVERTS with the theme (#171a20 light -> #f4f4f5 dark). The
 * author meant "ink = dark", which is true in exactly one theme. In the other
 * the fill flips to near-white while `text-white` stays put. Measured on a
 * live page 2026-08-30: 1.10:1. Not low contrast — no contrast.
 *
 * Rule enforced: a FILLED control must be built from a token that is stable
 * BY INTENT. An accent token qualifies (it may shift hue across themes but
 * never crosses the light/dark boundary). Semantic ink/canvas/surface tokens
 * do not.
 *
 * Rule 2: hard-coded palette colours (text-blue-600, dark:text-blue-400)
 * bypass the token system entirely. One such pair measured 1.29:1 on black.
 *
 * TUNING: edit INVERTING to match your theme's own inverting token names.
 * Anything you define in BOTH :root and .dark with light/dark values belongs
 * in that list.
 */
import fs from "node:fs";
import path from "node:path";

const SRC = path.join(process.cwd(), "src");

/** Tokens that FLIP across themes and cannot sit behind fixed-colour text. */
const INVERTING = ["--color-ink", "--color-ink-body", "--color-canvas"];

/** Palette families that indicate a raw Tailwind colour, not a token. */
const RAW_PALETTE = /\b(?:text|bg|border|decoration)-(?:blue|stone|gray|grey|zinc|slate|neutral|green|red|amber|indigo|purple)-\d{2,3}\b/;

function walk(dir: string): string[] {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) return walk(p);
    return /\.(tsx|jsx)$/.test(e.name) ? [p] : [];
  });
}

let violations = 0;
let checked = 0;

for (const file of walk(SRC)) {
  const src = fs.readFileSync(file, "utf8");
  const rel = path.relative(process.cwd(), file);

  // className="..." and className={`...`}
  for (const m of src.matchAll(/className=(?:"([^"]*)"|\{`([^`]*)`\})/g)) {
    const cls = m[1] ?? m[2] ?? "";
    checked++;
    const line = src.slice(0, m.index).split("\n").length;

    const invertingFill = INVERTING.find((t) =>
      cls.includes(`bg-[color:var(${t})]`),
    );
    const fixedText = /\btext-white\b|\btext-black\b/.test(cls);

    if (invertingFill && fixedText) {
      violations++;
      console.log(
        `FAIL ${rel}:${line}\n` +
          `     ${invertingFill} inverts across themes but text colour is fixed\n` +
          `     -> invisible in one theme. Use a stable accent token as the fill.\n` +
          `     ${cls.slice(0, 120)}\n`,
      );
    }

    if (RAW_PALETTE.test(cls)) {
      violations++;
      console.log(
        `FAIL ${rel}:${line}\n` +
          `     hard-coded palette colour bypasses the theme tokens\n` +
          `     ${cls.slice(0, 120)}\n`,
      );
    }
  }
}

console.log(`${checked} className blocks checked, ${violations} violation(s)`);
process.exit(violations ? 1 : 0);
