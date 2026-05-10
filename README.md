# My Hello Worlds: My first interaction to a technical solution
This repo contains various "Hello World" catagory of applications

## Semantics and Context Engineering
If you have understood the purpose of the Semantic layer, Context Engineering follows naturally — it is the discipline of designing, structuring, and governing the business context delivered to the LLM, at the right time and in the right format, so it reasons and acts correctly on your data. CE is not a one-time activity. The outcome it continuously produces and maintains is the semantic layer itself — a living, structured representation of the business meaning of customer data. Put simply:— good Context Engineering produces good semantics. 

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

**How they relate**

- A **data contract** says: *"this table exists, has these columns, owned by this team, refreshed daily"*
- An **ontology** says: *"CET1 Capital is a subclass of Regulatory Capital, which is governed by Basel III"*
- A **semantic model** says: *"cet1_ratio_pct = CET1 Capital ÷ RWA × 100, display as percentage"*
- A **knowledge graph** says: *"BANK_HOLDCO → holds → BANK_SUBSIDIARY → reports → CET1 position"*
- A **metric layer** says: *"CET1 Headroom = cet1_ratio_pct − combined_buffer, flagged if < 1pp"*

---

## There are two Hello World Examples on Context Engineering

#### **Example 1 using Data Contract-based Semantic Layer (Component 1)**
  A small but complete demo that gives you a basic idea of Context Engineering. This demo makes the concept tangible in under five minutes. I have tried to keep it simple for easy understanding.
  For those who are already ahead in CE, this demo won’t matter much, but for anybody still in the initial learning phase, this example will help you understand why CE matters

  What it shows
  - Clients have "AI agents." Context engineering is the missing piece — it's the discipline of giving the LLM precisely the right context, in a structured and governed way, so it acts correctly on your data.
  - A bank's capital reporting team gets asked the same questions every quarter: What's our current CET1 ratio? How much buffer headroom do we have?* The data is in a table. The friction is in writing and maintaining SQL against a schema that changes with every regulatory update.
  - This demo replaces that friction. An AI agent reads a data contract — a YAML file that describes what the data means in plain English — then writes its own SQL, queries a DuckDB database, and returns a clear answer. No hardcoded prompts. No vector store. No custom fine-tuning. Just a structured contract and a two-turn agent loop.

Two ways to run it: Claude (via the Anthropic API) or any local model via Ollama. Get it running in four commands
1.	git clone https://github.com/inbravo/my-hello-worlds
2.	cd my-hello-worlds/\[ce\]-\[hello-world\]-\[2026-05\]/code
3.	pip install duckdb structlog pyyaml numpy pandas anthropic 
4.	python bootstrap.py && python agent.py


#### **Example 2 using MCP-compatible Semantic Layer (Component 3)**
  A Second Example that brings the CE example closer to a real production pattern. Instead of a YAML data contract, it uses a proper running semantic model ( using slayer ) that the agent discovers and queries via the MCP/REST API. The agent never writes SQL; the   semantic layer compiles it. The same semantic layer can be wired directly into any agent. A governed, schema-aware layer that sits between the agent and the data, translating the business story into agentic language. 

Full walkthrough in the README, including the Ollama or Anthropic API options. To run the second demo fully local:
1.	git clone https://github.com/inbravo/my-hello-worlds
2.	uvx --from 'motley-slayer[all]' slayer serve --demo
3.	ollama serve && ollama pull qwen2.5
4.	cd my-hello-worlds/[ce]-[slayer]-[bfsi]-[2026-05]/code
5.	pip install openai requests duckdb structlog ‘motley-slayer[all]’
6.	python bootstrap_bfsi.py && python setup_bfsi.py && python agent_slayer_bfsi_ollama.py


