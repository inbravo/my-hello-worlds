"""
SLayer Hello World — Jaffle Shop demo via REST API.

Requires SLayer running at http://127.0.0.1:5143:
    uvx --from 'motley-slayer[all]' slayer serve --demo

Usage:
    python agent_slayer_hw.py
    python agent_slayer_hw.py > trace.jsonl
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/amitnoida/
# ─────────────────────────────────────────────────────


import json
import anthropic
import requests
import structlog
from datetime import datetime, timezone

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()

SLAYER_BASE = "http://127.0.0.1:5143"
MODEL_NAME  = "orders"
QUESTION    = "What are the top 3 stores by total order revenue?"

# --- Discover model metadata from the running SLayer server ---
model = requests.get(f"{SLAYER_BASE}/models/{MODEL_NAME}").json()

direct_columns  = [c["name"] for c in model["columns"] if not c.get("hidden") and not c.get("primary_key")]
joined_models   = [j["target_model"] for j in model.get("joins", [])]
time_dimension  = model.get("default_time_dimension")

log.info(
    "agent.start",
    question=QUESTION,
    slayer_model=MODEL_NAME,
    columns=direct_columns,
    joins=joined_models,
)

client = anthropic.Anthropic()

tools = [
    {
        "name": "query_slayer",
        "description": (
            f"Query the SLayer '{MODEL_NAME}' model. "
            f"Direct columns available: {direct_columns}. "
            f"Joined models (use dot notation for dimensions): {joined_models} — "
            f"e.g. 'stores.name', 'customers.name'. "
            f"Default time dimension: '{time_dimension}'. "
            "Measures use formula syntax: '*:count', 'order_total:sum', "
            "'subtotal:avg', 'order_total:max'. "
            "Filters use SQL syntax: \"ordered_at > '2024-06-01'\". "
            "For order, reference the measure column name without colon: "
            "'order_total_sum', 'count'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "measures": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Formula measures, e.g. ['*:count', 'order_total:sum']",
                },
                "dimensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns or joined fields, e.g. ['stores.name', 'ordered_at']",
                },
                "filters": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "SQL-style filters, e.g. [\"ordered_at > '2024-01-01'\"]",
                },
                "order": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Sort order, e.g. [{\"column\": \"order_total_sum\", \"direction\": \"desc\"}]",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum rows to return",
                },
            },
            "required": ["measures"],
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

# --- Tool execution: POST to SLayer REST API ---
tool_call = next(b for b in response.content if b.type == "tool_use")
params = tool_call.input
log.info("slayer.query", **params)

# SLayer REST API expects measures as {"formula": "..."} and dimensions as {"name": "..."}
params = dict(params)
params["measures"]   = [{"formula": m} if isinstance(m, str) else m for m in params.get("measures", [])]
params["dimensions"] = [{"name": d}    if isinstance(d, str) else d for d in params.get("dimensions", [])]

# Remove 'order' if no dimensions — SLayer can't order without dimensions
if not params.get("dimensions"):
    params.pop("order", None)
# Remove empty filters — SLayer rejects an empty filter array
if not params.get("filters"):
    params.pop("filters", None)

query_payload = {"source_model": MODEL_NAME, **params}
slayer_resp = requests.post(f"{SLAYER_BASE}/query", json=query_payload)
if not slayer_resp.ok:
    log.error("slayer.error", status=slayer_resp.status_code, body=slayer_resp.text)
slayer_resp.raise_for_status()
result = slayer_resp.json()

data = result.get("data", result)  # some versions return list directly
log.info("slayer.result", rows=len(data), data=data)

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
                    "content": json.dumps(data),
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
