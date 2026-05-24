# Hello Worlds: First Contact with a Technology
Minimal, working examples across the agentic AI stack — MCP servers, agent frameworks, context pipelines, and the scaffolding nobody documents properly.

---

## Repository Structure

This repository contains **five examples** organized in separate folders, each introducing a new semantic component in the Context Engineering ladder:

### 📂 Directory Listing

| # | Folder | Semantic Component | Description |
|---|---|---|---|
| 1 | [[ce]-[hello-world]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bhello-world%5D-%5B2026-05%5D) | Hand-written YAML contract | CE baseline — agent reads a data contract and writes its own SQL |
| 2 | [[ce]-[slayer]-[hello-world]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bslayer%5D-%5Bhello-world%5D-%5B2026-05%5D) | Semantic model — generic | Agent queries a live semantic layer via REST. No SQL written by the agent |
| 3 | [[ce]-[slayer]-[bfsi]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bslayer%5D-%5Bbfsi%5D-%5B2026-05%5D) | Semantic model — BFSI domain | Real datasource registered into a semantic layer. BFSI capital adequacy use case |
| 4 | [[ce]-[odcs]-[bfsi]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bodcs%5D-%5Bbfsi%5D-%5B2026-05%5D) | Formal ODCS contract (Bitol 0.9.3) | Upgrades the YAML contract to a governed standard — adds ownership, quality checks, SLA, and freshness metadata |
| 5 | [[ce]-[odps]-[trade]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bodps%5D-%5Btrade%5D-%5B2026-05%5D) | Data product (ODPS 2.0) | Steps up from table governance to product governance — ports, use cases, SLAs. New domain: Trade Finance |

---

## Semantics and Context Engineering

If you have understood the purpose of the Semantic layer, Context Engineering follows naturally — it is the discipline of designing, structuring, and governing the business context delivered to the LLM, at the right time and in the right format, so it reasons and acts correctly on your data. CE is not a one-time activity. The outcome it continuously produces and maintains is the semantic layer itself — a living, structured representation of the business meaning of your data. Put simply: **good Context Engineering produces good semantics.**

Semantic is a broader term including these components:

---

| # | Component | What it captures | Examples |
|---|---|---|---|
| 1 | **Data Contract** | Schema, ownership, SLAs, freshness, lineage | YAML contracts (Databricks/Snowflake), Bitol ODCS |
| 2 | **Ontology** | Concepts, relationships, classifications in a domain | FIBO (banking), SNOMED (healthcare), OWL/RDF, OBML |
| 3 | **Semantic Model** | Business definitions mapped to physical data | LookML, MetricFlow, Cube schema, SLayer |
| 4 | **Knowledge Graph** | Entities, relationships, traversable connections | Neo4j, AWS Neptune, Google KG |
| 5 | **Metric Layer** | Named, governed business metrics with formulas | Databricks Metric views, dbt Metrics, Cube measures, AtScale |

---

**How they relate:**

- A **data contract** says: *"this table exists, has these columns, owned by this team, refreshed daily"*
- An **ontology** says: *"CET1 Capital is a subclass of Regulatory Capital, which is governed by Basel III"*
- A **semantic model** says: *"cet1_ratio_pct = CET1 Capital ÷ RWA × 100, display as percentage"*
- A **knowledge graph** says: *"BANK_HOLDCO → holds → BANK_SUBSIDIARY → reports → CET1 position"*
- A **metric layer** says: *"CET1 Headroom = cet1_ratio_pct − combined_buffer, flagged if < 1pp"*

The principle is simple — **the better the CE, the better the semantics, and the more trustworthy the AI.**

---

## 🎯 Overview of Examples

### Example 1: Hand-written YAML Data Contract

**Semantic component:** Data Contract (Component 1 — informal)

**What it shows:**
- An AI agent reads a hand-written YAML data contract describing a bank's capital position, writes its own SQL, and answers a Basel III question. No hardcoded prompts. No vector store. No fine-tuning.
- The friction of writing and maintaining SQL against a changing regulatory schema is replaced by a structured contract and a two-turn agent loop.

