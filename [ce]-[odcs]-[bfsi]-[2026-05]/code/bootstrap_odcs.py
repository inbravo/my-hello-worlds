"""
Bootstrap — seed capital_odcs.duckdb with 3 quarters of capital position data.

Run once before any agent.

Usage:
    python bootstrap_odcs.py
"""

import os
import duckdb

DB_FILE = "capital_odcs.duckdb"

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

db.close()

print(f"Created : {DB_FILE}")
print(f"Path    : {os.path.abspath(DB_FILE)}")
print(f"Seeded  : 3 rows → capital_position")
