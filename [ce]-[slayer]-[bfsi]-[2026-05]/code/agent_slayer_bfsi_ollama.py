"""
BFSI Capital Adequacy Agent — Ollama edition (qwen2.5).

Identical SLayer REST calls to agent_slayer_bfsi.py.
Only the LLM client changes.

Requires:
  - SLayer running:  uvx --from 'motley-slayer[all]' slayer serve --demo
  - Setup complete:  python setup_bfsi.py
  - Ollama running:  ollama serve && ollama pull qwen2.5

Usage:
    python agent_slayer_bfsi_ollama.py
    python agent_slayer_bfsi_ollama.py > trace.jsonl
"""

import json
import requests
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

SLAYER_BASE  = "http://127.0.0.1:5143"
MODEL_NAME   = "capital_position"
DS_NAME      = "capital_bfsi"
OLLAMA_MODEL = "qwen2.5"
QUESTION     = (
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
    ollama_model=OLLAMA_MODEL,
    columns=direct_columns,
)

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

tools = [
    {
        "type": "function",
        "function": {
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
            "parameters": {
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

# --- Tool execution: POST to SLayer REST API ---
tool_call = msg.tool_calls[0]
params = json.loads(tool_call.function.arguments)
log.info("slayer.query", **params)

params["measures"]   = [{"formula": m} if isinstance(m, str) else m for m in params.get("measures", [])]
params["dimensions"] = [{"name": d}    if isinstance(d, str) else d for d in params.get("dimensions", [])]

query_payload = {"source_model": MODEL_NAME, **params}
slayer_resp = requests.post(f"{SLAYER_BASE}/query", json=query_payload)
if not slayer_resp.ok:
    log.error("slayer.error", status=slayer_resp.status_code, body=slayer_resp.text)
slayer_resp.raise_for_status()

result = slayer_resp.json()
data   = result.get("data", [])
sql    = result.get("sql")

log.info("slayer.result", rows=len(data), data=data)
log.info("slayer.sql", sql=sql)

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
            "content": json.dumps(data),
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
