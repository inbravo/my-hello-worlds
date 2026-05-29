# Context Engineering — dbt Metric Layer BFSI Demo

**Example 9 of the CE series.** The same Basel III/IV capital adequacy data —
now exposed as five **named, governed business metrics** via the dbt Semantic
Layer (MetricFlow). The agent never writes SQL. It queries metrics by name.

```
dbt_project/
├── dbt_project.yml
├── profiles.yml                     ← points to capital_bfsi.duckdb
└── models/
    ├── capital_position.sql         ← dbt model (seeds the data)
    ├── metricflow_time_spine.sql    ← required by MetricFlow
    └── schema.yml                   ← semantic model + 5 metrics

code/
├── bootstrap_metrics.py             ← dbt run + mf validate-configs
└── agent_metrics_ollama.py          ← Ollama agent (calls mf query)
```

---

## What changes from previous examples

| | Examples 1–8 | Example 9 — Metric Layer |
|---|---|---|
| Context source | YAML / SLayer / ODCS / ODPS / ontology | dbt MetricFlow metric definitions |
| Agent queries | Raw SQL / SLayer REST or MCP / mf ontology | `mf query --metrics <name>` |
| SQL author | LLM (Ex 1) or SLayer (Ex 2–7) | **MetricFlow — never the agent** |
| Metric ownership | Not tracked | Named owner in metric description |
| Metric versioning | None | dbt project version-controlled |
| Derived metrics | Manual formula in prompt | `buffer_headroom` = derived metric in YAML |
| Governance guarantee | None | Every consumer of `cet1_ratio` gets the same number |

**The key shift:** A semantic layer (SLayer) knows *how to query* your data.
A metric layer knows *what your metrics mean* — and enforces that definition
for every consumer, every time.

---

## What is a Metric Layer?

A metric layer sits above the semantic layer. It defines named, versioned,
governed business metrics — not just SQL queries.

| Layer | Knows | Example |
|---|---|---|
| Raw data | Columns and types | `cet1_ratio_pct DECIMAL` |
| Semantic model | Measures and dimensions | `SUM(cet1_capital_mm) / SUM(rwa_mm)` |
| **Metric layer** | **Business meaning + governance** | `cet1_ratio` — owned by Treasury Risk, min 4.5% per Basel III Art. 92, certified |

---

## The 5 Metrics — `schema.yml`

| Metric | Type | Label | Basel III ref |
|---|---|---|---|
| `cet1_ratio` | simple | CET1 Ratio (%) | Article 92 — min 4.5% |
| `combined_buffer_requirement` | simple | Combined Buffer (%) | Article 128-131 |
| `cet1_capital` | simple | CET1 Capital (MM) | Article 26-50 |
| `rwa` | simple | Risk-Weighted Assets (MM) | Basel III |
| `buffer_headroom` | **derived** | Buffer Headroom (pp) | Article 141 — distribution gate |

`buffer_headroom` is a **derived metric**: MetricFlow computes it as
`cet1_ratio − combined_buffer_requirement` — no manual formula in the agent.

---

## Quick Start

**Step 1 — Install dependencies:**
```bash
pip install dbt-core dbt-duckdb dbt-metricflow openai structlog
ollama pull qwen2.5
```

**Step 2 — Bootstrap (run once):**
```bash
cd code/
python3 bootstrap_metrics.py
```

```
[dbt run]
  1 of 2 OK  capital_position
  2 of 2 OK  metricflow_time_spine

[mf validate-configs]
  ✔ Successfully validated metrics against data warehouse (ERRORS: 0)

Metrics defined:
  cet1_ratio              — CET1 Capital / RWA × 100 (%)
  combined_buffer_req     — Combined Buffer Requirement (%)
  cet1_capital            — CET1 Capital (MM)
  rwa                     — Risk-Weighted Assets (MM)
  buffer_headroom         — CET1 Ratio − Combined Buffer (pp) [derived]
```

**Step 3 — Run the agent:**
```bash
python3 agent_metrics_ollama.py
```

