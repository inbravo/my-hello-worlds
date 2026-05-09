# Context Engineering — SLayer Hello World

An AI agent that queries a live SLayer semantic layer via REST. No YAML authoring, no embedded engine. The agent discovers the data model at startup, builds its own tool description, and answers a business question in two turns.

```
agent_slayer_hw.py   — the entire demo, one file
```

---

## Quick Start

**1. Start SLayer with the Jaffle Shop demo:**

```bash
uvx --from 'motley-slayer[all]' slayer serve --demo
```

SLayer starts at `http://127.0.0.1:5143` and preloads the Jaffle Shop dataset — orders, customers, stores, products, and more.

**2. In a separate terminal, run the agent:**

```bash
cd code/
pip install anthropic requests structlog
export ANTHROPIC_API_KEY=sk-ant-...
python agent_slayer_hw.py
```

**3. Capture the trace:**

```bash
python agent_slayer_hw.py > trace.jsonl
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

## Stack

| Layer | Component |
|---|---|
| Data | Jaffle Shop (SLayer built-in demo) |
| Semantic Layer | SLayer HTTP server — `http://127.0.0.1:5143` |
| Query | `POST /query` with formula measures + dimensions |
| Agent | Claude (`claude-sonnet-4-6`) via Anthropic SDK |
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
