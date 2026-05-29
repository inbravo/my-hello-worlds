# Context Engineering — OWL/SKOS Ontology BFSI Demo

**Example 8 of the CE series.** The same Basel III/IV capital adequacy
data from Examples 3 and 7 — now enriched with a formal **OWL/SKOS
domain ontology** parsed at runtime. The agent doesn't just know the
schema. It knows the domain.

```
ontology/bfsi_capital.ttl        — OWL/SKOS ontology in Turtle format
code/bootstrap_ontology.py       — seed capital_bfsi.duckdb
code/agent_ontology_ollama.py    — Ollama agent (qwen2.5)
code/agent_ontology.py           — Anthropic Claude agent
```

---

## What changes from previous examples

| | Examples 1–7 | Example 8 — Ontology |
|---|---|---|
| Context source | YAML / data contract / ODCS / ODPS / SLayer model | OWL/SKOS Turtle ontology |
| Parsed by | Hand-crafted / SLayer | `rdflib` — standard RDF/OWL library |
| Concept hierarchy | Not modelled | `CET1Capital ⊂ Tier1Capital ⊂ RegulatoryCapital ⊂ Capital` |
| Formulas | In YAML or schema | `bfsi:formula` OWL property on each concept |
| Regulatory references | In YAML prose | `bfsi:basedOnArticle`, `bfsi:governedBy` triples |
| Minimum requirements | Hard-coded | `bfsi:minimumRequirement` on each ratio class |
| Column mapping | Implicit (schema names) | `bfsi:columnMapping` OBML-style annotation |
| Domain questions answered? | No | **Yes** — from ontology, without querying the DB |

**The key shift:** Previous examples made the agent schema-aware. This
example makes it **domain-aware** — it understands what the data *means*
in the context of banking regulation.

---

## What is an Ontology?

An ontology is a formal, machine-readable representation of knowledge in
a domain — the concepts that exist, how they relate to each other, and
what properties they have.

| Format | What it adds |
|---|---|
| **OWL** (Web Ontology Language) | Class hierarchy, logical relationships, property definitions |
| **SKOS** (Simple Knowledge Organisation System) | Human-readable labels, definitions, alternative terms, broader/narrower concept links |
| **Turtle (.ttl)** | Compact, readable serialisation of RDF triples — the format used in this demo |
| **OBML annotations** | Map database columns to ontology concepts — the `bfsi:columnMapping` triples |

---

## The Ontology — `bfsi_capital.ttl`

### Concept hierarchy (OWL `subClassOf`)

```
Capital
└── RegulatoryCapital               (governed by Basel III)
    ├── Tier1Capital                (min 6.0% of RWA)
    │   ├── CET1Capital ★           (min 4.5% · DB: cet1_capital_mm)
    │   └── AT1Capital
    └── Tier2Capital

RiskWeightedAssets ★               (DB: rwa_mm)

CapitalRatio
└── CET1Ratio ★                    (formula: CET1 ÷ RWA × 100 · DB: cet1_ratio_pct)

CapitalBuffer
└── CombinedBuffer ★               (DB: combined_buffer)
    ├── CapitalConservationBuffer   (fixed 2.5%)
    ├── CountercyclicalBuffer       (0–2.5%, set by regulator)
    └── SystemicRiskBuffer          (G-SIB / O-SII surcharge)

BufferHeadroom                     (formula: CET1Ratio − CombinedBuffer)
```

★ = has a `bfsi:columnMapping` to a DB column (OBML-style annotation)

### What rdflib extracts at runtime

For each concept, the agent's tool description includes:
- Full OWL definition and SKOS label
- Parent class (`subClassOf` chain)
- Formula (where applicable)
- Minimum regulatory requirement
- Basel III article reference
- DB column mapping

---

## Quick Start

**Step 1 — Install dependencies:**
```bash
cd code/
pip install duckdb rdflib openai structlog anthropic
ollama pull qwen2.5
```

**Step 2 — Bootstrap the database (once):**
```bash
python bootstrap_ontology.py
```

```
Created : capital_bfsi.duckdb
Path    : /your/path/capital_bfsi.duckdb
Seeded  : 3 rows → capital_position

Columns:
  reporting_date  → bfsi:col_reporting_date
  entity          → bfsi:col_entity
  cet1_capital_mm → bfsi:CET1Capital
  rwa_mm          → bfsi:RiskWeightedAssets
  cet1_ratio_pct  → bfsi:CET1Ratio
  combined_buffer → bfsi:CombinedBuffer
```

