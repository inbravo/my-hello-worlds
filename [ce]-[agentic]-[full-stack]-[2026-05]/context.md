# Context — CE Full Stack Comparison

## What this is
Capstone demo. One question through five agents with increasing context
richness. Scored comparison shows exactly which semantic layer unlocks
which part of the answer.

## What it shows
- Baseline (schema only) answers 1/5 parts of a complex regulatory question
- Each added layer — YAML, ODCS, Ontology, Metric Layer — unlocks more
- Full Stack (all layers) answers 5/5 — the CE payoff made visible
- No new data. No new model. Just better context = better answers.

## The question
"What is our current CET1 ratio, how does it compare to the Basel III
minimum, who owns this data and when was it last certified, and what
happens if our buffer headroom turns negative?"

## Prerequisites (must run first)
- Example 1  bootstrap: seeds YAML contract
- Example 4  bootstrap: seeds ODCS contract
- Example 8  ontology:  bfsi_capital.ttl (checked in — no bootstrap needed)
- Example 9  bootstrap: seeds dbt project + MetricFlow metrics

## Run order
1. `python3 bootstrap_full_stack.py`  — validates prereqs, seeds local DB
2. `python3 run_comparison.py`        — runs 5 agents, prints scored table

## Series position
| Demo | Folder | Semantic component |
|------|--------|--------------------|
| 1  | [ce]-[hello-world]-[2026-05]              | YAML contract |
| 2  | [ce]-[slayer]-[hello-world]-[2026-05]     | SLayer REST — generic |
| 3  | [ce]-[slayer]-[bfsi]-[2026-05]            | SLayer REST — BFSI |
| 4  | [ce]-[odcs]-[bfsi]-[2026-05]              | ODCS contract |
| 5  | [ce]-[odps]-[trade]-[2026-05]             | ODPS data product |
| 6  | [ce]-[slayer]-[mcp]-[2026-05]             | SLayer MCP — generic |
| 7  | [ce]-[slayer]-[mcp]-[bfsi]-[2026-05]      | SLayer MCP — BFSI |
| 8  | [ce]-[ontology]-[bfsi]-[2026-05]          | OWL/SKOS ontology |
| 9  | [ce]-[metrics]-[bfsi]-[2026-05]           | dbt Metric Layer |
| **10** | **[ce]-[agentic]-[full-stack]-[2026-05]** | **Full stack comparison** |
