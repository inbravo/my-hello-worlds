"""
Bootstrap — seed capital_bfsi.duckdb with three quarters of Basel III/IV
capital position data for the ontology CE demo (Example 8).

Identical dataset to Examples 3 and 7 — same data, richer context.

Run once before agent_ontology_ollama.py.

Usage:
    python bootstrap_ontology.py
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────

import os
import duckdb

DB_FILE = "capital_bfsi.duckdb"

db = duckdb.connect(DB_FILE)

db.execute("""
CREATE OR REPLACE TABLE capital_position (
    reporting_date  DATE,
    entity          VARCHAR,
    cet1_capital_mm DECIMAL(18,2),
    rwa_mm          DECIMAL(18,2),
    cet1_ratio_pct  DECIMAL(6,4),
    combined_buffer DECIMAL(6,4)
)
""")

db.execute("""
INSERT INTO capital_position VALUES
    ('2025-09-30', 'BANK_HOLDCO', 27410.00, 190500.00, 14.39, 9.75),
    ('2025-12-31', 'BANK_HOLDCO', 28150.00, 192000.00, 14.66, 9.75),
    ('2026-03-31', 'BANK_HOLDCO', 29273.00, 197400.00, 14.83, 9.75)
""")

count = db.execute("SELECT COUNT(*) FROM capital_position").fetchone()[0]
db.close()

print(f"Created : {DB_FILE}")
print(f"Path    : {os.path.abspath(DB_FILE)}")
print(f"Seeded  : {count} rows → capital_position")
print()
print("Columns:")
print("  reporting_date  → bfsi:col_reporting_date")
print("  entity          → bfsi:col_entity")
print("  cet1_capital_mm → bfsi:CET1Capital")
print("  rwa_mm          → bfsi:RiskWeightedAssets")
print("  cet1_ratio_pct  → bfsi:CET1Ratio")
print("  combined_buffer → bfsi:CombinedBuffer")
