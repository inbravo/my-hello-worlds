"""
Register capital_bfsi datasource and ingest capital_position model
into SLayer's default storage for MCP access.

Unlike setup_bfsi.py (which targets the REST server at port 5143),
this script writes directly to SLayer's default YAML storage so the
MCP server picks it up without needing the REST server running.

Run once after bootstrap_mcp_bfsi.py, before starting Claude Desktop.

Usage:
    python setup_mcp_bfsi.py
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────

import os
import sys
import requests

SLAYER_BASE = "http://127.0.0.1:5143"
DS_NAME     = "capital_bfsi"
DB_FILE     = "capital_bfsi.duckdb"
TABLE       = "capital_position"

db_path = os.path.abspath(DB_FILE)

if not os.path.exists(db_path):
    print(f"ERROR: {db_path} not found — run bootstrap_mcp_bfsi.py first.")
    sys.exit(1)

print(f"\n[1/3] Checking SLayer REST server at {SLAYER_BASE} ...")
try:
    resp = requests.get(f"{SLAYER_BASE}/datasources", timeout=3)
    resp.raise_for_status()
except Exception:
    print(
        f"\nERROR: SLayer REST server not running at {SLAYER_BASE}.\n"
        f"Start it first:\n"
        f"  uvx --from 'motley-slayer[all]' slayer serve\n"
        f"Then re-run this script."
    )
    sys.exit(1)

print(f"       Server is up.")

# --- Step 1: Register datasource ---
print(f"\n[2/3] Registering datasource '{DS_NAME}' → {db_path}")

existing = [d["name"] for d in requests.get(f"{SLAYER_BASE}/datasources").json()]
if DS_NAME in existing:
    print(f"       Already registered — skipping.")
else:
    resp = requests.post(f"{SLAYER_BASE}/datasources", json={
        "name":     DS_NAME,
        "type":     "duckdb",
        "database": db_path,
    })
    if not resp.ok:
        print(f"ERROR: {resp.status_code} — {resp.text}")
        sys.exit(1)
    print(f"       Done: {resp.json()}")

# --- Step 2: Auto-ingest model ---
print(f"\n[3/3] Ingesting model '{TABLE}' from '{DS_NAME}'")

resp = requests.post(f"{SLAYER_BASE}/ingest", json={
    "datasource":     DS_NAME,
    "include_tables": [TABLE],
})
if not resp.ok:
    print(f"ERROR: {resp.status_code} — {resp.text}")
    sys.exit(1)

model = requests.get(
    f"{SLAYER_BASE}/models/{TABLE}",
    params={"data_source": DS_NAME}
).json()
columns = [c["name"] for c in model.get("columns", [])]
print(f"       Columns : {columns}")
print(f"       Source  : {model.get('data_source')}")

print(f"""
Setup complete. The capital_bfsi datasource is now registered in
SLayer's default storage (~/.local/share/slayer).

Next steps:
  1. Stop the REST server (Ctrl+C)
  2. Add the MCP config to Claude Desktop:
       config/claude_desktop_bfsi.json
  3. Restart Claude Desktop
  4. Ask: "What is our current CET1 ratio and buffer headroom?"
""")
