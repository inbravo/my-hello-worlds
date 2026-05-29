# Context — CE Ontology BFSI Demo

## What this is
OWL/SKOS ontology demo. The same Basel III/IV capital adequacy data —
now enriched with a formal domain ontology parsed at runtime by rdflib.
The agent understands the concept hierarchy, regulatory references,
formulas, and column-to-concept mappings from the ontology.

## What it shows
- An OWL/SKOS Turtle ontology defines the BFSI capital adequacy domain
- rdflib parses it at runtime and builds the tool description dynamically
- The agent answers both data questions (DuckDB) and domain knowledge
  questions (ontology) from the same tool call
- OBML-style column annotations map DB columns to ontology concepts
- Previous examples knew the schema. This example knows the domain.

## Run order
1. `python bootstrap_ontology.py`     — seed capital_bfsi.duckdb (once)
2. `python agent_ontology_ollama.py`  — run with Ollama/qwen2.5
3. Try domain questions:
   - "Is CET1 Capital a subset of Tier 1 Capital?"
   - "What regulation governs the combined buffer requirement?"
   - "What is the Basel III minimum CET1 ratio and are we above it?"

## Stack
| Layer          | Component                              |
|----------------|----------------------------------------|
| Ontology       | OWL/SKOS Turtle (.ttl) + rdflib parser |
| Domain         | BFSI Capital Adequacy (Basel III/IV)   |
| LLM            | Ollama qwen2.5 / Anthropic Claude      |
| Data           | DuckDB (capital_bfsi.duckdb)           |
| Transport      | OpenAI-compatible tool call            |

## Series position
| Demo | Folder | Semantic component |
|------|--------|--------------------|
| 1 | [ce]-[hello-world]-[2026-05]              | YAML contract |
| 2 | [ce]-[slayer]-[hello-world]-[2026-05]     | SLayer REST — generic |
| 3 | [ce]-[slayer]-[bfsi]-[2026-05]            | SLayer REST — BFSI |
| 4 | [ce]-[odcs]-[bfsi]-[2026-05]              | ODCS contract |
| 5 | [ce]-[odps]-[trade]-[2026-05]             | ODPS data product |
| 6 | [ce]-[slayer]-[mcp]-[2026-05]             | SLayer MCP — generic |
| 7 | [ce]-[slayer]-[mcp]-[bfsi]-[2026-05]      | SLayer MCP — BFSI |
| **8** | **[ce]-[ontology]-[bfsi]-[2026-05]**  | **OWL/SKOS Ontology** |
| 9 | [ce]-[metrics]-[bfsi]-[2026-05]           | Metric layer — coming |
| 10 | [ce]-[agentic]-[full-stack]-[2026-05]    | Full stack — coming |
