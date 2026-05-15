# Context — CE ODCS BFSI Demo

## What this is
Demo 3 in the Context Engineering series. Upgrades the hand-written YAML data
contract from Demo 1 to a formal **Bitol/ACRYL Open Data Contract Standard
(ODCS 0.9.3)** contract. Same CET1 capital adequacy data. Same DuckDB runtime.
Richer, governed, standard-compliant context delivered to the LLM.

## What it shows
- How the ODCS standard structures a data contract (info, servers, models, quality, servicelevels)
- How governance metadata (owner, SLA, quality rules) becomes part of the agent's context
- That the agent can answer governance questions AND data questions from the same contract
- The upgrade path from Demo 1 (informal YAML) → Demo 3 (formal ODCS standard)

## Run order
1. `python bootstrap_odcs.py`   — seed capital_odcs.duckdb (once)
2. `python agent_odcs_ollama.py` — run agent (Ollama / local)
3. `python agent_odcs.py`        — run agent (Anthropic API)

## Stack
| Layer       | Component                          |
|-------------|-------------------------------------|
| Standard    | Bitol ODCS 0.9.3                   |
| Contract    | contracts/capital_risk_odcs.yaml   |
| Data        | DuckDB (capital_odcs.duckdb)       |
| Agent (local) | Ollama qwen2.5                   |
| Agent (cloud) | Claude claude-sonnet-4-6         |
| Logging     | structlog JSON                     |

## Series position
| Demo | Folder | Semantic component |
|------|--------|--------------------|
| 1 | [ce]-[hello-world]-[2026-05]      | Hand-written YAML contract |
| 2 | [ce]-[slayer]-[bfsi]-[2026-05]    | Semantic model (SLayer REST) |
| **3** | **[ce]-[odcs]-[bfsi]-[2026-05]** | **Formal ODCS contract (Bitol)** |
| 4 | [ce]-[odps]-[trade]-[2026-05]     | Data Product (DPDS) — coming |
| 5 | [ce]-[ontology]-[bfsi]-[2026-05]  | Ontology OWL/RDF + OBML — coming |
| 6 | [ce]-[metrics]-[bfsi]-[2026-05]   | Metric layer — coming |
| 7 | [ce]-[agentic]-[full-stack]-[2026-05] | Quality comparison — coming |