**Quick Start:**
```bash
git clone https://github.com/inbravo/my-hello-worlds
cd my-hello-worlds/[ce]-[hello-world]-[2026-05]/code
pip install duckdb structlog pyyaml anthropic
python bootstrap.py && python agent_ollama.py
```

**Options:** Anthropic API (`agent.py`) or Ollama (`agent_ollama.py`)

---

### Example 2: Semantic Layer — Generic (SLayer + Jaffle Shop)

**Semantic component:** Semantic Model (Component 3 — generic dataset)

**What it shows:**
- Agent queries a live SLayer semantic layer via REST API. Discovers the data model at startup. Never writes SQL — the semantic layer compiles it.
- Uses the built-in Jaffle Shop demo dataset (orders, stores, customers).

**Quick Start:**
```bash
pip install 'motley-slayer[all]'
slayer serve --demo
cd my-hello-worlds/[ce]-[slayer]-[hello-world]-[2026-05]/code
pip install openai requests structlog
ollama serve && ollama pull qwen2.5
python agent_slayer_ollama_hw.py
```

**Options:** Anthropic API (`agent_slayer_hw.py`) or Ollama (`agent_slayer_ollama_hw.py`)

---

### Example 3: Semantic Layer — BFSI Domain (SLayer + Capital Position)

**Semantic component:** Semantic Model (Component 3 — domain-specific)

**What it shows:**
- Registers a real DuckDB datasource into SLayer and runs a capital adequacy agent against it.
- The agent discovers the `capital_position` model at runtime and answers CET1 / buffer headroom questions. SLayer logs the SQL it compiled — the observable trace.

**Quick Start:**
```bash
pip install 'motley-slayer[all]'
slayer serve --demo
cd my-hello-worlds/[ce]-[slayer]-[bfsi]-[2026-05]/code
pip install openai requests duckdb structlog
ollama serve && ollama pull qwen2.5
python bootstrap_bfsi.py && python setup_bfsi.py && python agent_slayer_bfsi_ollama.py
```

**Options:** Anthropic API (`agent_slayer_bfsi.py`) or Ollama (`agent_slayer_bfsi_ollama.py`)

---

### Example 4: Formal ODCS Data Contract — Bitol 0.9.3

**Semantic component:** Data Contract (Component 1 — governed, standard-compliant)

**What it shows:**
- Upgrades the hand-written YAML from Example 1 to a formal **Bitol/ACRYL ODCS 0.9.3** contract — same concept, done the right way.
- The contract adds ownership, quality checks (SodaCL), freshness SLAs, usage terms, and retention policy. The agent answers both data and governance questions from the same contract.
- Example 1 answers: *"What is our CET1 ratio?"* Example 4 answers: *"What is our CET1 ratio — is this data certified, how fresh is it, and who owns it?"*

**Quick Start:**
```bash
cd my-hello-worlds/[ce]-[odcs]-[bfsi]-[2026-05]/code
pip install openai duckdb pyyaml structlog
ollama serve && ollama pull qwen2.5
python bootstrap_odcs.py && python agent_odcs_ollama.py
```

**Options:** Anthropic API (`agent_odcs.py`) or Ollama (`agent_odcs_ollama.py`)

---

### Example 5: Data Product — ODPS 2.0 (Trade Finance)

**Semantic component:** Data Product (above Component 1 — product governance)

**What it shows:**
- Steps up from table-level governance (ODCS) to **product-level governance** using the Open Data Product Standard (ODPS 2.0).
- The agent reads a full product definition — input ports, output ports, use cases, SLAs, quality rules, and ownership — and answers exposure, settlement risk, and governance questions.
- New domain: **Trade Finance** (counterparty exposure, settlement risk, credit concentration) — shows CE is not BFSI capital adequacy-specific.
- ODPS is to data products what OpenAPI is to REST APIs — a standard spec that makes data products discoverable, understandable, and governable.