---

## Sample Questions

### Data questions (calls `mf query`):
```
What is our current CET1 ratio and buffer headroom?
Show the CET1 ratio trend across all three quarters.
What is our total risk-weighted asset position?
How has CET1 capital grown since Q3 2025?
```

### Governance questions (answered from metric catalogue — no mf query needed):
```
Who owns the CET1 ratio metric?
What is the formula for buffer headroom?
What happens if buffer headroom turns negative?
Which Basel III article governs the combined buffer requirement?
```

### Direct mf query (CLI — no agent needed):
```bash
mf query --metrics cet1_ratio,buffer_headroom --group-by metric_time__month
mf query --metrics cet1_capital,rwa --group-by metric_time__month
mf query --metrics buffer_headroom --order -buffer_headroom
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              schema.yml — MetricFlow Metric Catalogue   │
│                                                         │
│  cet1_ratio              (simple · owner: Treasury Risk)│
│  combined_buffer_req     (simple · Basel III Art. 128)  │
│  cet1_capital            (simple · Basel III Art. 26)   │
│  rwa                     (simple · Basel III)           │
│  buffer_headroom         (derived: cet1_ratio - buffer) │
└─────────────────────────────┬───────────────────────────┘
                              │  read at startup → tool description
                              ▼
            ┌──────────────────────────────────┐
            │          LLM Agent               │
            │  (Ollama qwen2.5)                │
            │  Knows metric definitions,       │
            │  Basel III thresholds, owners    │
            └────────────┬─────────────────────┘
                         │  tool call: query_metric
                         │  {metrics: ["cet1_ratio","buffer_headroom"],
                         │   group_by: ["metric_time__month"]}
                         ▼
            ┌──────────────────────────────────┐
            │   mf query (subprocess)          │
            │   MetricFlow compiles SQL        │
            │   Runs against DuckDB            │
            └────────────┬─────────────────────┘
                         │
                         ▼
            ┌──────────────────────────────────────────┐
            │  metric_time__month  cet1_ratio  headroom │
            │  2025-09-01          14.39        4.64    │
            │  2025-12-01          14.66        4.91    │
            │  2026-03-01          14.83        5.08    │
            └──────────────────────────────────────────┘
```

**Key difference from Example 8 (Ontology):** The ontology says what CET1 Ratio
*is*. The metric layer governs how it is *computed and consumed* — the formula
is enforced by MetricFlow, not left to the agent or analyst to implement.

---

## CE Series

| Example | Semantic component | What the agent knows |
|---------|-------------------|----------------------|
| [Ex 1](../[ce]-[hello-world]-[2026-05]/README.md) | YAML contract | Schema |
| [Ex 2–3](../[ce]-[slayer]-[bfsi]-[2026-05]/README.md) | SLayer REST | Measures + dimensions |
| [Ex 4](../[ce]-[odcs]-[bfsi]-[2026-05]/README.md) | ODCS | Ownership + quality + SLA |
| [Ex 5](../[ce]-[odps]-[trade]-[2026-05]/README.md) | ODPS | Product ports + use cases |
| [Ex 6–7](../[ce]-[slayer]-[mcp]-[bfsi]-[2026-05]/README.md) | SLayer MCP | Zero-code semantic queries |
| [Ex 8](../[ce]-[ontology]-[bfsi]-[2026-05]/README.md) | OWL/SKOS Ontology | Domain concept hierarchy |
| **Ex 9 (this)** | **dbt Metric Layer** | **Named governed metrics — formula enforced, not assumed** |
| Ex 10 | Full stack | Coming |

---

## Stack

| Layer | Component |
|---|---|
| Metric layer | dbt Semantic Layer — MetricFlow YAML |
| dbt adapter | dbt-duckdb |
| Query CLI | `mf query` (MetricFlow, Apache 2.0) |
| LLM (local) | Ollama qwen2.5 |
| Data | DuckDB (`capital_bfsi.duckdb` via dbt model) |
| Domain | BFSI — Basel III/IV Capital Adequacy |
