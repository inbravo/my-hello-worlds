# Context — CE dbt Metric Layer BFSI Demo

## What this is
dbt Semantic Layer (MetricFlow) demo. The same Basel III/IV capital adequacy
data — now exposed as five named, governed business metrics via MetricFlow.
The agent calls `mf query` via subprocess; it never writes raw SQL.

## What it shows
- 5 metrics defined in MetricFlow YAML: cet1_ratio, combined_buffer_requirement,
  cet1_capital, rwa, buffer_headroom (derived: cet1_ratio - combined_buffer_req)
- `mf query` compiles and executes the SQL — the agent never touches raw data
- Metric descriptions carry Basel III regulatory context (articles, formulas, owners)
- Governance question answered from the catalogue; data questions via mf query

## Run order
1. `pip install dbt-core dbt-duckdb dbt-metricflow`
2. `python3 bootstrap_metrics.py`     — dbt run + mf validate-configs
3. `python3 agent_metrics_ollama.py`  — run with Ollama/qwen2.5
4. Try: `python3 agent_metrics_ollama.py "Show CET1 ratio trend by quarter"`

## Stack
| Layer          | Component                                    |
|----------------|----------------------------------------------|
| Metric layer   | dbt Semantic Layer (MetricFlow YAML)         |
| Query engine   | mf query CLI (subprocess)                    |
| dbt adapter    | dbt-duckdb                                   |
| LLM            | Ollama qwen2.5 / Anthropic Claude            |
| Data           | DuckDB (capital_bfsi.duckdb via dbt model)   |

## Series position
| Demo | Folder | Semantic component |
|------|--------|--------------------|
| 1–7  | ...    | YAML / SLayer / ODCS / ODPS / MCP |
| 8  | [ce]-[ontology]-[bfsi]-[2026-05]          | OWL/SKOS Ontology |
| **9** | **[ce]-[metrics]-[bfsi]-[2026-05]**    | **dbt Metric Layer (MetricFlow)** |
| 10 | [ce]-[agentic]-[full-stack]-[2026-05]    | Full stack — coming |