**Quick Start:**
```bash
cd my-hello-worlds/[ce]-[odps]-[trade]-[2026-05]/code
pip install openai duckdb pyyaml structlog
ollama serve && ollama pull qwen2.5
python bootstrap_odps.py && python agent_odps_ollama.py
```

**Options:** Anthropic API (`agent_odps.py`) or Ollama (`agent_odps_ollama.py`)

---

## 📈 Learning Progression

Run the examples in this order for the clearest learning curve:

| Step | Example | What you learn |
|---|---|---|
| 1 | Example 1 — YAML contract | How a data contract gives an LLM context to write its own SQL. The CE baseline. |
| 2 | Example 2 — SLayer (generic) | How a semantic layer works. Agent queries via REST, never writes SQL. |
| 3 | Example 3 — SLayer (BFSI) | How to register a real datasource into a semantic layer and run a domain agent. |
| 4 | Example 4 — ODCS (Bitol) | How a governed, standard-compliant contract adds ownership, quality, and SLA context. |
| 5 | Example 5 — ODPS (Trade Finance) | How a data product definition governs at the capability level — ports, use cases, pricing. |
| Coming | Ontology (OWL/RDF + OBML) | How domain knowledge elevates agent reasoning beyond schema. |
| Coming | Metric layer | How named, governed metrics become agent context. |
| Coming | Full stack comparison | One question. All layers. Measurable quality difference. |

---

## 🏗️ Architecture

### Example 1: Hand-written YAML Contract

```
┌──────────────────┐
│  YAML Contract   │  (informal, hand-written)
│  table + columns │
│  + description   │
└──────┬───────────┘
       │  injected into tool description
       ▼
┌──────────────────┐        ┌─────────────┐
│   LLM Agent      │◄──────►│   DuckDB    │
│  (generates SQL) │        │ (executes)  │
└──────┬───────────┘        └─────────────┘
       │
       ▼
 ┌─────────────────┐
 │  Business Answer │
 └─────────────────┘
```

---

### Example 2 & 3: Semantic Layer (SLayer REST API)

```
┌──────────────────┐
│  Business Query  │
│   (plain text)   │
└──────┬───────────┘
       ▼
┌──────────────────┐
│   LLM Agent      │  discovers model at startup via GET /models
└──────┬───────────┘
       ▼
┌──────────────────────────┐
│   SLayer Semantic Model  │  POST /query (REST / MCP)
│  measures, dimensions    │
└──────┬───────────────────┘
       ▼
┌──────────────────┐        ┌─────────────┐
│  Semantic Layer  │◄──────►│   DuckDB    │
│  (compiles SQL)  │        │             │
└──────┬───────────┘        └─────────────┘
       ▼
 ┌──────────────────┐
 │  Governed Answer  │  + SQL trace logged
 └──────────────────┘
```

**Key difference from Example 1:** The agent never writes SQL. The semantic layer compiles it — more controlled, auditable, and reliable.

---

### Example 4: ODCS Formal Data Contract (Bitol 0.9.3)

```
┌─────────────────────────────────────────────────┐
│            ODCS Contract (Bitol 0.9.3)          │
│  ┌───────────┐  ┌─────────┐  ┌───────────────┐  │
│  │   info    │  │ models  │  │    quality    │  │
│  │  owner    │  │ fields  │  │  SodaCL checks│  │
│  │  status   │  │ descrip.│  │               │  │
│  └───────────┘  └─────────┘  └───────────────┘  │
│  ┌───────────┐  ┌─────────┐  ┌───────────────┐  │
│  │  servers  │  │  terms  │  │ servicelevels │  │
│  │  (DuckDB) │  │  usage  │  │ SLA/freshness │  │
│  └───────────┘  └─────────┘  └───────────────┘  │
└───────────────────────┬─────────────────────────┘
                        │  all sections injected into tool description
                        ▼
         ┌──────────────────────────┐
         │        LLM Agent         │
         │  (data + governance Q's) │
         └──────────┬───────────────┘
                    │  generates SQL
                    ▼
         ┌──────────────────┐
         │     DuckDB       │
         └──────────┬───────┘
                    ▼
         ┌──────────────────────────────────────┐
         │  "CET1 is 14.83%. Data is active,    │
         │   owned by Treasury Risk Team,        │
         │   refreshed within 5 days of QE."    │
         └──────────────────────────────────────┘
```

