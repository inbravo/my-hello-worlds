"""
Trade Finance Exposure Agent — ODPS edition, Anthropic (claude-sonnet-4-6).

Reads an Open Data Product Standard (ODPS 2.0) product definition and
uses it as the agent's context. Demonstrates CE at the data product level.

Requires:
  - ANTHROPIC_API_KEY set
  - Bootstrap done: python bootstrap_odps.py

Usage:
    python agent_odps.py
    python agent_odps.py > trace.jsonl
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────

import json
import yaml
import duckdb
import anthropic
import structlog
from datetime import datetime, timezone

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()

DB_FILE      = "trade_odps.duckdb"
PRODUCT_FILE = "products/trade_exposure_product.yaml"
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

output_port = product["outputPorts"][0]
table_def   = output_port["tables"][0]
columns     = table_def["columns"]

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
)

client = anthropic.Anthropic()

tools = [
    {
        "name": "query_trade_exposure",
        "description": (
            f"Query the trade_exposure table from the '{product['name']}' data product. "
            f"{table_description} "
            f"Product context: {product_context} "
            f"Columns:\n{column_descriptions}"
        ),
        "input_schema": {
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
    }
]

# --- Turn 1: agent decides what to query ---
t1_start = datetime.now(timezone.utc)
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": QUESTION}],
)
log.info(
    "agent.turn1",
    stop_reason=response.stop_reason,
    latency_ms=int((datetime.now(timezone.utc) - t1_start).total_seconds() * 1000),
)

# --- Tool execution: query DuckDB ---
tool_call = next(b for b in response.content if b.type == "tool_use")
sql       = tool_call.input["sql"]
log.info("tool.call", sql=sql)

db   = duckdb.connect(DB_FILE, read_only=True)
rows = db.execute(sql).fetchall()
cols = [d[0] for d in db.execute(sql).description]
db.close()

data = [dict(zip(cols, row)) for row in rows]
log.info("tool.result", rows=len(data), data=data)

# --- Turn 2: agent synthesises the answer ---
t2_start = datetime.now(timezone.utc)
final = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=[
        {"role": "user", "content": QUESTION},
        {"role": "assistant", "content": response.content},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": json.dumps(data, default=str),
                }
            ],
        },
    ],
)
answer = final.content[0].text
log.info(
    "agent.answer",
    latency_ms=int((datetime.now(timezone.utc) - t2_start).total_seconds() * 1000),
)

print("\n" + "=" * 60)
print(answer)
print("=" * 60)
