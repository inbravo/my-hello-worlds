# [ce]-[slayer]-[bfsi]-[2026-05]

## Active Knowledge

knowledge:
  - domains/bfsi
  - technologies/context-fabric

## Engagement Summary

- **Customer:** a European Bank — Impetus (reference architecture)
- **Work:** Context Engineering — SLayer BFSI use case (capital adequacy)
- **Date:** 2026-05
- **Objective:** Register a capital risk DuckDB datasource with a running SLayer instance, auto-ingest the model, and run a CET1/buffer adequacy agent loop against it.
- **Deliverables:** bootstrap_bfsi.py, setup_bfsi.py, agent_slayer_bfsi.py, agent_slayer_bfsi_ollama.py, README.md

## Stack

| Layer | Tool |
|---|---|
| Data | DuckDB (`capital_bfsi.duckdb`) |
| Semantic Layer | SLayer HTTP server at `http://127.0.0.1:5143` |
| Model Registration | `POST /datasources` + `POST /ingest` |
| Agent | Claude via Anthropic SDK / Ollama (qwen2.5) |
| Observability | structlog — logs the SQL SLayer generated |

## Run Order

```bash
cd code/
pip install anthropic openai requests duckdb structlog

# 1. Start SLayer (keep running)
uvx --from 'motley-slayer[all]' slayer serve --demo

# 2. Bootstrap + register (run once each)
python bootstrap_bfsi.py
python setup_bfsi.py

# 3. Run the agent
export ANTHROPIC_API_KEY=sk-ant-...
python agent_slayer_bfsi.py           # Anthropic
python agent_slayer_bfsi_ollama.py    # Ollama
```