---

### Example 5: ODPS Data Product (2.0)

```
┌──────────────────────────────────────────────────────┐
│              ODPS Product Definition (2.0)           │
│  ┌──────────────┐  ┌───────────┐  ┌───────────────┐  │
│  │    product   │  │ inputPorts│  │ outputPorts   │  │
│  │  name, domain│  │  source   │  │ DuckDB table  │  │
│  │  owner, SLA  │  │  cadence  │  │ + columns     │  │
│  └──────────────┘  └───────────┘  └───────────────┘  │
│  ┌──────────────┐  ┌───────────┐  ┌───────────────┐  │
│  │   useCases   │  │  quality  │  │    terms      │  │
│  │ approved Q's │  │  checks   │  │ usage/pricing │  │
│  └──────────────┘  └───────────┘  └───────────────┘  │
└──────────────────────────┬───────────────────────────┘
                           │  product-aware tool description
                           ▼
            ┌──────────────────────────┐
            │        LLM Agent         │
            │ (data + product + use    │
            │  case questions)         │
            └──────────┬───────────────┘
                       │  generates SQL
                       ▼
            ┌──────────────────┐
            │     DuckDB       │
            └──────────┬───────┘
                       ▼
            ┌──────────────────────────────────────┐
            │  "Goldman Sachs exposure: $790M.      │
            │   3 trades settle within 30 days.     │
            │   Data owned by Trade Finance Risk,   │
            │   updated T+1 by 08:00 GMT."          │
            └──────────────────────────────────────┘
```

**Key difference from Example 4:** ODCS governs a table. ODPS governs a business capability — the agent understands what problem the data product is built to solve, for whom, and under what SLA.

---

## 📚 Glossary

| Term | Definition |
|------|-----------|
| **AI Agent** | An autonomous system that understands natural language and takes actions (writing SQL, querying data, reasoning) to find answers. |
| **Context Engineering (CE)** | The discipline of designing, structuring, and governing the business context delivered to the LLM — at the right time and in the right format. |
| **Data Contract** | A file that documents what a dataset means, who owns it, SLAs, freshness, and lineage. Bridges semantic and technical layers. |
| **ODCS** | Open Data Contract Standard (Bitol/ACRYL). Formal spec for data contracts — schema, quality, SLAs, ownership, usage terms. |
| **ODPS** | Open Data Product Standard. Formal spec for data products — input/output ports, use cases, SLAs, pricing, governance. Think OpenAPI for data products. |
| **Data Product** | A governed, reusable business capability that exposes data through defined interfaces with ownership, SLAs, and quality guarantees. |
| **Semantic Layer** | A governed abstraction over raw data that defines what metrics and dimensions mean in business terms. |
| **SLayer** | Open-source semantic layer (motley-slayer). Compiles business metric queries into SQL via REST/MCP API. |
| **DuckDB** | In-process analytical SQL database. Used across all demos for fast, local query execution. |
| **Ollama** | Local LLM inference engine. Runs models like qwen2.5 on your machine without cloud APIs. |
| **MCP** | Model Context Protocol. Open standard for agents to discover and query semantic models and tools. |
| **LLM** | Large Language Model (Claude, GPT-4, Qwen). Powers the agent's reasoning and language understanding. |
| **YAML** | Human-readable data format. Used for data contracts and configuration. |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

```
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/amitnoida/
# ─────────────────────────────────────────────────────
```
