"""
Bootstrap — run dbt to materialise the capital_position model and the
MetricFlow time spine into capital_bfsi.duckdb.

Runs dbt run + mf validate-configs. Only needs to run once.

Usage:
    cd code/
    python3 bootstrap_metrics.py
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────

import os
import sys
import subprocess

DBT_PROJECT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../dbt_project")
)

def run(cmd: list[str], label: str) -> None:
    print(f"\n[{label}]")
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=DBT_PROJECT, capture_output=False)
    if result.returncode != 0:
        print(f"\nERROR: '{label}' failed (exit {result.returncode})")
        sys.exit(1)

def main() -> None:
    print("=" * 60)
    print("CE Example 9 — dbt Metric Layer Bootstrap")
    print(f"Project : {DBT_PROJECT}")
    print("=" * 60)

    # Step 1 — materialise models
    run(["dbt", "run", "--profiles-dir", "."], "dbt run")

    # Step 2 — validate MetricFlow configs
    run(["mf", "validate-configs"], "mf validate-configs")

    print("\n" + "=" * 60)
    print("Bootstrap complete.")
    print()
    print("Metrics defined:")
    print("  cet1_ratio              — CET1 Capital / RWA × 100 (%)")
    print("  combined_buffer_req     — Combined Buffer Requirement (%)")
    print("  cet1_capital            — CET1 Capital (MM)")
    print("  rwa                     — Risk-Weighted Assets (MM)")
    print("  buffer_headroom         — CET1 Ratio − Combined Buffer (pp)")
    print()
    print("Try a query:")
    print("  mf query --metrics cet1_ratio,buffer_headroom --group-by metric_time__month")
    print()
    print("Or run the agent:")
    print("  python3 agent_metrics_ollama.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
