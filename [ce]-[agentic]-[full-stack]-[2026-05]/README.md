# Context Engineering — Full Stack Comparison

**Example 10 of the CE series — the capstone.** One question. Five agents.
Increasing context richness. A scored comparison table that makes the CE
progression tangible.

```
code/bootstrap_full_stack.py   — validate prerequisites, seed local DB
code/run_comparison.py         — orchestrate all 5 agents, print scored table
```

---

## The Question

```
What is our current CET1 ratio, how does it compare to the Basel III
minimum requirement, who owns this data and when was it last certified,
and what happens if our buffer headroom turns negative?
```

This question has **five distinct parts**. Each requires a different
semantic layer to answer correctly:

| Part | Requires |
|---|---|
| CET1 ratio value | Data (DuckDB) |
| Basel III minimum (4.5%) | Domain ontology (OWL/SKOS) |
| Data owner | Governance contract (ODCS) |
| Last certified | Governance contract (ODCS) |
| Negative headroom consequence | Domain ontology (Article 141) |

No single earlier example answers all five.

---

## The Five Agents

| Agent | Context layers | Expected score |
|---|---|---|
| 1 — Baseline | Schema only (table + column names) | 1 / 5 |
| 2 — + YAML Contract | Column descriptions + table purpose | 1 / 5 |
| 3 — + ODCS Contract | + Ownership, certification date, SLA | 3 / 5 |
| 4 — + OWL/SKOS Ontology | + Basel III min, concept hierarchy, Article 141 | 4 / 5 |
| 5 — Full Stack | All layers + MetricFlow governed metrics | 5 / 5 |

---

## Prerequisites

This demo **pulls context files from sibling examples** — no duplication.
Run these bootstraps first if you haven't already:

```bash
# Example 1 — seeds the YAML contract (capital_risk.yaml)
cd ../[ce]-[hello-world]-[2026-05]/code && python3 bootstrap.py

# Example 4 — seeds the ODCS contract (capital_risk_odcs.yaml)
cd ../[ce]-[odcs]-[bfsi]-[2026-05]/code && python3 bootstrap_odcs.py

# Example 8 — ontology is checked in, no bootstrap needed
# ../[ce]-[ontology]-[bfsi]-[2026-05]/ontology/bfsi_capital.ttl ✅

# Example 9 — seeds the dbt project + MetricFlow DB
cd ../[ce]-[metrics]-[bfsi]-[2026-05]/code && python3 bootstrap_metrics.py
```

---

## Quick Start

**Step 1 — Install dependencies:**
```bash
pip install duckdb pyyaml rdflib openai structlog
ollama pull qwen2.5
```

**Step 2 — Bootstrap:**
```bash
cd code/
python3 bootstrap_full_stack.py
```

```
[1/2] Checking sibling example prerequisites ...
  ✅  YAML contract
  ✅  ODCS contract
  ✅  OWL ontology
  ✅  dbt project
  ✅  MetricFlow DB

[2/2] Seeding capital_bfsi.duckdb ...
  Seeded 3 rows → capital_position
```

**Step 3 — Run the comparison:**
```bash
python3 run_comparison.py
```

---

## Expected Output

```
▶ Running Agent 1 — Baseline (schema only) ...        Score: 1/5
▶ Running Agent 2 — + YAML Data Contract ...          Score: 1/5
▶ Running Agent 3 — + ODCS Governance Contract ...    Score: 3/5
▶ Running Agent 4 — + OWL/SKOS Domain Ontology ...   Score: 4/5
▶ Running Agent 5 — Full Stack (all layers) ...       Score: 5/5

══════════════════════════════════════════════════════════
  SCORING — Which parts of the question each layer answered
══════════════════════════════════════════════════════════
  Criterion                    Agent 1  Agent 2  Agent 3  Agent 4  Agent 5
  ─────────────────────────────────────────────────────────────────────────
  CET1 ratio value (14.83%)      ✅       ✅       ✅       ✅       ✅
  Basel III minimum (4.5%)       ❌       ❌       ❌       ✅       ✅
  Data owner identified          ❌       ❌       ✅       ✅       ✅
  Certification / freshness      ❌       ❌       ✅       ✅       ✅
  Negative headroom consequence  ❌       ❌       ❌       ❌       ✅
  ─────────────────────────────────────────────────────────────────────────
  TOTAL                         1/5      1/5      3/5      4/5      5/5
══════════════════════════════════════════════════════════
```

