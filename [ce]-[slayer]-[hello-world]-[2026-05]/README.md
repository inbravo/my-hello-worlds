# Context Engineering — SLayer Hello World

An AI agent that queries a live SLayer semantic layer via REST. No YAML authoring, no embedded engine. The agent discovers the data model at startup, builds its own tool description, and answers a business question in two turns.

```
agent_slayer_hw.py         — Option A: Claude via Anthropic SDK
agent_slayer_ollama_hw.py  — Option B: same loop via local Ollama (qwen2.5)
```

---

## Two Options: Anthropic or Ollama

The SLayer REST calls are identical in both agents. Only the LLM client changes.

| | **Option A — Anthropic (cloud)** | **Option B — Ollama (local)** |
|---|---|---|
| Script | `agent_slayer_hw.py` | `agent_slayer_ollama_hw.py` |
| LLM | `claude-sonnet-4-6` | `qwen2.5` (default) |
| Requires | API key + internet | Ollama running locally |
| Cost | Per-token | Free |
| SLayer calls | Identical | Identical |

---

## Quick Start

**Step 0 — Install SLayer with DuckDB support:**

```bash
pip install 'motley-slayer[all]'
```

> `[all]` includes the DuckDB adapter.  
> Alternatively, use `uvx` (part of [`uv`](https://docs.astral.sh/uv/)) which installs and runs SLayer in one command — no separate install needed:
> ```bash
> pip install uv
> ```

**Step 1 — Start SLayer (required for both options):**

```bash
# Option A — if installed via pip:
slayer serve --demo

# Option B — via uvx (installs on first run):
uvx --from 'motley-slayer[all]' slayer serve --demo
```

SLayer starts at `http://127.0.0.1:5143` and preloads the Jaffle Shop dataset — orders, customers, stores, products, and more.

**Step 2A — Run with Anthropic (new terminal):**

```bash
cd code/
pip install anthropic requests structlog
export ANTHROPIC_API_KEY=sk-ant-...
python agent_slayer_hw.py
```

**Step 2B — Run with Ollama (new terminal):**

```bash
# Start Ollama and pull the model (once)
ollama serve
ollama pull qwen2.5

cd code/
pip install openai requests structlog
python agent_slayer_ollama_hw.py
```

**Step 3 — Capture the trace:**

```bash
python agent_slayer_hw.py > trace.jsonl          # Option A
python agent_slayer_ollama_hw.py > trace.jsonl   # Option B
```

---

## What It Does

The agent asks: **"What are the top 3 stores by total order revenue?"**

At startup it calls `GET /models/orders` to discover the model — columns, joins, time dimension. It builds its tool description from that response. If the model changes on the SLayer side, the agent picks it up automatically on the next run.

The two-turn loop:

```
Turn 1 — agent decides what to query
→ tool_call: {
      measures:   ["order_total:sum"],
      dimensions: ["stores.name"],
      order:      [{"column": "order_total_sum", "direction": "desc"}],
      limit:      3
  }

SLayer executes → POST /query → returns ranked store revenue

Turn 2 — agent reads the result → plain-English answer
```

---

## The Jaffle Shop Dataset

Seven models ship with the SLayer demo:

| Model | What it contains |
|---|---|
| `orders` | Order headers — totals, dates, store and customer FK |
| `customers` | Customer profiles |
| `stores` | Store locations |
| `products` | Product catalogue |
| `items` | Order line items |
| `supplies` | Supply records |
| `tweets` | Social mentions |

The `orders` model joins to `customers` and `stores`. Use dot notation in dimensions to traverse joins: `stores.name`, `customers.name`.

---

## Measure Formula Syntax

SLayer uses formula strings — not pre-named measures.

| Formula | Meaning |
|---|---|
| `*:count` | Row count |
| `order_total:sum` | Sum of order_total |
| `order_total:avg` | Average order total |
| `order_total:max` | Maximum order total |
| `subtotal:sum` | Sum of subtotal |
| `order_total:sum / *:count` | Revenue per order (inline formula) |
| `cumsum(*:count)` | Running order count over time |
| `change(*:count)` | Month-over-month change |

---

## Filter and Order Syntax

**Filters** use SQL equality syntax:

```python
filters=["ordered_at > '2024-06-01'"]
filters=["store_id = 'SFO'", "order_total > 50"]
```

**Order** references the measure column name (colon replaced with underscore):

```python
order=[{"column": "order_total_sum", "direction": "desc"}]
order=[{"column": "count", "direction": "asc"}]
```

---

## Trying Different Questions

Change the `QUESTION` constant in `agent_slayer_hw.py` and re-run:

```python
QUESTION = "How many orders were placed each month in 2024?"
QUESTION = "Which customers have spent the most in total?"
QUESTION = "What is the average order value by store?"
QUESTION = "Show me the month-over-month change in order count."
```

To query a different model, change `MODEL_NAME`:

```python
MODEL_NAME = "customers"
MODEL_NAME = "stores"
```

The agent re-discovers the model metadata automatically — no other changes needed.

---

## Switching the Ollama Model

Edit `OLLAMA_MODEL` at the top of `agent_slayer_ollama_hw.py`:

```python
OLLAMA_MODEL = "qwen2.5"       # recommended — tested
OLLAMA_MODEL = "llama3.1"      # solid alternative
OLLAMA_MODEL = "mistral-nemo"  # lightweight
OLLAMA_MODEL = "command-r"     # strong on retrieval tasks
```

Any Ollama model with tool/function-calling support works. Check [ollama.com/search](https://ollama.com/search) and filter by **Tools**.

---

## Stack

| Layer | Component |
|---|---|
| Data | Jaffle Shop (SLayer built-in demo) |
| Semantic Layer | SLayer HTTP server — `http://127.0.0.1:5143` |
| Query | `POST /query` with formula measures + dimensions |
| Agent (cloud) | Claude (`claude-sonnet-4-6`) via Anthropic SDK |
| Agent (local) | Ollama (`qwen2.5`) via OpenAI-compatible endpoint |
| Observability | structlog — JSON to console, pipe to `.jsonl` |

---

## Sample Trace

```jsonl
{"event":"agent.start","question":"What are the top 3 stores by total order revenue?","slayer_model":"orders","columns":["customer_id","ordered_at","store_id","subtotal","tax_paid","order_total"],"joins":["customers","stores"],"timestamp":"2026-05-09T10:01:00Z"}
{"event":"agent.turn1","stop_reason":"tool_use","latency_ms":712,"timestamp":"2026-05-09T10:01:01Z"}
{"event":"slayer.query","measures":["order_total:sum"],"dimensions":["stores.name"],"order":[{"column":"order_total_sum","direction":"desc"}],"limit":3,"timestamp":"2026-05-09T10:01:01Z"}
{"event":"slayer.result","rows":3,"data":[{"orders.stores.name":"Chicago","orders.order_total_sum":4821.50},{"orders.stores.name":"Brooklyn","orders.order_total_sum":4105.75},{"orders.stores.name":"Austin","orders.order_total_sum":3940.00}],"timestamp":"2026-05-09T10:01:01Z"}
{"event":"agent.answer","latency_ms":534,"timestamp":"2026-05-09T10:01:02Z"}
```

---

## CE Series

| Example | Semantic component | What the agent understands |
|---------|-------------------|-----------------------------|
| [Example 1](../[ce]-[hello-world]-[2026-05]/README.md) | Hand-written YAML contract | Schema — column names and types |
| **[Example 2](../[ce]-[slayer]-[hello-world]-[2026-05]/README.md) (this)** | Semantic model — SLayer REST (generic) | Measures and dimensions |
| [Example 3](../[ce]-[slayer]-[bfsi]-[2026-05]/README.md) | Semantic model — SLayer REST (BFSI) | Business metric definitions |
| [Example 4](../[ce]-[odcs]-[bfsi]-[2026-05]/README.md) | Formal ODCS contract (Bitol 0.9.3) | Ownership, quality, SLAs |
| [Example 5](../[ce]-[odps]-[trade]-[2026-05]/README.md) | Data product (ODPS 2.0) | Ports, use cases, governance |
| [Example 6](../[ce]-[slayer]-[mcp]-[2026-05]/README.md) | Semantic layer via MCP (generic) | Zero-code semantic queries |
| [Example 7](../[ce]-[slayer]-[mcp]-[bfsi]-[2026-05]/README.md) | Semantic layer via MCP (BFSI) | Capital adequacy via MCP |
| [Example 8](../[ce]-[ontology]-[bfsi]-[2026-05]/README.md) | OWL/SKOS domain ontology | Concept hierarchy, Basel III articles |
| [Example 9](../[ce]-[metrics]-[bfsi]-[2026-05]/README.md) | dbt Metric Layer (MetricFlow) | Named governed metrics |
| [Example 10](../[ce]-[agentic]-[full-stack]-[2026-05]/README.md) | Full stack comparison | One question, five agents, scored — CE's measurable payoff |
