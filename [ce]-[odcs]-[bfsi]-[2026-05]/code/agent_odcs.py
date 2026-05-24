"""
BFSI Capital Adequacy Agent — ODCS edition, Anthropic (claude-sonnet-4-6).

Upgrades Demo 1 (hand-written YAML contract) to a formal Bitol/ACRYL
Open Data Contract Standard (ODCS 0.9.3) contract.

The agent extracts richer context from the ODCS contract:
  - Business description (what the data means)
  - Governance metadata (owner, status, usage terms)
  - Quality rules (is the data certified?)
  - SLA / freshness (how current is the data?)

Requires:
  - ANTHROPIC_API_KEY set
  - Bootstrap done: python bootstrap_odcs.py

Usage:
    python agent_odcs.py
    python agent_odcs.py > trace.jsonl
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

DB_FILE  = "capital_odcs.duckdb"
CONTRACT = "contracts/capital_risk_odcs.yaml"
QUESTION = (
    "What is our current CET1 ratio and buffer headroom? "
    "Is this data certified, and who should I contact if I have questions?"
)

# --- Load ODCS contract and extract context ---
with open(CONTRACT) as f:
    contract = yaml.safe_load(f)

info      = contract["info"]
terms     = contract.get("terms", {})
sla       = contract.get("servicelevels", {})
model_def = contract["models"]["capital_position"]
fields    = model_def["fields"]
quality   = contract.get("quality", {})

governance_context = (
    f"Data contract: '{info['title']}' v{info['version']} "
    f"[status: {info['status']}]. "
    f"Owner: {info['contact']['name']} <{info['contact']['email']}>. "
    f"Usage: {terms.get('usage', '').strip()} "
    f"Freshness SLA: {sla.get('freshness', {}).get('description', 'not specified')}. "
    f"Quality checks: {', '.join(quality.get('specification', {}).get('checks for capital_position', [])[:3])} (and more). "
    f"Retention: {sla.get('retention', {}).get('description', 'not specified')}."
)

field_descriptions = "\n".join(
    f"  - {name}: {meta['description'].strip()}"
    for name, meta in fields.items()
)

table_description = model_def["description"].strip()

log.info(
    "agent.start",
    question=QUESTION,
    contract=CONTRACT,
    odcs_version=contract["dataContractSpecification"],
    contract_status=info["status"],
    contract_owner=info["contact"]["email"],
)

client = anthropic.Anthropic()

tools = [
    {
        "name": "query_capital_data",
        "description": (
            f"Query the capital_position table. "
            f"{table_description} "
            f"Governance: {governance_context} "
            f"Columns and meaning:\n{field_descriptions}"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": (
                        "A SQL SELECT query against the capital_position table. "
                        "Use standard SQL. Always include reporting_date in ORDER BY "
                        "when fetching latest data."
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
