# Hello Worlds: First Contact with a Technology
Minimal, working examples across the agentic AI stack — MCP servers, agent frameworks, context pipelines, and the scaffolding nobody documents properly.

---

## Repository Structure

This repository contains **four examples** organized in separate folders, each introducing a new semantic component in the Context Engineering ladder:

### 📂 Directory Listing

| # | Folder | Semantic Component | Description |
|---|---|---|---|
| 1 | [[ce]-[hello-world]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bhello-world%5D-%5B2026-05%5D) | Hand-written YAML contract | CE baseline — agent reads a data contract and writes its own SQL |
| 2 | [[ce]-[slayer]-[hello-world]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bslayer%5D-%5Bhello-world%5D-%5B2026-05%5D) | Semantic model — generic | Agent queries a live semantic layer via REST. No SQL written by the agent |
| 3 | [[ce]-[slayer]-[bfsi]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bslayer%5D-%5Bbfsi%5D-%5B2026-05%5D) | Semantic model — BFSI domain | Real datasource registered into a semantic layer. BFSI capital adequacy use case |
| 4 | [[ce]-[odcs]-[bfsi]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bodcs%5D-%5Bbfsi%5D-%5B2026-05%5D) | Formal ODCS contract (Bitol 0.9.3) | Upgrades the YAML contract to a governed standard — adds ownership, quality checks, SLA, and freshness metadata |

---

## Semantics and Context Engineering

If you have understood the purpose of the Semantic layer, Context Engineering follows naturally — it is the discipline of designing, structuring, and governing the business context delivered to the LLM, at the right time and in the right format, so it reasons and acts correctly on your data. CE is not a one-time activity. The outcome it continuously produces and maintains is the semantic layer itself — a living, structured representation of the business meaning of customer data. Put simply: **good Context Engineering produces good semantics.**

Semantic is a broader term including these components:

---

| Layer | What it captures | Examples |
|---|---|---|
| **Data Contract** | Schema, ownership, SLAs, freshness, lineage | YAML contracts, dbt sources, Great Expectations |
| **Ontology** | Concepts, relationships, classifications in a domain | FIBO (banking), SNOMED (healthcare), OWL/RDF |
| **Semantic Model** | Business definitions mapped to physical data | LookML, MetricFlow, Cube schema, SLayer model |
| **Knowledge Graph** | Entities, relationships, traversable connections | Neo4j, AWS Neptune, Google KG |
| **Metric Layer** | Named, governed business metrics with formulas | dbt Metrics, Cube measures, Atscale |

---

**How they relate:**

- A **data contract** says: *"this table exists, has these columns, owned by this team, refreshed daily"*
- An **ontology** says: *"CET1 Capital is a subclass of Regulatory Capital, which is governed by Basel III"*
- A **semantic model** says: *"cet1_ratio_pct = CET1 Capital ÷ RWA × 100, display as percentage"*
- A **knowledge graph** says: *"BANK_HOLDCO → holds → BANK_SUBSIDIARY → reports → CET1 position"*
- A **metric layer** says: *"CET1 Headroom = cet1_ratio_pct − combined_buffer, flagged if < 1pp"*

---

## 🎯 Overview of Examples

### Example 1: Data Contract-based Semantic Layer (Component 1)

**What it shows:**
- Clients have "AI agents." Context engineering is the missing piece — it's the discipline of giving the LLM precisely the right context, in a structured and governed way, so it acts correctly on your data.
- A bank's capital reporting team gets asked the same questions every quarter: *What's our current CET1 ratio? How much buffer headroom do we have?* The data is in a table. The friction is in writing and maintaining SQL against a schema that changes with every regulatory update.
- This demo replaces that friction. An AI agent reads a data contract — a YAML file that describes what the data means in plain English — then writes its own SQL, queries a DuckDB database, and returns a clear answer. No hardcoded prompts. No vector store. No custom fine-tuning. Just a structured contract and a two-turn agent loop.

**Quick Start (4 commands):**
```bash
git clone https://github.com/inbravo/my-hello-worlds
cd my-hello-worlds/[ce]-[hello-world]-[2026-05]/code
pip install duckdb structlog pyyaml numpy pandas anthropic 
python bootstrap.py && python agent.py
```

**Options:** Use Claude via Anthropic API or any local model via Ollama

---

### Example 2: MCP-compatible Semantic Layer (Component 3) - BFSI

**What it shows:**
- A production-grade pattern that brings Context Engineering closer to real-world scenarios. Instead of a YAML data contract, it uses a proper running semantic model (using Slayer) that the agent discovers and queries via the MCP/REST API.
- The agent never writes SQL; the semantic layer compiles it. The same semantic layer can be wired directly into any agent. A governed, schema-aware layer that sits between the agent and the data, translating the business story into agentic language.

**Quick Start (fully local):**
```bash
git clone https://github.com/inbravo/my-hello-worlds
uvx --from 'motley-slayer[all]' slayer serve --demo
ollama serve && ollama pull qwen2.5
cd my-hello-worlds/[ce]-[slayer]-[bfsi]-[2026-05]/code
pip install openai requests duckdb structlog 'motley-slayer[all]'
python bootstrap_bfsi.py && python setup_bfsi.py && python agent_slayer_bfsi_ollama.py
```

