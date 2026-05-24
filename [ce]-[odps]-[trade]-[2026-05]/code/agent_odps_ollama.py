"""
Trade Finance Exposure Agent — ODPS edition, Ollama (qwen2.5).

Reads an Open Data Product Standard (ODPS 2.0) product definition and
uses it as the agent's context. Demonstrates CE at the data product level —
one level above a data contract (ODCS) or hand-written YAML.

The agent extracts context from the product definition:
  - Product description and domain (what capability does this serve?)
  - Owner and team (who is responsible?)
  - Use cases (what questions is this product built to answer?)
  - Output port table definitions and column descriptions
  - SLA properties (how fresh and reliable is the data?)
  - Data quality checks (is the data certified?)
  - Usage terms (what are the rules of engagement?)

New domain: Trade Finance (counterparty exposure, settlement risk).
Shows CE is not BFSI capital adequacy-specific.

Requires:
  - Ollama running:  ollama serve && ollama pull qwen2.5
  - Bootstrap done:  python bootstrap_odps.py

Usage:
    python agent_odps_ollama.py
    python agent_odps_ollama.py > trace.jsonl
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/amitnoida/
# ─────────────────────────────────────────────────────

import json
import yaml
import duckdb
import structlog
from datetime import datetime, timezone
from openai import OpenAI

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()

DB_FILE      = "trade_odps.duckdb"
PRODUCT_FILE = "products/trade_exposure_product.yaml"
OLLAMA_MODEL = "qwen2.5"
QUESTION     = (
    "What is our total trade exposure by counterparty for all open trades? "
    "Which trades are settling within the next 30 days? "
    "Is this data fresh and who is responsible for it?"
)

# --- Load ODPS product definition and extract context ---
with open(PRODUCT_FILE) as f:
    product_def = yaml.safe_load(f)

product    = product_def["product"]
owner      = product["owner"]
slas       = product.get("slaProperties", [])
terms      = product.get("terms", {})
use_cases  = product.get("useCases", [])
quality    = product.get("dataQuality", [])

# Output port — where the data lives
output_port = product["outputPorts"][0]
table_def   = output_port["tables"][0]
columns     = table_def["columns"]

# Build product-level context summary
sla_summary = "; ".join(
    f"{s['dimension']}: {s['value']} ({s['description']})"
    for s in slas
)
use_case_summary = "; ".join(use_cases)
quality_summary  = "; ".join(
    f"{q['dimension']}: {', '.join(q['checks'][:2])}"
    for q in quality
)

product_context = (
    f"Data product: '{product['name']}' v{product['version']} "
    f"[domain: {product['domain']}, status: {product['status']}]. "
    f"Owner: {owner['name']} <{owner['email']}>. "
    f"Use cases: {use_case_summary}. "
    f"SLAs: {sla_summary}. "
    f"Quality: {quality_summary}. "
    f"Usage: {terms.get('usage', '').strip()}"
)

# Build column descriptions from product definition
column_descriptions = "\n".join(
    f"  - {col['name']} ({col['type']}): {col['description'].strip()}"
    for col in columns
)

table_description = table_def["description"].strip()

log.info(
    "agent.start",
    question=QUESTION,
    product=PRODUCT_FILE,
    odps_version=product_def["openDataProductSpecification"],
    product_status=product["status"],
    product_domain=product["domain"],
    product_owner=owner["email"],
    ollama_model=OLLAMA_MODEL,
)

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

tools = [
    {
        "type": "function",
        "function": {
            "name": "query_trade_exposure",
            "description": (
                f"Query the trade_exposure table from the '{product['name']}' data product. "
                f"{table_description} "
                f"Product context: {product_context} "
                f"Columns:\n{column_descriptions}"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": (
                            "A SQL SELECT query against the trade_exposure table. "
                            "For open trades use: WHERE status = 'OPEN'. "
                            "For settlement risk use: WHERE settlement_date <= CURRENT_DATE + INTERVAL 30 DAY. "
                            "For exposure totals use: SUM(notional_usd_mm) GROUP BY counterparty. "
                            "Always ORDER BY for readability."
                        ),
                    }
                },
                "required": ["sql"],
            },
        },
    }
]

# --- Turn 1: agent decides what to query ---
t1_start = datetime.now(timezone.utc)
response = client.chat.completions.create(
    model=OLLAMA_MODEL,
    tools=tools,
    messages=[{"role": "user", "content": QUESTION}],
)
msg = response.choices[0].message
log.info(
    "agent.turn1",
    stop_reason=response.choices[0].finish_reason,
    latency_ms=int((datetime.now(timezone.utc) - t1_start).total_seconds() * 1000),
)

if not msg.tool_calls:
    print("\n" + "=" * 60)
    print(msg.content)
    print("=" * 60)
    exit(0)

# --- Tool execution: query DuckDB ---
tool_call = msg.tool_calls[0]
args      = json.loads(tool_call.function.arguments)
sql       = args.get("sql") or next(iter(args.values()))
log.info("tool.call", sql=sql)

db   = duckdb.connect(DB_FILE, read_only=True)
rows = db.execute(sql).fetchall()
cols = [d[0] for d in db.execute(sql).description]
db.close()

data = [dict(zip(cols, row)) for row in rows]
log.info("tool.result", rows=len(data), data=data)

# --- Turn 2: agent synthesises the answer ---
t2_start = datetime.now(timezone.utc)
final = client.chat.completions.create(
    model=OLLAMA_MODEL,
    tools=tools,
    messages=[
        {"role": "user", "content": QUESTION},
        msg,
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(data, default=str),
        },
        {
            "role": "user",
            "content": "Using the tool result above, answer the question in plain English. Do not call any tools.",
        },
    ],
)
answer = final.choices[0].message.content

answer = final.choices[0].message.content

# Guard: model made another tool call instead of answering
if not answer and final.choices[0].message.tool_calls:
    answer = "(Model issued a second tool call instead of answering. Raw tool args: " \
             + json.dumps([json.loads(tc.function.arguments) for tc in final.choices[0].message.tool_calls]) + ")"

# Guard: model returned nothing
if not answer:
    answer = "(No answer generated — check model tool_calls loop or increase context)"

log.info(
    "agent.answer",
    latency_ms=int((datetime.now(timezone.utc) - t2_start).total_seconds() * 1000),
)

print("\n" + "=" * 60)
print(answer)
print("=" * 60)
