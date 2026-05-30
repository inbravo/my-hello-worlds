# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────

import json
import duckdb
import yaml
import structlog
from datetime import datetime, timezone
from pathlib import Path
from openai import OpenAI

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
MODEL = "qwen2.5"  # any tool-capable Ollama model: llama3.1, qwen2.5, mistral-nemo, command-r

log.info("agent.start", question=QUESTION, contract=contract["name"], model=MODEL)

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

tools = [
    {
        "type": "function",
        "function": {
            "name": "query_capital_position",
            "description": table_descriptions["capital_position"],
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": (
                            "SQL query against the capital_position table. "
                            "Available columns: reporting_date (DATE), entity (VARCHAR), "
                            "cet1_capital_mm (DECIMAL), rwa_mm (DECIMAL), "
                            "cet1_ratio_pct (DECIMAL), combined_buffer (DECIMAL)."
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

# --- Tool execution: DuckDB ---
tool_call = msg.tool_calls[0]
args = json.loads(tool_call.function.arguments)
log.info("tool.args", raw_args=args)  # debug: see actual keys returned

# Fallback: pick first value if 'sql' key is missing
sql = args.get("sql") or args.get("query") or next(iter(args.values()))
log.info("tool.call", tool=tool_call.function.name, sql=sql)

db = duckdb.connect("context_hw.duckdb", read_only=True)
result = db.execute(sql).fetchdf()
log.info("tool.result", rows=len(result), data=result.to_dict(orient="records"))

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
    lineage_source=contract["lineage"]["source_scripts"],
)

print("\n" + "=" * 60)
print(answer)
print("=" * 60)
