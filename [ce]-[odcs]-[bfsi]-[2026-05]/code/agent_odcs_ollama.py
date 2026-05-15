"""
BFSI Capital Adequacy Agent — ODCS edition, Ollama (qwen2.5).

Upgrades Demo 1 (hand-written YAML contract) to a formal Bitol/ACRYL
Open Data Contract Standard (ODCS 0.9.3) contract.

The agent extracts richer context from the ODCS contract:
  - Business description (what the data means)
  - Governance metadata (owner, status, usage terms)
  - Quality rules (is the data certified?)
  - SLA / freshness (how current is the data?)

This richer context enables the agent to answer both data questions
AND governance questions from the same contract.

Requires:
  - Ollama running:  ollama serve && ollama pull qwen2.5
  - Bootstrap done:  python bootstrap_odcs.py

Usage:
    python agent_odcs_ollama.py
    python agent_odcs_ollama.py > trace.jsonl
"""

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

DB_FILE      = "capital_odcs.duckdb"
CONTRACT     = "contracts/capital_risk_odcs.yaml"
OLLAMA_MODEL = "qwen2.5"
QUESTION     = (
    "What is our current CET1 ratio and buffer headroom? "
    "Is this data certified, and who should I contact if I have questions?"
)

# --- Load ODCS contract and extract context ---
with open(CONTRACT) as f:
    contract = yaml.safe_load(f)

info        = contract["info"]
terms       = contract.get("terms", {})
sla         = contract.get("servicelevels", {})
model_def   = contract["models"]["capital_position"]
fields      = model_def["fields"]
quality     = contract.get("quality", {})

# Build a rich governance summary from the ODCS contract
governance_context = (
    f"Data contract: '{info['title']}' v{info['version']} "
    f"[status: {info['status']}]. "
    f"Owner: {info['contact']['name']} <{info['contact']['email']}>. "
    f"Usage: {terms.get('usage', '').strip()} "
    f"Freshness SLA: {sla.get('freshness', {}).get('description', 'not specified')}. "
    f"Quality checks: {', '.join(quality.get('specification', {}).get('checks for capital_position', [])[:3])} (and more). "
    f"Retention: {sla.get('retention', {}).get('description', 'not specified')}."
)

# Build field descriptions from ODCS fields
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
    ollama_model=OLLAMA_MODEL,
)

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

tools = [
    {
        "type": "function",
        "function": {
            "name": "query_capital_data",
            "description": (
                f"Query the capital_position table. "
                f"{table_description} "
                f"Governance: {governance_context} "
                f"Columns and meaning:\n{field_descriptions}"
            ),
            "parameters": {
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
    ],
)
answer = final.choices[0].message.content
log.info(
    "agent.answer",
    latency_ms=int((datetime.now(timezone.utc) - t2_start).total_seconds() * 1000),
)

print("\n" + "=" * 60)
print(answer)
print("=" * 60)
