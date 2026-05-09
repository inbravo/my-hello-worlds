# [ce]-[hello-world]-[2026-05]

## Active Knowledge

knowledge:
  - domains/bfsi
  - technologies/context-fabric

## Engagement Summary

- **Customer:** Internal — Impetus (reference architecture)
- **Work:** Context Engineering hello-world — five-component agentic loop
- **Date:** 2026-05
- **Objective:** Prove the question → contract → SQL → answer → trace chain in four files, zero Docker
- **Deliverables:** bootstrap.py, capital_risk.yaml, agent.py, trace.jsonl (runtime output)

## Stack

| Layer | Tool |
|---|---|
| Data | DuckDB (`context_hw.duckdb`) |
| Data Contract | `contracts/capital_risk.yaml` |
| Agent | Claude via Anthropic SDK (tool use) |
| Observability | structlog → console / `trace.jsonl` |

## Run Order

```bash
cd code/
pip install anthropic duckdb structlog pyyaml
python bootstrap.py          # once — seeds context_hw.duckdb
python agent.py              # ask the question
python agent.py > trace.jsonl  # capture the trace
```
