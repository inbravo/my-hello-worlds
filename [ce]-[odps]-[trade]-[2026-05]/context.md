# Context — CE ODPS Trade Finance Demo

## What this is
Demo 4 in the Context Engineering series. Introduces the **Open Data Product
Standard (ODPS 2.0)** as the agent's context layer. Upgrades from a
table-level contract (ODCS, Demo 3) to a **product-level definition** — one
that describes a business capability, not just a schema.

New domain: **Trade Finance** — counterparty exposure, settlement risk,
credit concentration. Shows CE is not BFSI capital adequacy-specific.

## What it shows
- How a data product definition differs from a data contract — product has
  input ports, output ports, SLAs, use cases, and ownership at the capability level
- How the agent reads product-level context to answer domain questions
- That CE applies equally to trade finance as to capital adequacy
- The upgrade path: YAML → ODCS → ODPS (each layer adds governance maturity)

## Run order
1. `python bootstrap_odps.py`    — seed trade_odps.duckdb (once)
2. `python agent_odps_ollama.py` — run agent (Ollama / local)
3. `python agent_odps.py`         — run agent (Anthropic API)

## Stack
| Layer         | Component                              |
|---------------|----------------------------------------|
| Standard      | Open Data Product Standard (ODPS) 2.0 |
| Product file  | products/trade_exposure_product.yaml  |
| Data          | DuckDB (trade_odps.duckdb)            |
| Agent (local) | Ollama qwen2.5                        |
| Agent (cloud) | Claude claude-sonnet-4-6              |
| Logging       | structlog JSON                        |

## Series position
| Demo | Folder | Semantic component |
|------|--------|--------------------|
| 1 | [ce]-[hello-world]-[2026-05]          | Hand-written YAML contract |
| 2 | [ce]-[slayer]-[hello-world]-[2026-05] | Semantic model — generic (SLayer) |
| 3 | [ce]-[slayer]-[bfsi]-[2026-05]        | Semantic model — BFSI domain |
| 4 | [ce]-[odcs]-[bfsi]-[2026-05]          | Formal ODCS contract (Bitol 0.9.3) |
| **5** | **[ce]-[odps]-[trade]-[2026-05]**  | **Data product (ODPS 2.0)** |
| 6 | [ce]-[ontology]-[bfsi]-[2026-05]      | Ontology OWL/RDF + OBML — coming |
| 7 | [ce]-[metrics]-[bfsi]-[2026-05]       | Metric layer — coming |
| 8 | [ce]-[agentic]-[full-stack]-[2026-05] | Quality comparison — coming |
