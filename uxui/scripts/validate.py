#!/usr/bin/env python3
"""uxui v2.1 static validator — checkable constraints, not taste prose.

    python3 validate.py artifact.html [--json]

Exit 0 = pass (warnings allowed), 1 = ERROR present, 2 = usage.
Catches the failure modes GPT-5.6-sol identified as agent-specific: raw colors in
component CSS, theme flash, unreachable states for bundled data, invented data,
missing reduced-motion, chart lies (dual axis, pie slices, smoothing), a11y gaps.
"""
import re, sys, json

ERR, WARN = "ERROR", "WARN"

def styles(h):
    return "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", h, re.S | re.I))

def scripts(h):
    return "\n".join(re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", h, re.S | re.I))

def body(h):
    m = re.search(r"<body[^>]*>(.*)</body>", h, re.S | re.I)
    return m.group(1) if m else h

def manifest(h):
    for c in re.findall(r"<!--(.*?)-->", h, re.S):
        if "artifact_class:" in c:
            return c
    return None


def check(html, path):
    out = []
    def add(sev, code, msg):
        out.append({"sev": sev, "code": code, "msg": msg})

    css, js, bod = styles(html), scripts(html), body(html)
    head = html[:html.lower().find("<body")] if "<body" in html.lower() else html

    # --- 1. Manifest -------------------------------------------------------
    man = manifest(html)
    if not man:
        add(ERR, "M001", "No artifact manifest comment. Declare artifact_class/audience/"
                         "primary_question/data_lifecycle/provenance before generating markup.")
        cls, lifecycle = None, None
    else:
        cls = (re.search(r"artifact_class:\s*(\w+)", man) or [None, None])[1]
        lifecycle = (re.search(r"data_lifecycle:\s*(\w+)", man) or [None, None])[1]
        if cls not in {"executive", "operational", "analytical", "narrative", "report"}:
            add(ERR, "M002", f"artifact_class '{cls}' is not one of the five archetypes.")
        if not lifecycle:
            add(ERR, "M003", "manifest missing data_lifecycle (bundled|fetched|live) — "
                             "it determines which states are reachable.")
        if "provenance" not in man:
            add(WARN, "M004", "manifest has no provenance block (supplied/derived/assumptions).")

    # --- 2. Tokens: no raw color in component CSS --------------------------
    decl = re.sub(r"(:root|\[data-theme=[^\]]+\]|\[data-brand=[^\]]+\])\s*\{.*?\}", "", css, flags=re.S)
    decl = re.sub(r"@media\s+print\s*\{.*?\n\}", "", decl, flags=re.S)
    for m in re.finditer(r"(#[0-9a-fA-F]{3,8}\b|\brgba?\([^)]*\)|\bhsla?\([^)]*\))", decl):
        val = m.group(1)
        if val.lower() in {"#fff", "#ffffff", "#000", "#000000"}:
            continue
        line = decl[:m.start()].count("\n") + 1
        add(ERR, "T001", f"raw color '{val}' in component CSS (~line {line} of style block). "
                         "Components must use semantic tokens only.")
    # widths/heights/breakpoints are layout geometry, not spacing tokens — only flag
    # spacing/padding/margin/gap/radius, which is what the scale actually governs.
    for m in re.finditer(r"\b(padding|margin|gap|border-radius)(?:-\w+)?\s*:\s*([^;{}]+)", decl):
        for px in re.findall(r"(\d+)px", m.group(2)):
            if px not in {"0", "1", "2", "3"}:
                add(WARN, "T002", f"hardcoded {px}px in {m.group(1)} — use the spacing/radius scale.")

    # --- 3. Theme ----------------------------------------------------------
    if "data-theme" not in html:
        add(ERR, "H001", "no data-theme support — every artifact ships both themes.")
    if 'data-theme="light"' not in css and "[data-theme=light]" not in css:
        add(ERR, "H002", "no light-theme token block.")
    if "prefers-color-scheme" not in head:
        add(ERR, "H003", "theme not resolved in <head> — light users will see a dark flash.")
    elif "prefers-color-scheme" in js and "prefers-color-scheme" not in head:
        add(ERR, "H004", "theme resolution runs after first paint.")
    if "color-scheme:" not in css.replace(" ", "") and "color-scheme :" not in css:
        add(WARN, "H005", "no `color-scheme` declaration — native controls/scrollbars "
                          "will not follow the theme (the meta tag does not do this).")
    if re.search(r"matchMedia\([^)]*\)\s*;?\s*$", js, re.M) is None and "addEventListener('change'" not in js.replace('"', "'"):
        add(WARN, "H006", "no matchMedia change listener — 'auto' will not follow OS changes.")

    # --- 4. Motion / a11y --------------------------------------------------
    if "prefers-reduced-motion" not in css:
        add(ERR, "A001", "missing prefers-reduced-motion block (mandatory).")
    elif "animation-duration" in css.split("prefers-reduced-motion")[1][:400]:
        add(WARN, "A002", "reduced-motion uses animation-duration:.01ms — infinite animations "
                          "keep running. Use `animation:none`.")
    if "[tabindex]" in css and '[tabindex]:not([tabindex^="-"])' not in css:
        add(ERR, "A003", 'focus selector matches [tabindex="-1"] containers. '
                         'Use [tabindex]:not([tabindex^="-"]).')
    if ":focus-visible" not in css:
        add(ERR, "A004", "no :focus-visible styling — keyboard users get no focus indicator.")
    for m in re.finditer(r"<button\b((?:(?!</button>).)*?)>((?:(?!</button>).)*)</button>", bod, re.S):
        attrs, inner = m.group(1), m.group(2)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        if not text and "aria-label" not in attrs:
            add(ERR, "A005", "icon-only <button> without aria-label.")
    for m in re.finditer(r'role=["\']button["\']', bod):
        add(WARN, "A006", "role=button is not keyboard-operable by itself — prefer <button>.")

    # --- 5. Charts ---------------------------------------------------------
    if re.search(r"yAxis\s*:\s*\[", js) and re.search(r"xAxis\s*:\s*\{", js):
        add(ERR, "C001", "two y-axes detected — dual axis manufactures correlation. "
                         "Use indexed lines or aligned small multiples.")
    if "smooth:true" in js.replace(" ", "") and "interpolation:" not in (man or ""):
        add(ERR, "C002", "smooth:true without a justified `interpolation:` in the manifest — "
                         "smoothing invents unmeasured values.")
    if "connectNulls:true" in js.replace(" ", ""):
        add(ERR, "C003", "connectNulls:true bridges missing data — missing must render as a gap.")
    if re.search(r"type\s*:\s*['\"]pie['\"]", js):
        add(WARN, "C004", "pie chart — allowed only at <=4 slices with a center total (donut).")
    if "type:'bar'" in js.replace(" ", "") or 'type:"bar"' in js.replace(" ", ""):
        if "min:" in js and re.search(r"min\s*:\s*(?!0)", js):
            add(WARN, "C005", "bar chart with non-zero value-axis min — the value axis "
                              "(x on horizontal bars) must start at zero.")
    if "setOption(" in js and "notMerge" not in js:
        add(WARN, "C006", "setOption without {notMerge:true} — theme switches will leave "
                          "stale colors in series/legend/markLine.")
    if "getDataURL" in js and "beforeprint" not in js:
        add(WARN, "C007", "getDataURL present but no beforeprint swap — it returns a string, "
                          "it does not make the canvas printable.")
    if "echarts.init" in js and "ResizeObserver" not in js:
        add(WARN, "C008", "no ResizeObserver — window resize misses container-driven resizes.")
    if re.search(r"\+\s*['\"]40['\"]|\+\s*['\"]00['\"]", js):
        add(ERR, "C009", "hex-alpha string concat (color+'40') — breaks on hsl()/rgb()/var(). "
                         "Use the alpha() helper.")

    # --- 6. Unreachable states / invented data (agent-specific) ------------
    if lifecycle == "bundled":
        # the .skeleton CLASS ships in core CSS for all archetypes; only its USE in
        # markup is the defect.
        if re.search(r"class=[\"'][^\"']*\bskeleton\b", bod):
            add(ERR, "S001", "skeleton loader used with data_lifecycle: bundled — unreachable state.")
        if re.search(r">\s*(retry|try again|reconnect)\s*<", bod, re.I):
            add(ERR, "S002", "retry/reconnect control with bundled data — dead control.")
    if re.search(r"last\s*updated", bod, re.I) and not re.search(
            r"id=[\"']updated[\"']|toLocale|Date\(|\{\{", bod):
        add(WARN, "D001", "static 'last updated' text with no real timestamp binding.")
    for lit in re.findall(r">\s*([+-]\d{1,3}(?:\.\d+)?%)\s*<", bod):
        add(WARN, "D002", f"hardcoded delta '{lit}' — deltas must be derived from supplied data.")
    if re.search(r"lorem ipsum|Example Corp|John Doe|foo@bar", bod, re.I):
        add(ERR, "D003", "placeholder content present and not visibly labeled as placeholder.")

    # --- 7. Structural inflation ------------------------------------------
    navs = re.findall(r"<(?:nav|aside)[^>]*class=[\"'][^\"']*sidebar", bod)
    if navs:
        links = len(re.findall(r"<a\b", bod))
        if links < 3:
            add(WARN, "L001", "sidebar with fewer than 3 destinations — drop it.")
    tabs = re.findall(r"role=[\"']tab[\"']", bod)
    if 0 < len(tabs) < 2:
        add(WARN, "L002", "tab UI with a single tab.")
    if cls == "operational" and "overrides" not in (man or ""):
        add(WARN, "O001", "operational archetype without an overrides block — 'one hero' and "
                          "single-density defaults do not apply here; state the override.")
    if cls == "narrative" and re.search(r"class=[\"'][^\"']*\bstrip\b", bod):
        add(WARN, "O002", "narrative artifact using a KPI strip — use editorial beats, not cards.")

    return out


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    as_json = "--json" in sys.argv
    paths = [a for a in sys.argv[1:] if not a.startswith("--")]
    failed = False
    report = {}
    for p in paths:
        with open(p, encoding="utf-8") as f:
            res = check(f.read(), p)
        report[p] = res
        errs = [r for r in res if r["sev"] == ERR]
        failed = failed or bool(errs)
        if not as_json:
            print(f"\n=== {p} ===")
            if not res:
                print("  PASS — no findings")
            for r in res:
                print(f"  [{r['sev']:5}] {r['code']}  {r['msg']}")
            print(f"  -> {len(errs)} error(s), {len(res)-len(errs)} warning(s)")
    if as_json:
        print(json.dumps(report, indent=2))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
