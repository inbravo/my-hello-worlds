"""
CE Example 9 — dbt Metric Layer Agent (Ollama / qwen2.5)

What this demo adds over Example 8 (Ontology):
  - Metrics are not raw columns or ontology concepts.
  - They are named, governed, versioned business definitions in the dbt
    Semantic Layer (MetricFlow YAML) — with owners, formulas, regulatory
    references, and descriptions baked into the catalogue.
  - The agent does not write SQL. It calls MetricFlow (mf query) via
    subprocess — the metric layer compiles the SQL, enforces the definition,
    and returns a typed result.
  - Any downstream consumer (BI tool, another agent, this script) gets the
    same number from the same governed definition. One metric. One truth.

Metrics available:
  cet1_ratio              — CET1 Ratio (%) — Basel III Article 92
  combined_buffer_req     — Combined Buffer Requirement (%)
  cet1_capital            — CET1 Capital (MM)
  rwa                     — Risk-Weighted Assets (MM)
  buffer_headroom         — CET1 Ratio − Combined Buffer (pp) — derived

Run order:
    python3 bootstrap_metrics.py  (once)
    python3 agent_metrics_ollama.py

Usage:
    python3 agent_metrics_ollama.py
    python3 agent_metrics_ollama.py "Show CET1 ratio trend by quarter"
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/amitnoida/
# ─────────────────────────────────────────────────────

import os
import sys
import json
import subprocess
import textwrap
import structlog
from openai import OpenAI

log = structlog.get_logger()

OLLAMA_BASE  = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen2.5"
DBT_PROJECT  = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../dbt_project")
)

DEFAULT_QUESTION = (
    "What is our current CET1 ratio and buffer headroom, "
    "and how have they trended over the last three quarters?"
)

# ── Metric catalogue (mirrors schema.yml) ────────────────────────
METRICS = {
    "cet1_ratio": {
        "label":       "CET1 Ratio (%)",
        "description": (
            "Primary Basel III capital adequacy measure. "
            "Formula: CET1 Capital / RWA × 100. "
            "Regulatory minimum: 4.5% (Basel III Article 92). "
            "Owner: Treasury Risk. Certified for regulatory reporting."
        ),
        "type": "simple",
    },
    "combined_buffer_requirement": {
        "label":       "Combined Buffer Requirement (%)",
        "description": (
            "Total CET1 buffer required above the 4.5% minimum. "
            "Sum of capital conservation buffer (fixed 2.5%) plus any "
            "countercyclical and systemic risk buffers in force. "
            "Governed by Basel III Article 128-131."
        ),
        "type": "simple",
    },
    "cet1_capital": {
        "label":       "CET1 Capital (MM)",
        "description": (
            "Total CET1 Capital in millions. Highest quality regulatory capital — "
            "ordinary shares, retained earnings, net of regulatory deductions. "
            "Governed by Basel III Article 26-50."
        ),
        "type": "simple",
    },
    "rwa": {
        "label":       "Risk-Weighted Assets (MM)",
        "description": (
            "Total Risk-Weighted Assets in millions. Denominator of all Basel "
            "capital ratios — assets weighted by credit, market, and operational risk."
        ),
        "type": "simple",
    },
    "buffer_headroom": {
        "label":       "Buffer Headroom (pp)",
        "description": (
            "Excess CET1 Ratio above the Combined Buffer Requirement, in percentage points. "
            "Positive = compliant. Negative = Basel III Article 141 triggers automatic "
            "restrictions on dividends, share buybacks, and bonus payments. "
            "Formula: CET1 Ratio (%) − Combined Buffer Requirement (%)."
        ),
        "type": "derived",
    },
}

DIMENSIONS = {
    "metric_time__month": "Quarter-end month (groups results by reporting period)",
    "entity":             "Legal entity (BANK_HOLDCO)",
}


# ── Build metric catalogue context ───────────────────────────────
def build_metric_context() -> str:
    lines = ["=== dbt Metric Layer — BFSI Capital Adequacy Catalogue ===\n"]
    for name, meta in METRICS.items():
        lines.append(
            f"Metric     : {name}\n"
            f"  Label    : {meta['label']}\n"
            f"  Type     : {meta['type']}\n"
            f"  Definition: {meta['description']}"
        )
    lines.append("\n=== Available Dimensions for group-by ===")
    for dim, desc in DIMENSIONS.items():
        lines.append(f"  {dim:<30} — {desc}")
    lines.append(
        "\n=== Key Governance Rules ===\n"
        "  - Metrics are versioned and owned. cet1_ratio is owned by Treasury Risk.\n"
        "  - The metric layer compiles SQL — consumers never write raw SQL against capital_position.\n"
        "  - buffer_headroom is a derived metric: cet1_ratio − combined_buffer_requirement.\n"
        "  - Any negative buffer_headroom triggers Basel III Article 141 distribution restrictions."
    )
    return "\n\n".join(lines)


# ── Run mf query via subprocess ───────────────────────────────────
def run_mf_query(metrics: list[str], group_by: list[str] | None = None,
                 order_by: list[str] | None = None, limit: int | None = None) -> str:
    cmd = ["mf", "query", "--metrics", ",".join(metrics)]
    if group_by:
        cmd += ["--group-by", ",".join(group_by)]
    if order_by:
        cmd += ["--order", ",".join(order_by)]
    if limit:
        cmd += ["--limit", str(limit)]

    log.info("metrics.mf_query", cmd=" ".join(cmd))

    try:
        result = subprocess.run(
            cmd, cwd=DBT_PROJECT,
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            return f"mf query error:\n{result.stderr.strip()}"
        # Strip spinner/emoji lines, keep the table
        lines = [l for l in output.splitlines() if not l.startswith(("⠋", "⠙", "✔", "⠸", "⠼"))]
        return "\n".join(lines).strip()
    except Exception as e:
        return f"ERROR running mf query: {e}"


# ── Tool definition ───────────────────────────────────────────────
def build_tool(metric_context: str) -> dict:
    metric_names = list(METRICS.keys())
    dim_names    = list(DIMENSIONS.keys())

    return {
        "type": "function",
        "function": {
            "name": "query_metric",
            "description": textwrap.dedent(f"""
                Query one or more governed business metrics from the dbt Metric Layer
                using MetricFlow. Do NOT write SQL — the metric layer compiles it.

                Available metrics (use exact names):
                {chr(10).join(f'  - {n}' for n in metric_names)}

                Available group-by dimensions:
                {chr(10).join(f'  - {d}' for d in dim_names)}

                ── METRIC CATALOGUE CONTEXT ─────────────────────────────
                {metric_context}
                ─────────────────────────────────────────────────────────
            """).strip(),
            "parameters": {
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": f"One or more metric names. Choose from: {metric_names}"
                    },
                    "group_by": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": f"Dimensions to group by. Choose from: {dim_names}"
                    },
                    "order_by": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional ordering. Use metric or dimension names, prefix with '-' for descending."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Optional row limit."
                    }
                },
                "required": ["metrics"]
            }
        }
    }


# ── Two-turn agent loop ───────────────────────────────────────────
def ask(question: str, tool: dict, client: OpenAI) -> None:
    log.info("metrics.question", q=question)

    t1_messages = [
        {
            "role": "system",
            "content": (
                "You are a Basel III capital adequacy analyst. "
                "You have access to a governed dbt Metric Layer — use the query_metric tool "
                "to retrieve metric values. Never write raw SQL. "
                "For governance questions (ownership, formula, regulation), answer from the "
                "metric catalogue in the tool description without calling the tool."
            )
        },
        {"role": "user", "content": question}
    ]

    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=t1_messages,
        tools=[tool],
        tool_choice="auto"
    )
    msg = response.choices[0].message

    # Guard: model answered directly (governance question, no metric query needed)
    if not msg.tool_calls:
        print("\n" + "=" * 60)
        print(msg.content)
        print("=" * 60)
        return

    tool_call = msg.tool_calls[0]
    params    = json.loads(tool_call.function.arguments)

    metrics  = params.get("metrics", [])
    group_by = params.get("group_by")
    order_by = params.get("order_by")
    limit    = params.get("limit")

    log.info("metrics.tool_call", metrics=metrics, group_by=group_by)
    result = run_mf_query(metrics, group_by, order_by, limit)
    log.info("metrics.result", preview=result[:300])

    # Turn 2 — synthesise answer
    t2_messages = t1_messages + [
        {"role": "assistant",  "content": None, "tool_calls": [tool_call]},
        {"role": "tool",       "content": result, "tool_call_id": tool_call.id},
        {
            "role": "user",
            "content": (
                "Using the metric query result above and the metric catalogue context "
                "in your tool description, answer the question in plain English. "
                "Reference metric definitions, Basel III thresholds, and governance "
                "details where relevant. Do not call any tools."
            )
        }
    ]

    final  = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=t2_messages,
        tools=[tool],
        tool_choice="none"
    )
    answer = final.choices[0].message.content

    if not answer and final.choices[0].message.tool_calls:
        answer = "(Model issued a second tool call instead of answering — try a simpler question.)"
    if not answer:
        answer = "(No answer generated.)"

    print("\n" + "=" * 60)
    print(answer)
    print("=" * 60)


# ── Main ──────────────────────────────────────────────────────────
def main() -> None:
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_QUESTION

    if not os.path.isdir(DBT_PROJECT):
        print(f"ERROR: dbt project not found at {DBT_PROJECT}")
        sys.exit(1)

    if not os.path.exists(os.path.join(DBT_PROJECT, "capital_bfsi.duckdb")):
        print("ERROR: capital_bfsi.duckdb not found — run bootstrap_metrics.py first.")
        sys.exit(1)

    metric_context = build_metric_context()
    tool   = build_tool(metric_context)
    client = OpenAI(base_url=OLLAMA_BASE, api_key="ollama")

    ask(question, tool, client)


if __name__ == "__main__":
    main()
