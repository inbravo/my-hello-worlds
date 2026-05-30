# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────

import anthropic
import duckdb
import yaml
import structlog
from datetime import datetime, timezone
from pathlib import Path

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)
log = structlog.get_logger()

contract = yaml.safe_load(Path("contracts/capital_risk.yaml").read_text())
table_descriptions = {t["name"]: t["description"] for t in contract["tables"]}

QUESTION = (
    "What is our current CET1 ratio and how does it compare"
    " to the combined buffer requirement?"
)

log.info("agent.start", question=QUESTION, contract=contract["name"])

client = anthropic.Anthropic()

tools = [
    {
        "name": "query_capital_position",
        "description": table_descriptions["capital_position"],
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "SQL query against the capital_position table",
                }
            },
            "required": ["sql"],
        },
    }
]

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

tool_call = next(b for b in response.content if b.type == "tool_use")
sql = tool_call.input["sql"]
log.info("tool.call", tool=tool_call.name, sql=sql)

db = duckdb.connect("context_hw.duckdb", read_only=True)
result = db.execute(sql).fetchdf()
log.info("tool.result", rows=len(result), data=result.to_dict(orient="records"))

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
    lineage_source=contract["lineage"]["source_scripts"],
)

print("\n" + "=" * 60)
print(answer)
print("=" * 60)
