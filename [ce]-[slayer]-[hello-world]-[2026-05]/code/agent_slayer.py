import anthropic
import yaml
import structlog
from datetime import datetime, timezone
from pathlib import Path
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

# --- SLayer: local mode — reads models/ directory, no server required ---
slayer = SlayerClient(storage=YAMLStorage(base_dir="models"))

# Discover available measures and dimensions from the semantic model YAML
# so the tool description is always in sync with the model definition
model_yaml = yaml.safe_load(Path("models/capital_position.yaml").read_text())
available_measures = [m["name"] for m in model_yaml.get("measures", [])]
available_dimensions = [c["name"] for c in model_yaml.get("columns", [])]

QUESTION = (
    "What is our current CET1 ratio and how does it compare"
    " to the combined buffer requirement?"
)

log.info(
    "agent.start",
    question=QUESTION,
    semantic_model=model_yaml["name"],
    available_measures=available_measures,
)

client = anthropic.Anthropic()

tools = [
    {
        "name": "query_capital_metrics",
        "description": (
            f"{model_yaml['description'].strip()} "
            f"Available named measures: {available_measures}. "
            f"Available dimensions: {available_dimensions}. "
            "Request measures by name. SLayer handles the SQL translation."
        ),
        "input_schema": {
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
    }
]

# --- Turn 1: agent decides which metrics to request ---
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

# --- SLayer execution: named metrics → SQL → DuckDB ---
tool_call = next(b for b in response.content if b.type == "tool_use")
params = tool_call.input

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
                    "content": result.to_json(orient="records"),
                }
            ],
        },
    ],
)
answer = final.content[0].text
log.info(
    "agent.answer",
    latency_ms=int((datetime.now(timezone.utc) - t2_start).total_seconds() * 1000),
    semantic_model=model_yaml["name"],
)

print("\n" + "=" * 60)
print(answer)
print("=" * 60)
