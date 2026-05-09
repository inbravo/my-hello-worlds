# Context Engineering — SLayer Hello World

A five-component agentic loop using a **semantic layer** instead of raw SQL generation. The agent calls named business metrics. SLayer translates them to SQL. The LLM never sees a column name or writes a query.

```
bootstrap.py                          — seed DuckDB (run once)
models/datasources/capital_db.yaml    — DuckDB connection config
models/capital_position.yaml          — SLayer semantic model with named measures
agent_slayer.py                       — Claude agent querying metrics, not SQL
```

---

## Quick Start

```bash
# 1. Clone and move into the code folder
git clone https://github.com/inbravo/my-hello-worlds
cd my-hello-worlds/[ce]-[slayer]-[hello-world]-[2026-05]/code

# 2. Install dependencies
pip install anthropic duckdb structlog pyyaml numpy pandas "motley-slayer[duckdb]"

# 3. Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# 4. Seed the database (run once)
python bootstrap.py

# 5. Run the agent
python agent_slayer.py

# 6. Capture the full trace to a file
python agent_slayer.py > trace.jsonl
```

---

## Why This Exists

The [text-to-SQL hello world](../[ce]-[hello-world]-[2026-05]/README.md) in this repo proves the agent can generate correct SQL from a data contract. This demo takes the next step: the agent doesn't generate SQL at all. It asks for metrics by name. SLayer owns the translation.

That shift matters in production. When a column is renamed or a calculation changes, you update the semantic model in one place. Every agent, dashboard, and report that queries through SLayer gets the fix automatically — with no prompt changes, no re-testing SQL generation, no regression risk.

---

## Text-to-SQL vs Semantic Layer

| | Text-to-SQL (`agent.py`) | SLayer (`agent_slayer.py`) |
|---|---|---|
| Agent sends | Raw SQL string | Named metric + optional filter |
| LLM knows about | Column names, table schema | Metric names, dimension names |
| SQL lives | In the LLM's output | In the semantic model YAML |
| Schema change impact | Prompt may break | Update model YAML only |
| Auditability | Log the SQL | Log the metric name + measure formula |
| Governance | In the data contract | In the semantic model |

---

## The Banking Use Case

Same scenario as the text-to-SQL demo. A bank's capital reporting team needs instant answers to Basel III/IV capital adequacy questions:

- **CET1 ratio** — Common Equity Tier 1 capital ÷ Risk-Weighted Assets × 100
- **Combined buffer requirement** — Capital Conservation Buffer (2.5%) + G-SII buffer + Countercyclical Capital Buffer
- **Buffer headroom** — how far above the regulatory floor the bank sits

A CET1 of **14.83%** against a combined buffer of **9.75%** gives **5.08 percentage points of headroom**. This number is reviewed daily by treasury, risk, and regulators. Getting it wrong — or getting it from a broken SQL query — has direct regulatory consequences.

With SLayer, the metric `buffer_headroom` is defined once in the semantic model. The formula `cet1_ratio_pct:max - combined_buffer:max` is the single source of truth. Any agent that queries it gets the same correct answer, every time.

---

## The Semantic Model

`models/capital_position.yaml` defines the table structure and the business metrics on top of it.

### Columns — the raw schema

```yaml
columns:
  - name: cet1_ratio_pct
    sql:  cet1_ratio_pct
    type: number
    description: CET1 ratio as a percentage (cet1_capital_mm / rwa_mm * 100)

  - name: combined_buffer
    sql:  combined_buffer
    type: number
    description: Combined buffer requirement as a percentage
```

### Measures — the business metrics

```yaml
measures:
  - name: latest_cet1_ratio
    formula: "cet1_ratio_pct:max"
    label: Latest CET1 Ratio (%)

  - name: latest_combined_buffer
    formula: "combined_buffer:max"
    label: Latest Combined Buffer Requirement (%)

  - name: buffer_headroom
    formula: "cet1_ratio_pct:max - combined_buffer:max"
    label: Buffer Headroom (percentage points above regulatory minimum)

  - name: total_cet1_capital
    formula: "cet1_capital_mm:sum"
    label: Total CET1 Capital (millions GBP)

  - name: total_rwa
    formula: "rwa_mm:sum"
    label: Total Risk-Weighted Assets (millions GBP)
```

The measure formulas use SLayer's aggregation syntax: `column:aggregation`. Compound formulas like `cet1_ratio_pct:max - combined_buffer:max` are evaluated by SLayer at query time and compiled into correct SQL.

### Datasource config

`models/datasources/capital_db.yaml` points SLayer at the DuckDB file:

```yaml
name: capital_db
type: duckdb
database: context_hw.duckdb
```

No host, no port, no credentials. DuckDB is file-based.

---

## How the Agent Loop Works

```
User question
     │
     ▼
agent_slayer.py reads capital_position.yaml
→ discovers available measures and dimensions
→ builds tool description from the model (always in sync)
     │
     ▼
Turn 1 — LLM decides which metrics to request
→ returns tool_call: { measures: ["latest_cet1_ratio", "buffer_headroom"],
                        dimensions: ["reporting_date"] }
     │
     ▼
SLayer translates measures → compiles SQL → queries DuckDB
→ returns result set as a DataFrame
     │
     ▼
Turn 2 — LLM reads the metric values → plain-English answer
     │
     ▼
structlog emits a JSON line at every step
```

