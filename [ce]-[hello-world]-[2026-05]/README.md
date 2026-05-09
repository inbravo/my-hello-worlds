# Context Engineering — Hello World

A five-component agentic loop built around a real banking use case: an AI agent reads a structured data contract, writes its own SQL, queries a live database, and returns a plain-English answer — with a full audit trace at every step.

```
bootstrap.py                 — seed DuckDB (run once)
contracts/capital_risk.yaml  — data contract (the context fabric)
agent.py                     — Option A: Claude via Anthropic SDK
agent_ollama.py              — Option B: same loop via local Ollama
```

---

## Quick Start

**Option A — Anthropic (cloud):**

```bash
# 1. Clone and move into the code folder
git clone https://github.com/inbravo/my-hello-worlds
cd my-hello-worlds/[ce]-[hello-world]-[2026-05]/code

# 2. Install dependencies
pip install anthropic duckdb structlog pyyaml numpy pandas

# 3. Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# 4. Seed the database (run once)
python bootstrap.py

# 5. Run the agent
python agent.py

# 6. Capture the full trace to a file
python agent.py > trace.jsonl
```

**Option B — Ollama (local, no API key needed):**

```bash
# 1. Install and start Ollama
brew install ollama && ollama serve

# 2. Pull a tool-capable model
ollama pull qwen2.5

# 3. Install dependencies
pip install openai duckdb structlog pyyaml numpy pandas

# 4. Seed the database (run once)
python bootstrap.py

# 5. Run the agent
python agent_ollama.py

# 6. Capture the full trace to a file
python agent_ollama.py > trace.jsonl
```

---

## The Banking Use Case

Under Basel III/IV, every bank must hold Common Equity Tier 1 (CET1) capital above a regulatory floor made up of several stacked buffers:

- **CET1 ratio** = CET1 capital ÷ Risk-Weighted Assets × 100
- **Combined buffer requirement** = Capital Conservation Buffer (2.5%) + G-SII buffer + Countercyclical Capital Buffer

A bank with a CET1 ratio of **14.83%** and a combined buffer of **9.75%** has **5.08 percentage points of headroom**. Breaching this threshold triggers regulatory intervention — dividend restrictions, executive pay caps, and mandatory capital rebuild plans.

Capital reporting teams field these questions daily: from risk managers, CFOs, group treasury, and regulators. The data exists. The friction is in writing and maintaining ad-hoc SQL against tables that change with every regulatory update cycle.

This demo replaces that friction with a **data contract and an AI agent**. The analyst asks in plain English. The agent figures out the SQL, runs it, and explains what the numbers mean.

---

## The Key Insight: The Data Contract

`contracts/capital_risk.yaml` is a structured description of what the data *means* — written in language the LLM can read and act on directly.

```yaml
- name: capital_position
  description: >
    Daily capital adequacy snapshot per legal entity and reporting date.
    Contains CET1 capital ratios, risk-weighted assets (RWA), and the
    combined regulatory buffer requirement (CCB + G-SII + countercyclical).
    Query this table to assess capital adequacy, buffer headroom, or CET1
    ratio trends across quarters.
  columns:
    - name: cet1_ratio_pct
      description: CET1 ratio as percentage (cet1_capital_mm / rwa_mm * 100)
    - name: combined_buffer
      description: Combined buffer requirement as percentage (CCB + G-SII + countercyclical)
```

The agent reads this file at startup and injects the table description directly into the tool definition sent to the LLM. The model reads it, understands the schema, and generates correct SQL — without hardcoded prompts, without a vector store, without a metadata catalogue.

**The data contract is the context.** That's context engineering.

---

## How It Works

```
User question
     │
     ▼
Agent reads data contract → builds tool definition from YAML
     │
     ▼
Turn 1 — LLM decides what to query → returns tool_call with SQL
     │
     ▼
DuckDB executes the SQL → returns a result set
     │
     ▼
Turn 2 — LLM reads the result → returns a plain-English answer
     │
     ▼
structlog emits a JSON line at every step → full observable trace
```

