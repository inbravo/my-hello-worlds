"""
BFSI Capital Adequacy Agent — Anthropic edition.

Queries CET1 / buffer headroom via SLayer REST API.
Logs the SQL SLayer generated — the observable trace.

Requires:
  - SLayer running:  uvx --from 'motley-slayer[all]' slayer serve --demo
  - Setup complete:  python setup_bfsi.py

Usage:
    python agent_slayer_bfsi.py
    python agent_slayer_bfsi.py > trace.jsonl
"""

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
MODEL_NAME  = "capital_position"
DS_NAME     = "capital_bfsi"
QUESTION    = (
    "What is our current CET1 ratio and how does it compare"
    " to the combined buffer requirement?"
)

# --- Discover model metadata ---
model = requests.get(
    f"{SLAYER_BASE}/models/{MODEL_NAME}",
    params={"data_source": DS_NAME}
).json()

direct_columns = [
    c["name"] for c in model["columns"]
    if not c.get("hidden") and not c.get("primary_key")
]
time_dimension = model.get("default_time_dimension")

log.info(
    "agent.start",
    question=QUESTION,
    slayer_model=MODEL_NAME,
    data_source=DS_NAME,
    columns=direct_columns,
)

client = anthropic.Anthropic()

tools = [
    {
        "name": "query_capital_metrics",
        "description": (
            f"Query the '{MODEL_NAME}' capital adequacy model via SLayer. "
            f"Available columns: {direct_columns}. "
            f"Default time dimension: '{time_dimension}'. "
            "Use formula measures — '*:count', 'cet1_ratio_pct:max', "
            "'combined_buffer:max', 'cet1_capital_mm:sum', 'rwa_mm:sum'. "
            "Compute headroom inline: 'cet1_ratio_pct:max - combined_buffer:max'. "
            "Filters use SQL syntax: \"reporting_date = '2026-03-31'\". "
            "For order, use the measure name without colon: 'cet1_ratio_pct_max'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "measures": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Formula measures, e.g. ['cet1_ratio_pct:max', 'combined_buffer:max']",
                },
                "dimensions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Columns to group by, e.g. ['reporting_date', 'entity']",
                },
                "filters": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "SQL-style filters, e.g. [\"reporting_date = '2026-03-31'\"]",
                },
                "order": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Sort, e.g. [{\"column\": \"reporting_date\", \"direction\": \"desc\"}]",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max rows to return",
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
params = dict(tool_call.input)
log.info("slayer.query", **params)

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
data   = result.get("data", [])
sql    = result.get("sql")  # the SQL SLayer compiled — the key demo artefact

log.info("slayer.result", rows=len(data), data=data)
log.info("slayer.sql", sql=sql)  # show what SLayer generated under the hood

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
