import json
import yaml
import structlog
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAI
from slayer.client.slayer_client import SlayerClient
from slayer.core.query import SlayerQuery
from slayer.storage.yaml_storage import YAMLStorage

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()

# --- SLayer: local mode — identical to agent_slayer.py ---
slayer = SlayerClient(storage=YAMLStorage(base_dir="models"))

model_yaml = yaml.safe_load(Path("models/capital_position.yaml").read_text())
available_measures = [m["name"] for m in model_yaml.get("measures", [])]
available_dimensions = [c["name"] for c in model_yaml.get("columns", [])]

QUESTION = (
    "What is our current CET1 ratio and how does it compare"
    " to the combined buffer requirement?"
)
MODEL = "qwen2.5"  # any tool-capable Ollama model: llama3.1, mistral-nemo, command-r

log.info(
    "agent.start",
    question=QUESTION,
    semantic_model=model_yaml["name"],
    available_measures=available_measures,
    ollama_model=MODEL,
)

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

tools = [
    {
        "type": "function",
        "function": {
            "name": "query_capital_metrics",
            "description": (
                f"{model_yaml['description'].strip()} "
                f"Available named measures: {available_measures}. "
                f"Available dimensions: {available_dimensions}. "
                "Request measures by name. SLayer handles the SQL translation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "measures": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Named measures to retrieve, e.g. "
                            "['latest_cet1_ratio', 'buffer_headroom']"
                        ),
                    },
                    "dimensions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Columns to group by, e.g. ['reporting_date', 'entity']"
                        ),
                    },
                    "filters": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Filter conditions, e.g. [\"reporting_date == '2026-03-31'\"]"
                        ),
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum rows to return (default: 10)",
                    },
                },
                "required": ["measures"],
            },
        },
    }
]

# --- Turn 1: agent decides which metrics to request ---
t1_start = datetime.now(timezone.utc)
response = client.chat.completions.create(
    model=MODEL,
    tools=tools,
    messages=[{"role": "user", "content": QUESTION}],
)
msg = response.choices[0].message
log.info(
    "agent.turn1",
    stop_reason=response.choices[0].finish_reason,
    latency_ms=int((datetime.now(timezone.utc) - t1_start).total_seconds() * 1000),
)

# --- SLayer execution: named metrics → SQL → DuckDB ---
tool_call = msg.tool_calls[0]
params = json.loads(tool_call.function.arguments)

log.info(
    "slayer.query",
    measures=params.get("measures"),
    dimensions=params.get("dimensions"),
    filters=params.get("filters"),
)

query = SlayerQuery(
    source_model="capital_position",
    measures=params.get("measures", []),
    dimensions=params.get("dimensions", []),
    filters=params.get("filters", []),
    limit=params.get("limit", 10),
)
result = slayer.query_df(query)
log.info("slayer.result", rows=len(result), data=result.to_dict(orient="records"))

# --- Turn 2: agent synthesises the answer ---
t2_start = datetime.now(timezone.utc)
final = client.chat.completions.create(
    model=MODEL,
    tools=tools,
    messages=[
        {"role": "user", "content": QUESTION},
        msg,
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result.to_json(orient="records"),
        },
    ],
)
answer = final.choices[0].message.content
log.info(
    "agent.answer",
    latency_ms=int((datetime.now(timezone.utc) - t2_start).total_seconds() * 1000),
    semantic_model=model_yaml["name"],
)

print("\n" + "=" * 60)
print(answer)
print("=" * 60)
