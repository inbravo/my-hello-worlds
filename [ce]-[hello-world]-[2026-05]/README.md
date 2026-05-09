# Context Engineering — Hello World

A minimal five-component agentic loop that proves the **question → contract → SQL → answer → trace** chain in four files and zero Docker.

```
bootstrap.py                 — seed DuckDB (run once)
contracts/capital_risk.yaml  — data contract (the context fabric)
agent.py                     — Claude via Anthropic SDK
agent_ollama.py              — same loop via local Ollama
```

---

## How It Works

1. The **data contract** (`capital_risk.yaml`) describes the `capital_position` table in natural language — column names, types, and what each field means.
2. The **agent** reads the contract, injects the table description into a tool definition, and sends it to the LLM.
3. The LLM generates a SQL query. The agent executes it against **DuckDB**.
4. The result goes back to the LLM, which writes a plain-English answer.
5. Every step emits a structured JSON log line — the observable trace.

---

## Prerequisites

- Python 3.10+
- For `agent.py`: an Anthropic API key
- For `agent_ollama.py`: [Ollama](https://ollama.com) running locally

---

## Installation

### Common dependencies (both agents)

```bash
pip install duckdb structlog pyyaml
```

### Anthropic agent

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-...
```

### Ollama agent

```bash
pip install openai
```

Ollama itself:

```bash
# macOS
brew install ollama
ollama serve          # starts the local server on port 11434

# pull a tool-capable model (pick one)
ollama pull llama3.1       # recommended default
ollama pull qwen2.5
ollama pull mistral-nemo
ollama pull command-r
```

---

## Step-by-Step Usage

All commands run from the `code/` directory.

```bash
cd code/
```

### Step 1 — Seed the database (run once)

```bash
python bootstrap.py
```

Creates `context_hw.duckdb` and inserts three quarters of capital position data:

```
Seeded capital_position: 3 rows → context_hw.duckdb
```

---

### Step 2a — Run the Anthropic agent

```bash
python agent.py
```

Streams structured JSON to stdout as the agent works, then prints the answer:

```
============================================================
As of 31 March 2026, the CET1 ratio is 14.83%. The combined
buffer requirement is 9.75%, giving a headroom of 5.08 percentage
points above the minimum threshold.
============================================================
```

---

### Step 2b — Run the Ollama agent

Set the model at the top of `agent_ollama.py` (default: `llama3.1`):

```python
MODEL = "llama3.1"   # change to qwen2.5, mistral-nemo, command-r, etc.
```

```bash
python agent_ollama.py
```

Output format is identical to `agent.py`.

---

### Step 3 — Capture the trace

Pipe to a file to get a grep-able, importable JSONL trace:

```bash
python agent.py > trace.jsonl          # Anthropic
python agent_ollama.py > trace.jsonl   # Ollama
```

Sample trace:

```jsonl
{"timestamp":"2026-05-09T10:01:00Z","event":"agent.start","question":"What is our current CET1 ratio...","contract":"capital_risk","model":"claude-sonnet-4-6"}
{"timestamp":"2026-05-09T10:01:01Z","event":"agent.turn1","stop_reason":"tool_use","latency_ms":843}
{"timestamp":"2026-05-09T10:01:01Z","event":"tool.call","tool":"query_capital_position","sql":"SELECT cet1_ratio_pct, combined_buffer FROM capital_position WHERE reporting_date='2026-03-31'"}
{"timestamp":"2026-05-09T10:01:01Z","event":"tool.result","rows":1,"data":[{"cet1_ratio_pct":14.83,"combined_buffer":9.75}]}
{"timestamp":"2026-05-09T10:01:02Z","event":"agent.answer","latency_ms":612,"lineage_source":["bootstrap.py"]}
```

Query the trace directly:

```bash
grep "tool.call" trace.jsonl | python3 -m json.tool
```

---

## Stack

| Layer | Tool | Notes |
|---|---|---|
| Data | DuckDB | Zero-install, in-process SQL |
| Data Contract | Hand-written YAML | The context fabric — drives the tool description |
| Agent (cloud) | Claude via Anthropic SDK | `agent.py` — model: `claude-sonnet-4-6` |
| Agent (local) | Ollama via OpenAI SDK | `agent_ollama.py` — model: configurable |
| Observability | structlog | JSON to console; pipe to `.jsonl` for persistence |

---

## Switching Models

**Anthropic** — change the `model` argument in `agent.py`:

```python
model="claude-sonnet-4-6"   # or claude-opus-4-7, claude-haiku-4-5-20251001
```

**Ollama** — change the `MODEL` constant in `agent_ollama.py`:

```python
MODEL = "llama3.1"   # or qwen2.5, mistral-nemo, command-r
```

Any Ollama model with tool/function-calling support works. Check [ollama.com/search](https://ollama.com/search) and filter by **Tools**.