---

## Architecture

```
                    ┌──────────────────────────────┐
                    │  The Same Question           │
                    └──────────┬───────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
    ┌─────▼──────┐      ┌──────▼─────┐      ┌──────▼──────┐
    │  Agent 1   │      │  Agent 3   │      │  Agent 5    │
    │  Schema    │      │  + ODCS    │      │ Full Stack  │
    │  only      │      │  Contract  │      │ All layers  │
    └─────┬──────┘      └──────┬─────┘      └──────┬──────┘
          │                    │                    │
        1/5                  3/5                  5/5
          │                    │                    │
    ┌─────▼────────────────────▼────────────────────▼──────┐
    │                      DuckDB                          │
    │              capital_position table                  │
    └──────────────────────────────────────────────────────┘

  Context layers added progressively:
  ① Schema ──► ② YAML ──► ③ ODCS ──► ④ Ontology ──► ⑤ + Metrics
  (1/5)        (1/5)       (3/5)      (4/5)           (5/5)
```

---

## What this proves

The data never changes. The model never changes. The only variable is
**how much business context the agent has**. The scored table makes this
visible — Context Engineering is not abstract. It has a measurable,
demonstrable effect on answer quality.

---

## CE Series

| Example | Semantic component | What the agent understands |
|---------|-------------------|-----------------------------|
| [Example 1](../[ce]-[hello-world]-[2026-05]/README.md) | Hand-written YAML contract | Schema — column names and types |
| [Example 2](../[ce]-[slayer]-[hello-world]-[2026-05]/README.md) | Semantic model — SLayer REST (generic) | Measures and dimensions |
| [Example 3](../[ce]-[slayer]-[bfsi]-[2026-05]/README.md) | Semantic model — SLayer REST (BFSI) | Business metric definitions |
| [Example 4](../[ce]-[odcs]-[bfsi]-[2026-05]/README.md) | Formal ODCS contract (Bitol 0.9.3) | Ownership, quality, SLAs |
| [Example 5](../[ce]-[odps]-[trade]-[2026-05]/README.md) | Data product (ODPS 2.0) | Ports, use cases, governance |
| [Example 6](../[ce]-[slayer]-[mcp]-[2026-05]/README.md) | Semantic layer via MCP (generic) | Zero-code semantic queries |
| [Example 7](../[ce]-[slayer]-[mcp]-[bfsi]-[2026-05]/README.md) | Semantic layer via MCP (BFSI) | Capital adequacy via MCP |
| [Example 8](../[ce]-[ontology]-[bfsi]-[2026-05]/README.md) | OWL/SKOS domain ontology | Concept hierarchy, Basel III articles |
| [Example 9](../[ce]-[metrics]-[bfsi]-[2026-05]/README.md) | dbt Metric Layer (MetricFlow) | Named governed metrics |
| **Example 10 (this)** | **Full stack comparison** | **Everything — scored side by side** |

---

## Stack

| Layer | Component |
|---|---|
| Baseline context | Table schema (column names only) |
| Data contract | YAML (`capital_risk.yaml` from Example 1) |
| Governance | ODCS 0.9.3 (`capital_risk_odcs.yaml` from Example 4) |
| Domain ontology | OWL/SKOS Turtle (`bfsi_capital.ttl` from Example 8) |
| Metric layer | dbt MetricFlow (`schema.yml` from Example 9) |
| LLM | Ollama qwen2.5 |
| Data | DuckDB (`capital_bfsi.duckdb`) |
| Scoring | Keyword rubric — 5 criteria, 0/1 per agent |