The key step is that the agent's tool description is **generated from the model YAML at runtime** — not hardcoded. Add a measure to `capital_position.yaml` and it immediately appears in the tool description on the next run.

---

## Prerequisites

- Python 3.10+
- An Anthropic API key — [console.anthropic.com](https://console.anthropic.com)

---

## Installation

```bash
pip install anthropic duckdb structlog pyyaml numpy pandas "motley-slayer[duckdb]"
export ANTHROPIC_API_KEY=sk-ant-...
```

The `[duckdb]` extra installs the DuckDB driver for SLayer alongside the core package.

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

Creates `context_hw.duckdb` with three quarters of capital position data:

```
Seeded capital_position: 3 rows → context_hw.duckdb
```

| reporting_date | entity | cet1_ratio_pct | combined_buffer |
|---|---|---|---|
| 2025-09-30 | BANK_HOLDCO | 14.39 | 9.75 |
| 2025-12-31 | BANK_HOLDCO | 14.66 | 9.75 |
| 2026-03-31 | BANK_HOLDCO | 14.83 | 9.75 |

---

### Step 2 — Run the agent

```bash
python agent_slayer.py
```

The agent reads the semantic model, discovers available measures, and builds its tool definition dynamically. You'll see structured JSON logs as it works through both turns, then the answer:

```
============================================================
As of 31 March 2026, the CET1 ratio stands at 14.83%. The combined
buffer requirement is 9.75%, giving a buffer headroom of 5.08
percentage points. The bank is comfortably above its regulatory
minimum.
============================================================
```

---

### Step 3 — Capture the trace

```bash
python agent_slayer.py > trace.jsonl
```

The trace shows the full chain — question, metric names requested, SLayer query, result, answer:

```jsonl
{"event":"agent.start","question":"What is our current CET1 ratio...","semantic_model":"capital_position","available_measures":["latest_cet1_ratio","latest_combined_buffer","buffer_headroom","total_cet1_capital","total_rwa"],"timestamp":"2026-05-09T10:01:00Z"}
{"event":"agent.turn1","stop_reason":"tool_use","latency_ms":756,"timestamp":"2026-05-09T10:01:01Z"}
{"event":"slayer.query","measures":["latest_cet1_ratio","buffer_headroom"],"dimensions":["reporting_date"],"filters":[],"timestamp":"2026-05-09T10:01:01Z"}
{"event":"slayer.result","rows":3,"data":[{"reporting_date":"2025-09-30","latest_cet1_ratio":14.39,"buffer_headroom":4.64},{"reporting_date":"2025-12-31","latest_cet1_ratio":14.66,"buffer_headroom":4.91},{"reporting_date":"2026-03-31","latest_cet1_ratio":14.83,"buffer_headroom":5.08}],"timestamp":"2026-05-09T10:01:01Z"}
{"event":"agent.answer","latency_ms":589,"semantic_model":"capital_position","timestamp":"2026-05-09T10:01:02Z"}
```

Notice what's **not** in the trace: no SQL. The agent requested `buffer_headroom` by name. SLayer compiled the SQL internally. The trace records intent, not implementation.

Query the trace:

```bash
# What metrics did the agent request?
grep "slayer.query" trace.jsonl | python3 -m json.tool

# What values came back?
grep "slayer.result" trace.jsonl | python3 -m json.tool
```

---

## Adding a New Metric

To expose a new capital metric to the agent, add a measure to `models/capital_position.yaml`:

```yaml
measures:
  # ... existing measures ...
  - name: cet1_trend_qoq
    formula: "cet1_ratio_pct:max - lag(cet1_ratio_pct:max)"
    label: CET1 Ratio Change Quarter-on-Quarter (pp)
```

Run the agent again. The new measure appears automatically in the tool description — no changes to `agent_slayer.py` required.

---

## Stack

| Layer | Component | Notes |
|---|---|---|
| Data | DuckDB (`context_hw.duckdb`) | In-process SQL, file-based |
| Datasource config | `models/datasources/capital_db.yaml` | DuckDB connection |
| Semantic model | `models/capital_position.yaml` | Named measures + column definitions |
| Semantic layer | motley-slayer Python API (local mode) | In-process, no server required |
| Agent | Claude via Anthropic SDK | `claude-sonnet-4-6` |
| Observability | structlog | JSON to console; pipe to `.jsonl` |

---

## SLayer Modes

This demo uses SLayer's **Python API in local mode** — the simplest setup. Two other modes are available if you need them:

**MCP stdio (for Claude Code / Cursor):**
```bash
# Register SLayer as an MCP server in Claude Code
claude mcp add slayer -- uvx --from motley-slayer slayer mcp --models-dir ./models
```

Claude Code will then have direct access to SLayer's query tools in every session — no agent loop needed.

**HTTP server (for shared/multi-agent access):**
```bash
uvx --from "motley-slayer[duckdb]" slayer serve --models-dir ./models
# Server runs at http://localhost:5143
```

Switch the client in `agent_slayer.py`:
```python
# Local mode (current — default)
slayer = SlayerClient(storage=YAMLStorage(base_dir="models"))

# Remote mode (HTTP server)
slayer = SlayerClient(url="http://localhost:5143")
```

The agent code is identical. Only the client initialisation changes.

---

## Switching the LLM Model

Edit the `model` argument in `agent_slayer.py`:

```python
model="claude-sonnet-4-6"          # balanced — default
model="claude-opus-4-7"            # more capable, higher cost
model="claude-haiku-4-5-20251001"  # fastest, lowest cost
```
