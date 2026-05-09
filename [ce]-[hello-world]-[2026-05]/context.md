# [ce]-[hello-world]-[2026-05]

## Active Knowledge

knowledge:
  - domains/bfsi
  - technologies/context-fabric

## Engagement Summary

- **Customer:** a European Bank — Impetus (reference architecture)
- **Work:** Context Engineering hello-world — five-component agentic loop
- **Date:** 2026-05
- **Objective:** Prove the question → data contract → SQL → answer → trace chain in four files, zero Docker
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
pip install anthropic duckdb structlog pyyaml numpy pandas
python bootstrap.py          # once — seeds context_hw.duckdb
python agent.py      # ask the question, 'agent.py' for Anthropic or use 'agent_ollama.py' in case you have local ollama
python agent.py > trace.jsonl  # capture the trace
```
