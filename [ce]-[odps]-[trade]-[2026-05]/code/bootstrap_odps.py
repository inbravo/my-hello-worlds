"""
Bootstrap — seed trade_odps.duckdb with trade exposure data.

Run once before any agent.

Usage:
    python bootstrap_odps.py
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────


import os
import duckdb

DB_FILE = "trade_odps.duckdb"

db = duckdb.connect(DB_FILE)

db.execute("""
CREATE OR REPLACE TABLE trade_exposure (
    trade_id         VARCHAR,
    counterparty     VARCHAR,
    instrument_type  VARCHAR,
    notional_usd_mm  DECIMAL(18,2),
    settlement_date  DATE,
    credit_rating    VARCHAR,
    region           VARCHAR,
    status           VARCHAR
)
""")

db.execute("""
INSERT INTO trade_exposure VALUES
    ('T001', 'GOLDMAN_SACHS',  'FX_FORWARD', 450.00, '2026-05-30', 'AA',  'NORTH_AMERICA', 'OPEN'),
    ('T002', 'DEUTSCHE_BANK',  'BOND',        320.00, '2026-06-15', 'A',   'EUROPE',         'OPEN'),
    ('T003', 'BARCLAYS',       'DERIVATIVE',  180.00, '2026-05-28', 'AA',  'EUROPE',         'OPEN'),
    ('T004', 'JPMORGAN',       'FX_FORWARD',  890.00, '2026-06-01', 'AAA', 'NORTH_AMERICA', 'OPEN'),
    ('T005', 'CREDIT_SUISSE',  'BOND',        220.00, '2026-05-25', 'BB',  'EUROPE',         'OPEN'),
    ('T006', 'CITIBANK',       'DERIVATIVE',  560.00, '2026-06-20', 'A',   'NORTH_AMERICA', 'OPEN'),
    ('T007', 'GOLDMAN_SACHS',  'BOND',        340.00, '2026-07-01', 'AA',  'NORTH_AMERICA', 'OPEN'),
    ('T008', 'HSBC',           'FX_FORWARD',  410.00, '2026-05-29', 'AA',  'EUROPE',         'OPEN'),
    ('T009', 'DEUTSCHE_BANK',  'DERIVATIVE',  150.00, '2026-06-10', 'A',   'EUROPE',         'SETTLED'),
    ('T010', 'BARCLAYS',       'FX_FORWARD',  280.00, '2026-07-15', 'AA',  'EUROPE',         'OPEN')
""")

db.close()

print(f"Created : {DB_FILE}")
print(f"Path    : {os.path.abspath(DB_FILE)}")
print(f"Seeded  : 10 rows → trade_exposure")
print(f"         Counterparties : GOLDMAN_SACHS, DEUTSCHE_BANK, BARCLAYS, JPMORGAN,")
print(f"                          CREDIT_SUISSE, CITIBANK, HSBC")
print(f"         Instruments    : FX_FORWARD, BOND, DERIVATIVE")
print(f"         Regions        : EUROPE, NORTH_AMERICA")