**Options:** Use Anthropic API or Ollama for local inference

---

### Example 3: Formal ODCS Data Contract — Bitol 0.9.3 (Component 1 — governed)

**What it shows:**
- Upgrades the hand-written YAML contract from Example 1 to a formal **Bitol/ACRYL Open Data Contract Standard (ODCS 0.9.3)** contract — the same concept, done the right way.
- The contract now includes ownership, quality checks (SodaCL), freshness SLAs, usage terms, and retention policy. The agent reads all of it and can answer both data questions *and* governance questions from the same contract.
- Demo 1 could answer: *"What is our CET1 ratio?"* Demo 3 answers: *"What is our CET1 ratio — is this data certified, how fresh is it, and who owns it?"*

**Quick Start (fully local):**
```bash
cd my-hello-worlds/[ce]-[odcs]-[bfsi]-[2026-05]/code
pip install openai duckdb pyyaml structlog
ollama serve && ollama pull qwen2.5
python bootstrap_odcs.py && python agent_odcs_ollama.py
```

**Options:** Use Anthropic API or Ollama for local inference

---

## � Next Steps & Learning Path

After running the examples, here's how to deepen your understanding:

### Learning Progression

1. **Example 1** — Hand-written YAML contract. Understand how a data contract gives an LLM structured context to write its own SQL. The CE baseline.
2. **Example 2** — Semantic model (SLayer, generic dataset). Learn how a semantic layer works. Agent queries via REST, never writes SQL.
3. **Example 3** — Semantic model (SLayer, BFSI domain). Register a real datasource into a semantic layer and run a domain agent against it.
4. **Example 4** — Formal ODCS contract (Bitol 0.9.3). Understand how a governed, standard-compliant contract enriches agent context with ownership, quality, and SLA metadata.
5. **Coming** — Data product (DPDS), Ontology (OWL/RDF + OBML), Metric layer, Full stack quality comparison.

### Customization Ideas

- **Add custom domains** beyond BFSI (healthcare, e-commerce, supply chain)
- **Change the LLM** - swap Anthropic Claude for OpenAI GPT or local models
- **Add multi-turn conversations** - extend agents for complex dialogues
- **Implement monitoring** - add logging to track agent decisions and SQL generation
- **Connect real databases** - replace DuckDB with PostgreSQL, Snowflake, or BigQuery

---

## 🏗️ Architecture

### Example 1: Data Contract Flow

```
┌──────────────┐
│  Data        │
│  Contract    │  (YAML)
│  (Semantic)  │
└──────┬───────┘
       │
       ▼
┌──────────────────┐        ┌─────────────┐
│   LLM Agent      │◄──────►│  DuckDB     │
│  (generates SQL) │        │ (executes)  │
└──────┬───────────┘        └─────────────┘
       │
       ▼
 ┌───────────────┐
 │ Business      │
 │ Answer        │
 └───────────────┘
```

### Example 2: MCP Semantic Layer Flow

```
┌──────────────────┐
│  Business Query  │
│   (plain text)   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   LLM Agent      │
│ (understands Q)  │
└──────┬───────────┘
       │
       ▼
┌──────────────────────────┐
│   Slayer Semantic Model  │  (MCP/REST API)
│  (discovers entities)    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────┐        ┌─────────────┐
│  Semantic Layer  │◄──────►│   Data      │
│  (compiles SQL)  │        │ (database)  │
└──────┬───────────┘        └─────────────┘
       │
       ▼
 ┌───────────────┐
 │ Governed      │
 │ Answer        │
 └───────────────┘
```

**Key Difference:** In Example 1, the agent writes SQL. In Example 2, the semantic layer compiles SQL based on business metrics—more controlled, auditable, and reliable.

---

## 📚 Glossary & Terminology

| Term | Definition |
|------|-----------|
| **AI Agent** | An autonomous system that understands natural language questions and takes actions (writing SQL, querying data, reasoning) to find answers. |
| **Context Engineering (CE)** | The discipline of structuring and governing business context so LLMs reason correctly on your data. |
| **Data Contract** | A YAML or JSON file that documents what a dataset means, who owns it, SLAs, freshness, and lineage. Bridges semantic and technical layers. |
| **DuckDB** | An in-process SQL database optimized for analytical queries. Used in Example 1 for fast, local execution. |
| **LLM** | Large Language Model (e.g., Claude, GPT-4, Qwen). Powers the agent's reasoning and language understanding. |
| **MCP** | Model Context Protocol. A standard for agents to discover and query semantic models and APIs in a structured way. |
| **Ollama** | A local LLM inference engine. Allows running models like Qwen 2.5 on your machine without cloud APIs. |
| **Semantic Layer** | A governed, business-friendly abstraction over raw data. Defines what metrics and dimensions mean in business terms. |
| **Semantic Model** | A structured representation of business entities, relationships, and calculations. Can be YAML, dbt, LookML, or SQL. |
| **Slayer** | An open-source semantic modeling framework (by Motley Data). Compiles business questions into SQL queries. |
| **YAML** | Human-readable data format. Used for data contracts and configuration in Example 1. |

---

## �📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

Amit Dixit
