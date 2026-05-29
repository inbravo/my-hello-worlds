# Hello Worlds: First Contact with a Technology
Minimal, working examples across the agentic AI stack — MCP servers, agent frameworks, context pipelines, and the scaffolding nobody documents properly.

---

## Repository Structure

This repository contains **ten examples** organized in separate folders, each introducing a new semantic component in the Context Engineering ladder:

### 📂 Directory Listing

| # | Folder | Semantic Component | Description |
|---|---|---|---|
| 1 | [[ce]-[hello-world]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bhello-world%5D-%5B2026-05%5D) | Hand-written YAML contract | CE baseline — agent reads a data contract and writes its own SQL |
| 2 | [[ce]-[slayer]-[hello-world]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bslayer%5D-%5Bhello-world%5D-%5B2026-05%5D) | Semantic model — generic | Agent queries a live semantic layer via REST. No SQL written by the agent |
| 3 | [[ce]-[slayer]-[bfsi]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bslayer%5D-%5Bbfsi%5D-%5B2026-05%5D) | Semantic model — BFSI domain | Real datasource registered into a semantic layer. BFSI capital adequacy use case |
| 4 | [[ce]-[odcs]-[bfsi]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bodcs%5D-%5Bbfsi%5D-%5B2026-05%5D) | Formal ODCS contract (Bitol 0.9.3) | Upgrades the YAML contract to a governed standard — adds ownership, quality checks, SLA, and freshness metadata |
| 5 | [[ce]-[odps]-[trade]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bodps%5D-%5Btrade%5D-%5B2026-05%5D) | Data product (ODPS 2.0) | Steps up from table governance to product governance — ports, use cases, SLAs. New domain: Trade Finance |
| 6 | [[ce]-[slayer]-[mcp]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bslayer%5D-%5Bmcp%5D-%5B2026-05%5D) | Semantic layer via MCP — generic | Transport upgrade — same semantic layer, now accessed via MCP stdio. Claude Desktop is the agent. No Python |
| 7 | [[ce]-[slayer]-[mcp]-[bfsi]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bslayer%5D-%5Bmcp%5D-%5Bbfsi%5D-%5B2026-05%5D) | Semantic layer via MCP — BFSI | Same Basel III/IV capital adequacy data as Example 3, now over MCP. Zero agent code |
| 8 | [[ce]-[ontology]-[bfsi]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bontology%5D-%5Bbfsi%5D-%5B2026-05%5D) | OWL/SKOS domain ontology | 15-class BFSI ontology parsed by rdflib. Agent understands concept hierarchy, Basel III articles, and formulas — domain-aware, not just schema-aware |
| 9 | [[ce]-[metrics]-[bfsi]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bmetrics%5D-%5Bbfsi%5D-%5B2026-05%5D) | dbt Metric Layer (MetricFlow) | 5 named governed metrics — cet1_ratio, buffer_headroom, rwa, cet1_capital, combined_buffer. Agent calls mf query, never writes SQL |
| 10 | [[ce]-[agentic]-[full-stack]-[2026-05]](https://github.com/inbravo/my-hello-worlds/tree/main/%5Bce%5D-%5Bagentic%5D-%5Bfull-stack%5D-%5B2026-05%5D) | Full stack comparison | One question through all 9 context layers. Scored side-by-side table proves CE has a measurable effect on answer quality |

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

### Example 6: Semantic Layer via MCP — Generic (Jaffle Shop)

**Semantic component:** Semantic Model (Component 3) via MCP transport

**What it shows:**
- The same semantic layer from Examples 2 & 3 — but the transport changes from REST to **MCP stdio**. No Python agent code. Claude Desktop connects directly and auto-discovers the Jaffle Shop model.
- Demonstrates that the semantic context is transport-independent. You switch from REST to MCP; the business definitions stay the same.

**Quick Start:**
```bash
# No Python agent needed — Claude Desktop IS the agent
# Add to Claude Desktop config:
{
  "mcpServers": {
    "slayer": {
      "command": "uvx",
      "args": ["--from", "motley-slayer[all]", "slayer", "mcp", "--demo"]
    }
  }
}
# Restart Claude Desktop, then ask: "What are total orders by store?"
```

**Options:** Claude Desktop (Jaffle Shop demo data) or Claude Code CLI (`claude mcp add slayer -- uvx --from 'motley-slayer[all]' slayer mcp --demo`)

---

### Example 7: Semantic Layer via MCP — BFSI (Capital Adequacy)

**Semantic component:** Semantic Model (Component 3) via MCP — BFSI domain

**What it shows:**
- The same Basel III/IV capital adequacy data from Example 3 — but accessed via MCP, not the REST API.
- No Python agent. No tool definitions. Claude Desktop is the agent. SLayer MCP auto-discovers the `capital_position` model and Claude answers CET1 and buffer headroom questions directly.
- The transport switches from HTTP REST to MCP stdio. The semantic context — same data, same model, same business meaning — does not change.

**Quick Start:**
```bash
cd my-hello-worlds/[ce]-[slayer]-[mcp]-[bfsi]-[2026-05]/code
pip install requests duckdb
python bootstrap_mcp_bfsi.py
uvx --from 'motley-slayer[all]' slayer serve   # register only
python setup_mcp_bfsi.py                        # then Ctrl+C to stop serve
# Add config/claude_desktop_bfsi.json to Claude Desktop, restart, and ask:
# "What is our current CET1 ratio and buffer headroom?"
```

**Also works in Claude Code:**
```bash
claude mcp add slayer -- uvx --from 'motley-slayer[all]' slayer mcp
```

---

### Example 8: OWL/SKOS Domain Ontology — BFSI

**Semantic component:** Ontology (Component 2 — OWL/SKOS + OBML-style annotations)

**What it shows:**
- A 15-class BFSI capital adequacy ontology in Turtle format, parsed at runtime by `rdflib`. The agent's tool description is built dynamically from the ontology — not hand-crafted.
- The agent understands the full concept hierarchy (`CET1Capital ⊂ Tier1Capital ⊂ RegulatoryCapital`), Basel III article references, formulas, minimum requirements, and OBML-style column-to-concept mappings.
- Previous examples made the agent schema-aware. This makes it **domain-aware** — it can answer regulatory and conceptual questions without querying the database at all.

**Quick Start:**
```bash
cd my-hello-worlds/[ce]-[ontology]-[bfsi]-[2026-05]/code
pip install duckdb rdflib openai structlog
ollama serve && ollama pull qwen2.5
python3 bootstrap_ontology.py && python3 agent_ontology_ollama.py
```

**Try domain questions:**
```
python3 agent_ontology_ollama.py "Is CET1 Capital a subset of Tier 1 Capital?"
python3 agent_ontology_ollama.py "What regulation governs the combined buffer requirement?"
python3 agent_ontology_ollama.py "What is our CET1 ratio vs the Basel III minimum?"
```

**Options:** Anthropic API (`agent_ontology.py`) or Ollama (`agent_ontology_ollama.py`)

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
| 6 | Example 6 — SLayer MCP (Jaffle Shop) | How MCP replaces the REST agent loop entirely. Claude Desktop becomes the agent. |
| 7 | Example 7 — SLayer MCP (BFSI) | Same semantic model, same data — zero Python. MCP transport changes everything about the client, nothing about the semantics. |
| 8 | Example 8 — OWL/SKOS Ontology | How a formal domain ontology makes the agent domain-aware — it understands Basel III concept hierarchy, formulas, and regulatory articles, not just column names. |
| 9 | Example 9 — dbt Metric Layer | How named, governed business metrics (MetricFlow) replace raw SQL — the metric layer enforces the formula, the agent just asks by name. |
| 10 | Example 10 — Full Stack Comparison | One question. Five agents. Scored table. CE is not abstract — it has a measurable, demonstrable effect on answer quality. |
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

### Examples 6 & 7: Semantic Layer via MCP

```
┌──────────────────────────────────────────┐
│           Claude Desktop / Claude Code   │
│  (LLM + MCP client — no Python needed)  │
└──────────────────┬───────────────────────┘
                   │  MCP stdio
                   │  auto-discovers model
                   ▼
┌──────────────────────────────────────────┐
│        SLayer MCP Server                 │
│   uvx ... slayer mcp [--demo]            │
│                                          │
│   Reads: ~/.local/share/slayer           │
│   Finds: datasource + model              │
│   Exposes: model as MCP tools            │
└──────────────────┬───────────────────────┘
                   │  compiles SQL
                   ▼
┌──────────────────────────────────────────┐
│   DuckDB                                 │
│   (Jaffle Shop or capital_bfsi.duckdb)   │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  Answer in Claude Desktop chat           │
│  No Python. No agent loop. No tools.     │
└──────────────────────────────────────────┘
```

**How SLayer storage is shared:**
```
slayer serve  ──writes──►  ~/.local/share/slayer/  ◄──reads──  slayer mcp
```
Run `setup_mcp_bfsi.py` once against the REST server — the MCP server picks up the datasource automatically. No further config needed.

**Key difference from Examples 2 & 3:** REST requires a Python agent with an explicit tool loop. MCP exposes the same semantic model as native Claude tools — Claude Desktop calls them directly. Zero agent code.

---

### Example 8: OWL/SKOS Domain Ontology

```
┌──────────────────────────────────────────────────────┐
│           OWL/SKOS Ontology — bfsi_capital.ttl       │
│                                                      │
│  CET1Capital ⊂ Tier1Capital ⊂ RegulatoryCapital      │
│  Formula: CET1 ÷ RWA × 100                          │
│  Min requirement: 4.5% (Basel III Article 92)        │
│  DB column: cet1_ratio_pct  (OBML annotation)        │
└──────────────────────┬───────────────────────────────┘
                       │  rdflib parses at startup
                       ▼
       ┌───────────────────────────────────┐
       │   Tool Description (built once)   │
       │   15 concepts · regulations ·     │
       │   formulas · column mappings      │
       └──────────────────┬────────────────┘
                          │  injected into tool
                          ▼
       ┌───────────────────────────────────┐
       │          LLM Agent               │
       │  Domain-aware: knows Basel III    │
       │  hierarchy, not just schema       │
       └─────────┬─────────────┬──────────┘
                 │             │
         data Qs │    domain Qs│ (answered from
                 │             │  ontology, no DB)
                 ▼             ▼
       ┌──────────────┐   ┌──────────────────────────┐
       │    DuckDB    │   │  "CET1 ⊂ Tier1 ⊂         │
       │  capital_    │   │   RegulatoryCapital.      │
       │  position    │   │   Min 4.5% per Art. 92." │
       └──────────────┘   └──────────────────────────┘
```

**Key difference from Example 4 (ODCS):** ODCS adds governance metadata to a schema. An ontology encodes the domain knowledge itself — the agent knows *what* CET1 Capital *is*, not just that the column exists.

---

### Example 9: dbt Metric Layer — BFSI (MetricFlow)

**Semantic component:** Metric Layer (Component 5 — named, governed business metrics)

**What it shows:**
- Five Basel III metrics defined in MetricFlow YAML: `cet1_ratio`, `combined_buffer_requirement`, `cet1_capital`, `rwa`, and `buffer_headroom` (a derived metric: `cet1_ratio − combined_buffer_requirement`).
- The agent calls `mf query` via subprocess — it never writes SQL. MetricFlow compiles the SQL, enforces the formula, and returns typed results.
- Every consumer of `cet1_ratio` gets the same number from the same governed definition. One metric. One truth.

**Quick Start:**
```bash
pip install dbt-core dbt-duckdb dbt-metricflow openai structlog
ollama pull qwen2.5
cd my-hello-worlds/[ce]-[metrics]-[bfsi]-[2026-05]/code
python3 bootstrap_metrics.py   # dbt run + mf validate-configs
python3 agent_metrics_ollama.py
```

**Or query metrics directly from the CLI (no agent needed):**
```bash
cd my-hello-worlds/[ce]-[metrics]-[bfsi]-[2026-05]/dbt_project
mf query --metrics cet1_ratio,buffer_headroom --group-by metric_time__month
```

---

### Example 9: Architecture

```
┌─────────────────────────────────────────────────────┐
│           schema.yml — MetricFlow Catalogue         │
│  cet1_ratio      (simple · min 4.5% · Art. 92)     │
│  buffer_headroom (derived: cet1_ratio − buffer)     │
│  cet1_capital    (simple · Art. 26-50)              │
│  rwa             (simple · Basel III)               │
│  combined_buffer (simple · Art. 128-131)            │
└──────────────────────┬──────────────────────────────┘
                       │  read at startup → tool description
                       ▼
       ┌───────────────────────────────────┐
       │          LLM Agent               │
       │  Knows metric definitions,       │
       │  ownership, Basel III thresholds │
       └──────────────┬────────────────────┘
                      │  tool call: query_metric
                      │  {metrics: ["cet1_ratio","buffer_headroom"],
                      │   group_by: ["metric_time__month"]}
                      ▼
       ┌───────────────────────────────────┐
       │   mf query (subprocess)          │
       │   MetricFlow compiles SQL        │
       │   Runs against DuckDB            │
       └──────────────┬────────────────────┘
                      ▼
       metric_time__month  cet1_ratio  buffer_headroom
       2025-09-01          14.39        4.64
       2025-12-01          14.66        4.91
       2026-03-01          14.83        5.08
```

**Key difference from Example 8 (Ontology):** The ontology says what CET1 Ratio *is*. The metric layer governs how it is *computed and consumed* — MetricFlow enforces the formula for every consumer, not the agent or analyst.

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
| **Ontology** | A formal, machine-readable representation of domain knowledge — concepts, relationships, and properties. OWL and SKOS are the W3C standards for building ontologies. |
| **OWL** | Web Ontology Language. W3C standard for defining class hierarchies, logical relationships, and properties in machine-readable form. |
| **SKOS** | Simple Knowledge Organisation System. W3C standard for human-readable concept labels, definitions, and broader/narrower relationships. |
| **rdflib** | Python library for parsing and querying RDF/OWL/SKOS ontologies in Turtle (.ttl) and other RDF formats. |
| **OBML** | Ontology-Based Markup Language. Annotates data columns with ontology concept URIs, bridging the database schema and the domain model. |
| **Metric Layer** | A governed catalogue of named business metrics with defined formulas, owners, and thresholds — enforced for every consumer. Sits above the semantic layer. |
| **MetricFlow** | Open-source metric framework (Apache 2.0) that powers the dbt Semantic Layer. Compiles metric queries into SQL. CLI: `mf query`. |
| **dbt** | Data build tool. Transforms raw data into governed models and metrics. `dbt-duckdb` adapter enables fully local usage with DuckDB. |
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