**Step 3 — Run the agent:**
```bash
python agent_ontology_ollama.py
```

---

## Sample Questions

### Data questions (queries DuckDB):
```
What is our current CET1 ratio?
How much buffer headroom do we have as of Q1 2026?
Show the CET1 ratio trend across all three quarters.
What is our risk-weighted asset position as of the latest reporting date?
```

### Domain knowledge questions (answered from ontology, no DB query needed):
```
Is CET1 Capital a subset of Tier 1 Capital?
What is the formula for the CET1 ratio?
What is the Basel III minimum CET1 ratio requirement?
Which regulation governs the combined buffer requirement?
What happens if our buffer headroom turns negative?
What is the difference between Tier 1 and Tier 2 capital?
```

### Mixed questions (ontology context + DB data):
```
What is our current CET1 ratio and how does it compare to the Basel III minimum?
Are we above the combined buffer requirement? What is the headroom in percentage points?
How has our CET1 capital grown since September 2025, and what does Basel III say about CET1?
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│              OWL/SKOS Ontology (Turtle)                  │
│  bfsi_capital.ttl                                        │
│  ┌──────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │  OWL Classes │  │ SKOS Labels │  │ OBML Mappings   │  │
│  │  subClassOf  │  │ definitions │  │ col → concept   │  │
│  │  hierarchy   │  │ alt labels  │  │ formula, minReq │  │
│  └──────────────┘  └─────────────┘  └─────────────────┘  │
└──────────────────────────┬───────────────────────────────┘
                           │  rdflib parses at startup
                           ▼
         ┌──────────────────────────────────┐
         │   Tool Description (built once)  │
         │   Concept hierarchy + defs       │
         │   Formulas + Basel III articles  │
         │   Column → concept mappings      │
         └──────────────────┬───────────────┘
                            │  injected into tool
                            ▼
         ┌──────────────────────────────────┐
         │           LLM Agent              │
         │   (Ollama qwen2.5 / Claude)      │
         │   Understands domain, not just   │
         │   schema — reasons about Basel   │
         │   III rules, not just column names│
         └──────────┬───────────────────────┘
                    │  generates SQL (data Qs)
                    │  answers directly (domain Qs)
                    ▼
         ┌──────────────────────────────────┐
         │   DuckDB — capital_position      │
         │   3 quarters of capital data     │
         └──────────────────────────────────┘
```

---

## CE Series

| Example | Semantic component | What the agent understands |
|---------|-------------------|-----------------------------|
| [Example 1](../[ce]-[hello-world]-[2026-05]/README.md) | YAML contract | Column names and types |
| [Example 2](../[ce]-[slayer]-[hello-world]-[2026-05]/README.md) | SLayer (generic) | Measures and dimensions |
| [Example 3](../[ce]-[slayer]-[bfsi]-[2026-05]/README.md) | SLayer (BFSI) | Business metric definitions |
| [Example 4](../[ce]-[odcs]-[bfsi]-[2026-05]/README.md) | ODCS contract | Ownership, quality, SLAs |
| [Example 5](../[ce]-[odps]-[trade]-[2026-05]/README.md) | ODPS data product | Ports, use cases, governance |
| [Example 6](../[ce]-[slayer]-[mcp]-[2026-05]/README.md) | SLayer MCP (generic) | Semantic layer via MCP |
| [Example 7](../[ce]-[slayer]-[mcp]-[bfsi]-[2026-05]/README.md) | SLayer MCP (BFSI) | Capital adequacy via MCP |
| **Example 8 (this)** | **OWL/SKOS Ontology** | **Domain concept hierarchy, Basel III regulation, formulas** |
| Example 9 | Metric layer | Coming |
| Example 10 | Full stack comparison | Coming |

---

## Stack

| Layer | Component |
|---|---|
| Ontology | OWL/SKOS Turtle (`bfsi_capital.ttl`) |
| RDF parser | `rdflib` |
| LLM (local) | Ollama qwen2.5 |
| LLM (cloud) | Anthropic Claude |
| Data | DuckDB (`capital_bfsi.duckdb`) |
| Domain | BFSI — Basel III/IV Capital Adequacy |
