import duckdb

db = duckdb.connect("context_hw.duckdb")

db.execute("""
    CREATE OR REPLACE TABLE capital_position (
        reporting_date DATE,
        entity        VARCHAR,
        cet1_capital_mm  DECIMAL(18, 2),
        rwa_mm           DECIMAL(18, 2),
        cet1_ratio_pct   DECIMAL(6,  4),
        combined_buffer  DECIMAL(6,  4)
    )
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────
)

db.execute("""
    INSERT INTO capital_position VALUES
        ('2025-09-30', 'BANK_HOLDCO', 27410.00, 190500.00, 14.39, 9.75),
        ('2025-12-31', 'BANK_HOLDCO', 28150.00, 192000.00, 14.66, 9.75),
        ('2026-03-31', 'BANK_HOLDCO', 29273.00, 197400.00, 14.83, 9.75)
""")

count = db.execute("SELECT COUNT(*) FROM capital_position").fetchone()[0]
print(f"Seeded capital_position: {count} rows → context_hw.duckdb")
db.close()
