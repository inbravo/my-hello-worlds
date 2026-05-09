# [ce]-[slayer]-[hello-world]-[2026-05]

## Active Knowledge

knowledge:
  - domains/bfsi
  - technologies/context-fabric

## Engagement Summary

- **Customer:** Internal — Impetus (reference architecture)
- **Work:** Context Engineering — SLayer hello world via REST API
- **Date:** 2026-05
- **Objective:** Agent queries a running SLayer server (Jaffle Shop demo) via REST. No YAML authoring, no embedded engine. Proves the question → model discovery → SLayer query → answer loop.
- **Deliverables:** agent_slayer_hw.py, README.md

## Stack

| Layer | Tool |
|---|---|
| Data | Jaffle Shop demo (built into SLayer) |
| Semantic Layer | SLayer HTTP server at `http://127.0.0.1:5143` |
| Agent | Claude via Anthropic SDK (tool use) |
| Observability | structlog → console / `trace.jsonl` |

## Prerequisites

SLayer must be running before the agent starts:
```bash
uvx --from 'motley-slayer[all]' slayer serve --demo
```

## Run

```bash
cd code/
pip install anthropic requests structlog
export ANTHROPIC_API_KEY=sk-ant-...
python agent_slayer_hw.py
```
