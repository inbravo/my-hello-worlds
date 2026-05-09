# [ce]-[slayer]-[hello-world]-[2026-05]

## Active Knowledge

knowledge:
  - domains/bfsi
  - technologies/context-fabric

## Engagement Summary

- **Customer:** Internal — Impetus (reference architecture)
- **Work:** Context Engineering hello-world — SLayer semantic layer variant
- **Date:** 2026-05
- **Objective:** Prove the semantic layer pattern — agent queries named metrics, not raw SQL; SLayer owns the translation
- **Deliverables:** bootstrap.py, capital_db.yaml, capital_position.yaml, agent_slayer.py, README.md

## Stack

| Layer | Tool |
|---|---|
| Data | DuckDB (`context_hw.duckdb`) |
| Semantic Model | `models/capital_position.yaml` (SLayer YAML) |
| Semantic Layer | motley-slayer Python API (local mode) |
| Agent | Claude via Anthropic SDK (tool use) |
| Observability | structlog → console / `trace.jsonl` |

## How This Differs from the Text-to-SQL Demo

In `[ce]-[hello-world]-[2026-05]`, the LLM reads a data contract and writes SQL.
Here, the LLM calls named metrics (`buffer_headroom`, `latest_cet1_ratio`).
SLayer owns the SQL translation. The agent never touches raw SQL.

## Run Order

```bash
cd code/
pip install anthropic duckdb structlog pyyaml numpy pandas "motley-slayer[duckdb]"
export ANTHROPIC_API_KEY=sk-ant-...
python bootstrap.py          # once — seeds context_hw.duckdb
python agent_slayer.py       # ask the question
python agent_slayer.py > trace.jsonl  # capture the trace
```
