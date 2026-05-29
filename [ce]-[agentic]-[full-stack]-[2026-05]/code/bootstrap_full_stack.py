"""
Bootstrap — seed capital_bfsi.duckdb for the full stack comparison demo.

Also validates that all sibling example context files are present.

Usage:
    python3 bootstrap_full_stack.py
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/amitnoida/
# ─────────────────────────────────────────────────────

import os
import sys
import duckdb

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE    = os.path.join(SCRIPT_DIR, "capital_bfsi.duckdb")

REQUIRED = {
    "YAML contract":  "../../[ce]-[hello-world]-[2026-05]/code/contracts/capital_risk.yaml",
    "ODCS contract":  "../../[ce]-[odcs]-[bfsi]-[2026-05]/code/contracts/capital_risk_odcs.yaml",
    "OWL ontology":   "../../[ce]-[ontology]-[bfsi]-[2026-05]/ontology/bfsi_capital.ttl",
    "dbt project":    "../../[ce]-[metrics]-[bfsi]-[2026-05]/dbt_project",
    "MetricFlow DB":  "../../[ce]-[metrics]-[bfsi]-[2026-05]/dbt_project/capital_bfsi.duckdb",
}

def main() -> None:
    print("=" * 60)
    print("CE Example 10 — Full Stack Bootstrap")
    print("=" * 60)

    # Check prerequisites
    print("\n[1/2] Checking sibling example prerequisites ...")
    missing = []
    for label, rel_path in REQUIRED.items():
        abs_path = os.path.normpath(os.path.join(SCRIPT_DIR, rel_path))
        status   = "✅" if os.path.exists(abs_path) else "❌"
        print(f"  {status}  {label}")
        if status == "❌":
            missing.append(f"     {abs_path}")

    if missing:
        print("\nERROR: Missing files. Run bootstrap for these examples first:")
        for m in missing:
            print(m)
        print("\n  Example 1 : cd [ce]-[hello-world]-[2026-05]/code && python3 bootstrap.py")
        print("  Example 4 : cd [ce]-[odcs]-[bfsi]-[2026-05]/code && python3 bootstrap_odcs.py")
        print("  Example 8 : (ontology file is checked in — no bootstrap needed)")
        print("  Example 9 : cd [ce]-[metrics]-[bfsi]-[2026-05]/code && python3 bootstrap_metrics.py")
        sys.exit(1)

    # Seed local DuckDB
    print(f"\n[2/2] Seeding {DB_FILE} ...")
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
    print(f"  Seeded {count} rows → capital_position")

    print("\n" + "=" * 60)
    print("Bootstrap complete. Run the comparison:")
    print("  python3 run_comparison.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
