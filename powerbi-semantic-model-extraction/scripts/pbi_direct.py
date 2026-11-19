#!/usr/bin/env python3
"""
Minimal direct client for a Power BI / Fabric MCP semantic model.

Talks straight to the Fabric MCP HTTP endpoint with an `az` token, bypassing any
stdio proxy that depends on another app's OAuth cache. Handles the two things
that silently break naive clients:

  1. The endpoint answers as SSE - the JSON-RPC payload is on a `data:` line.
  2. Tool results are a JSON *string* nested in result.content[].text - double decode.

Set MODEL_ID / REPORT_ID in this starter for your model.
Set PBI_SUBSCRIPTION_ID and PBI_TENANT_ID from a verified cached Azure account;
the helper deliberately refuses to inherit the ambient Azure CLI identity.

    python3 pbi_direct.py schema                 # every table, column, measure
    python3 pbi_direct.py dax  "<DAX>"           # preview (truncates - probing only)
    python3 pbi_direct.py csv  "<DAX>" out.csv   # FULL result, use this for real work

Never rely on the `dax` preview for analysis: stdout truncation produces a
JSONDecodeError at a byte offset that looks like a server fault and is not.
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request

ENDPOINT = "https://api.fabric.microsoft.com/v1/mcp/powerbi"
RESOURCE = "https://api.fabric.microsoft.com"
MODEL_ID = ""    # semantic model artifactId
REPORT_ID = ""   # reportObjectId (NOT the portal URL GUID - see skill Step 2)


def token():
    """Use an explicitly verified identity, never the ambient Azure default."""
    subscription = os.environ.get('PBI_SUBSCRIPTION_ID')
    tenant = os.environ.get('PBI_TENANT_ID')
    if not subscription or not tenant:
        raise RuntimeError('Set PBI_SUBSCRIPTION_ID and PBI_TENANT_ID from '
                           'az account list --all for the intended report identity')
    tok = subprocess.run(
        ["az", "account", "get-access-token", "--subscription", subscription,
         "--resource", RESOURCE, "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True, check=True, timeout=60).stdout.strip()
    # Identity sanity check only; Fabric verifies the signature.
    try:
        part = tok.split('.')[1]
        claims = json.loads(base64.urlsafe_b64decode(part + '=' * (-len(part) % 4)))
        valid = (claims.get('tid') == tenant and claims.get('aud') == RESOURCE
                 and claims.get('exp', 0) > time.time() + 60)
    except (ValueError, IndexError, TypeError):
        valid = False
    if not valid:
        raise RuntimeError('Fabric token tenant/audience/expiry check failed')
    return tok


def call(method, params, tok=None, timeout=180):
    tok = tok or token()
    body = json.dumps({"jsonrpc": "2.0", "id": 1,
                       "method": method, "params": params}).encode()
    req = urllib.request.Request(ENDPOINT, data=body, headers={
        "Authorization": f"Bearer {tok}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    })
    raw = urllib.request.urlopen(req, timeout=timeout).read().decode()

    payload = None
    for line in raw.splitlines():          # SSE unwrap
        if line.startswith("data:"):
            payload = json.loads(line[5:].strip())
            break
    if payload is None:
        payload = json.loads(raw)
    if "error" in payload:
        raise RuntimeError(payload["error"])

    result = payload.get("result", {})
    for block in result.get("content", []):   # nested JSON string
        if block.get("type") == "text":
            try:
                return json.loads(block["text"])
            except json.JSONDecodeError:
                return block["text"]
    return result


def tool(name, args, tok=None):
    return call("tools/call", {"name": name, "arguments": args}, tok)


def run_dax(q, tok=None):
    """Execute DAX -> (headers, rows). Raises on the MCP's own error strings."""
    r = tool("ExecuteQuery", {"artifactId": MODEL_ID, "daxQueries": [q]}, tok)
    if isinstance(r, str):
        raise RuntimeError(r[:500])
    tables = r.get("executionResult", {}).get("tables", [])
    if not tables:
        raise RuntimeError(json.dumps(r)[:500])
    t = tables[0]
    return [c["name"] for c in t.get("columns", [])], t.get("rows", [])


def cmd_schema():
    """Dump the FULL surface. A report tab shows a fraction of what exists."""
    s = tool("GetSemanticModelSchema", {"artifactId": MODEL_ID})
    tables = s.get("schema", {}).get("Tables", []) if isinstance(s, dict) else []
    if not tables:
        print(json.dumps(s, indent=2)[:4000])
        return
    total = 0
    for t in tables:
        cols = [c.get("Name") for c in t.get("Columns", [])]
        meas = [m.get("Name") for m in t.get("Measures", [])]
        total += len(meas)
        print(f"\n=== TABLE {t.get('Name')} ({len(cols)} cols, {len(meas)} measures) ===")
        if cols:
            print("  COLUMNS :", ", ".join(sorted(filter(None, cols))))
        for m in sorted(filter(None, meas)):
            print("     -", m)
    print(f"\nTOTAL: {len(tables)} tables, {total} measures")


def cmd_dax(q):
    h, rows = run_dax(q)
    print(json.dumps({"columns": h, "rowCount": len(rows)}, indent=2))
    for r in rows[:25]:
        print(r)


def cmd_csv(q, out):
    import csv as _csv
    h, rows = run_dax(q)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = _csv.writer(fh)
        w.writerow(h)
        w.writerows(rows)
    # Assert this against your expected population - silent row-cap truncation
    # returns a plausible-looking SHORT result with no error.
    print(f"{len(rows)} rows -> {out}")
    print("columns:", ", ".join(h))


if __name__ == "__main__":
    if len(sys.argv) < 2 or not MODEL_ID:
        print(__doc__)
        sys.exit(1)
    c = sys.argv[1]
    if c == "schema":
        cmd_schema()
    elif c == "dax":
        cmd_dax(sys.argv[2])
    elif c == "csv":
        cmd_csv(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
        sys.exit(1)