The two-turn structure is deliberate. Turn 1 is planning (what data do I need?). Turn 2 is synthesis (what does this data mean?). Separating them gives you a clean record of what the agent decided vs. what it concluded.

---

## Two Options: Anthropic or Ollama

Both agents run the same loop. The only difference is where the LLM runs.

| | **Option A — Anthropic (cloud)** | **Option B — Ollama (local)** |
|---|---|---|
| Script | `agent.py` | `agent_ollama.py` |
| Model | `claude-sonnet-4-6` | `qwen2.5` (default) |
| Runs on | Anthropic's API | Your machine |
| Requires | API key + internet | Ollama installed + model pulled |
| Cost | Per-token billing | Free |
| Speed | ~1–2 s per turn | Depends on hardware |
| Privacy | Data leaves your machine | Fully local |

Pick Option A to get started fast with a state-of-the-art model. Pick Option B if you want everything on-premise, free of charge, or are working with sensitive data.

---

## Prerequisites

- Python 3.10+
- **Option A:** An Anthropic API key — get one at [console.anthropic.com](https://console.anthropic.com)
- **Option B:** [Ollama](https://ollama.com) installed and running on your machine

---

## Installation

### Common dependencies (required for both options)

```bash
pip install duckdb structlog pyyaml numpy pandas
```

### Option A — Anthropic

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

### Option B — Ollama

**1. Install and start Ollama:**

```bash
# macOS
brew install ollama
ollama serve          # starts the local server at http://localhost:11434
```

For Linux or Windows, see [ollama.com/download](https://ollama.com/download).

**2. Install the Python client:**

```bash
pip install openai    # Ollama exposes an OpenAI-compatible endpoint
```

**3. Pull a tool-capable model:**

```bash
ollama pull qwen2.5        # recommended — tested and verified
ollama pull llama3.1       # solid alternative
ollama pull mistral-nemo   # lightweight option
ollama pull command-r      # strong on retrieval-style tasks
```

> Only models with tool/function-calling support work here. On [ollama.com/search](https://ollama.com/search), filter by **Tools** to see the full list.

---

## Step-by-Step Usage

All commands run from the `code/` directory:

```bash
cd code/
```

---

### Step 1 — Seed the database (run once)

```bash
python bootstrap.py
```

Creates `context_hw.duckdb` and populates `capital_position` with three quarters of capital data:

```
Seeded capital_position: 3 rows → context_hw.duckdb
```

| reporting_date | entity | cet1_ratio_pct | combined_buffer |
|---|---|---|---|
| 2025-09-30 | BANK_HOLDCO | 14.39 | 9.75 |
| 2025-12-31 | BANK_HOLDCO | 14.66 | 9.75 |
| 2026-03-31 | BANK_HOLDCO | 14.83 | 9.75 |

The agent will query the most recent quarter. Having three rows lets you ask trend questions too.

---

### Step 2A — Run with Anthropic (cloud)

```bash
python agent.py
```

Structured JSON logs stream to stdout as the agent works through its two turns. The answer prints at the end:

```
============================================================
As of 31 March 2026, the CET1 ratio is 14.83%. The combined
buffer requirement is 9.75%, giving a headroom of 5.08 percentage
points above the regulatory minimum.
============================================================
```

---

### Step 2B — Run with Ollama (local)

Confirm the model at the top of `agent_ollama.py` matches what you pulled:

```python
MODEL = "qwen2.5"   # change to llama3.1, mistral-nemo, command-r, etc.
```

Then run:

```bash
python agent_ollama.py
```

Output format is identical to Option A.

---

### Step 3 — Capture the trace

Every log line is valid JSON. Pipe to a file for a persistent, grep-able audit trail:

```bash
python agent.py > trace.jsonl          # Option A
python agent_ollama.py > trace.jsonl   # Option B
```

The trace captures the full chain — question, SQL generated, data returned, answer, latency, and data lineage back to the source script:

```jsonl
{"event":"agent.start","question":"What is our current CET1 ratio...","contract":"capital_risk","model":"claude-sonnet-4-6","timestamp":"2026-05-09T10:01:00Z"}
{"event":"agent.turn1","stop_reason":"tool_use","latency_ms":843,"timestamp":"2026-05-09T10:01:01Z"}
{"event":"tool.call","tool":"query_capital_position","sql":"SELECT cet1_ratio_pct, combined_buffer FROM capital_position WHERE reporting_date='2026-03-31'","timestamp":"2026-05-09T10:01:01Z"}
{"event":"tool.result","rows":1,"data":[{"cet1_ratio_pct":14.83,"combined_buffer":9.75}],"timestamp":"2026-05-09T10:01:01Z"}
{"event":"agent.answer","latency_ms":612,"lineage_source":["bootstrap.py"],"timestamp":"2026-05-09T10:01:02Z"}
```

Query the trace directly from the command line:

```bash
# See the SQL the agent generated
grep "tool.call" trace.jsonl | python3 -m json.tool

# Check latency on both turns
grep "latency_ms" trace.jsonl

# Confirm data lineage
grep "lineage_source" trace.jsonl
```

---

## Stack

| Layer | Component | Notes |
|---|---|---|
| Data | DuckDB (`context_hw.duckdb`) | In-process SQL — no server, no config |
| Data Contract | `contracts/capital_risk.yaml` | Natural-language schema — drives the tool description |
| Agent (cloud) | Claude via Anthropic SDK | `agent.py` — model: `claude-sonnet-4-6` |
| Agent (local) | Ollama via OpenAI-compatible API | `agent_ollama.py` — model: `qwen2.5` default |
| Observability | structlog | JSON to console; pipe to `.jsonl` for persistence |

---

## Switching Models

**Option A — Anthropic:** edit the `model` argument in `agent.py`:

```python
model="claude-sonnet-4-6"          # balanced — default
model="claude-opus-4-7"            # more capable, higher cost
model="claude-haiku-4-5-20251001"  # fastest, lowest cost
```

**Option B — Ollama:** edit the `MODEL` constant in `agent_ollama.py`:

```python
MODEL = "qwen2.5"        # recommended — tested
MODEL = "llama3.1"       # reliable alternative
MODEL = "mistral-nemo"   # lightweight, fast on CPU
MODEL = "command-r"      # strong on retrieval-style tasks
```

---

## Sample Output (qwen2.5 via Ollama)

```bash
(.venv) inbravo@IMUL-ML0515 code % python agent_ollama.py
{"question": "What is our current CET1 ratio and how does it compare to the combined buffer requirement?", "contract": "capital_risk", "model": "qwen2.5", "event": "agent.start", "timestamp": "2026-05-09T09:36:14.911277Z"}
{"stop_reason": "tool_calls", "latency_ms": 16753, "event": "agent.turn1", "timestamp": "2026-05-09T09:36:32.149875Z"}
{"raw_args": {"sql": "SELECT cet1_ratio_pct, combined_buffer FROM capital_position ORDER BY reporting_date DESC LIMIT 1;"}, "event": "tool.args", "timestamp": "2026-05-09T09:36:32.150196Z"}
{"tool": "query_capital_position", "sql": "SELECT cet1_ratio_pct, combined_buffer FROM capital_position ORDER BY reporting_date DESC LIMIT 1;", "event": "tool.call", "timestamp": "2026-05-09T09:36:32.150249Z"}
{"rows": 1, "data": [{"cet1_ratio_pct": 14.83, "combined_buffer": 9.75}], "event": "tool.result", "timestamp": "2026-05-09T09:36:41.054748Z"}
{"latency_ms": 5539, "lineage_source": ["bootstrap.py"], "event": "agent.answer", "timestamp": "2026-05-09T09:36:46.594115Z"}

============================================================
Based on the most recent data, our current CET1 ratio is 14.83%, while the combined buffer
requirement stands at 9.75%. Buffer headroom: 5.08 percentage points.
============================================================
```
