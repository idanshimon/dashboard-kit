#!/usr/bin/env python3
"""Source lint for theme-inverting background tokens behind fixed text colors.

Catches the class of bug that `contrast_ratio.py` structurally CANNOT:
there is no static hex pair to compare, because one side flips with the theme.

    className="bg-[color:var(--color-ink)] text-white"

--color-ink is #171a20 in light and #f4f4f5 in dark. text-white does not move.
Dark mode renders white-on-white: measured 1.10:1 against a 4.5:1 requirement.
The control is invisible, not merely low-contrast.

Written after cartrack 2026-08-31, where the user reported "button text hard to
see" and a grep for the pattern found SIX instances shipped to production
(Calculate, Save settings, filter chips, active facet pills, pagination,
Dealer page).

Usage:
    python3 theme_token_contrast_lint.py [src_dir]      # default: ./src

Exits non-zero on any violation, so it gates a build:
    python3 theme_token_contrast_lint.py && npm run build

Configure INVERTING for your token names. The test is semantic, not textual:
does this token CROSS the light/dark boundary? --color-accent shifting
#3e6ae1 -> #3368ff is fine (stays mid-blue). --color-ink flipping near-black to
near-white is not.
"""
import re
import sys
from pathlib import Path

# Tokens whose value crosses the light/dark boundary. NOT safe behind a
# hard-coded text color.
INVERTING = [
    "--color-ink",
    "--color-ink-body",
    "--color-canvas",
]

# Raw palette classes that bypass the token system. Once a design system
# exists, these are unreviewed color decisions.
PALETTE = re.compile(r"\b(?:text|bg|border|decoration)-"
                     r"(?:blue|stone|gray|grey|zinc|slate|neutral)-\d{2,3}\b")

FIXED_TEXT = re.compile(r"\btext-(?:white|black)\b")

# className="..." and className={`...`}
CLASSNAME = re.compile(r"className=(?:\"([^\"]*)\"|\{`([^`]*)`\})")


def check(src_dir: Path) -> int:
    violations = 0
    checked = 0

    for path in sorted(src_dir.rglob("*.tsx")):
        text = path.read_text(encoding="utf8", errors="ignore")
        for m in CLASSNAME.finditer(text):
            cls = m.group(1) or m.group(2) or ""
            checked += 1
            line = text[: m.start()].count("\n") + 1
            rel = path.relative_to(src_dir.parent)

            fills_inverting = any(
                f"bg-[color:var({tok})]" in cls for tok in INVERTING
            )
            if fills_inverting and FIXED_TEXT.search(cls):
                violations += 1
                print(f"FAIL {rel}:{line}")
                print("     inverting bg token behind fixed text color "
                      "— invisible in one theme")
                print(f"     {cls[:110]}")

            if PALETTE.search(cls):
                violations += 1
                print(f"FAIL {rel}:{line}")
                print("     hard-coded palette color, not a theme token")
                print(f"     {cls[:110]}")

    # Vacuity guard: a lint that scanned nothing must not report success.
    if checked == 0:
        print(f"FAIL scanned 0 className blocks under {src_dir} "
              "— wrong path or glob, this is not a pass")
        return 1

    print(f"\n{checked} className blocks checked, {violations} violation(s)")
    return 1 if violations else 0


if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "src")
    if not root.is_dir():
        print(f"no such directory: {root}")
        sys.exit(2)
    sys.exit(check(root))
