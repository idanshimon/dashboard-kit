#!/usr/bin/env python3
"""WCAG contrast ratio between two hex colors.

Turns a reviewer's adjective ("subtle", "blends in", "hard to read") into a
pass/fail number. Written after a session where two successive eyeballed border
bumps both landed UNDER the 3:1 threshold and had to be re-reviewed each time.

Usage:
    python3 contrast_ratio.py "#4A5D78" "#0B0F14"
    python3 contrast_ratio.py "#4A5D78" "#0B0F14" --kind text

Thresholds (WCAG 2.1):
    3.0:1   non-text UI boundaries, borders, focus rings, icon strokes  (1.4.11)    4.5:1   normal body text                                            (1.4.3)
    3.0:1   large text (>=18pt, or >=14pt bold)                         (1.4.3)
    7.0:1   normal body text, AAA                                       (1.4.6)

Exits non-zero when the pair fails its threshold, so it works as a gate:
    python3 contrast_ratio.py "$FG" "$BG" || echo "fix the token"

LIMITATION: this compares a STATIC pair. It cannot catch a token that inverts
with the theme (`bg-[color:var(--color-ink)] text-white` is white-on-white in
dark mode at 1.10:1) because there is no fixed pair to hand it. For that class
run `theme_token_contrast_lint.py`, and see
`references/theme-inverting-token-contrast.md`.
"""
import sys


def _lin(c: float) -> float:
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_color: str) -> float:
    h = hex_color.strip().lstrip("#")
    if len(h) == 3:                      # #abc -> #aabbcc
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        raise ValueError(f"expected 3- or 6-digit hex, got {hex_color!r}")
    r, g, b = (_lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


THRESHOLDS = {"ui": 3.0, "large": 3.0, "text": 4.5, "aaa": 7.0}

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    kind = "ui"
    for a in sys.argv[1:]:
        if a.startswith("--kind"):
            kind = a.split("=", 1)[1] if "=" in a else sys.argv[sys.argv.index(a) + 1]

    if len(args) < 2:
        print(__doc__)
        sys.exit(2)

    fg, bg = args[0], args[1]
    need = THRESHOLDS.get(kind, 3.0)
    r = ratio(fg, bg)
    verdict = "PASS" if r >= need else "FAIL"
    print(f"{fg} on {bg}: {r:.2f}:1  (need {need}:1 for '{kind}')  {verdict}")

    if verdict == "FAIL":
        # Suggest how far off it is, so the next guess isn't blind.
        print(f"  short by {need - r:.2f} — lighten/darken and re-run, "
              f"do not ship on 'looks better'")
        sys.exit(1)
