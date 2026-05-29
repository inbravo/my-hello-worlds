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

| Part | Requires | Scored as |
|---|---|---|
| CET1 ratio value | Data (DuckDB) | `"14.83"` verbatim in answer |
| Regulation cited (Basel III Art. 92) | OWL/SKOS ontology | `"Article 92"` or `"Art. 92"` — only in the TTL file |
| Owner: Treasury Risk Team | ODCS contract | Exact string `"Treasury Risk Team"` — only in the ODCS YAML |
| Freshness SLA (5 business days) | ODCS contract | `"5 business days"` or `"P5D"` — only in the ODCS YAML |
| Negative headroom → Art. 141 | OWL/SKOS ontology | `"141"` or `"dividend"` / `"buyback"` |

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

  Criterion                               Baseline  + YAML  + ODCS  + Ontology  Full Stack
  ──────────────────────────────────────────────────────────────────────────────────────────
  CET1 ratio value (14.83%)                 ✅        ✅      ✅       ✅          ✅
  Regulation cited (Basel III Art. 92)      ❌        ❌      ❌       ✅          ✅
  Owner: Treasury Risk Team                 ❌        ❌      ✅       ✅          ✅
  Freshness SLA (5 business days)           ❌        ❌      ✅       ✅          ✅
  Negative headroom → Art. 141              ❌        ❌      ❌       ❌          ✅
  ──────────────────────────────────────────────────────────────────────────────────────────
  TOTAL                                    1/5       1/5     2/5      4/5         5/5
```

> **Why Agents 1 & 2 score 1/5 and not higher:** The scoring rubric deliberately uses
> exact strings from the context files — "Treasury Risk Team" from the ODCS contract,
> "5 business days" from the ODCS freshness SLA, "Article 141" from the OWL ontology.
> A model with general Basel III knowledge cannot fake these without the actual context.

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
  (1/5)        (1/5)       (2/5)      (4/5)           (5/5)
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

```bash
(.venv) inbravo@IMUL-ML0515 code % python run_comparison.py

▶ Running Agent 1 — Baseline (schema only) ...
  Score: 1/5

▶ Running Agent 2 — + YAML Data Contract ...
  Score: 1/5

▶ Running Agent 3 — + ODCS Governance Contract ...
  Score: 2/5

▶ Running Agent 4 — + OWL/SKOS Domain Ontology ...
  Score: 4/5

▶ Running Agent 5 — Full Stack (all layers) ...
  Score: 5/5

════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
  CONTEXT ENGINEERING — FULL STACK COMPARISON
  Q: What is our current CET1 ratio, how does it compare to the Basel III minimum requirement, ...
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════

  ── Agent 1 — Baseline (schema only)  [1/5] ──
     Our current CET1 ratio as of 2026-03-31 is 14.83%. This exceeds the Basel III minimum requirement of
     4.5% for Common Equity Tier 1 (CET1) capital ratio.  The data is owned by BANK_HOLDCO and was last
     certified on 2026-03-31.  If our buffer headroom turns negative, it means that the additional buffer
     capital required under the countercyclical capital buffer or the planned systemic risk buffer would
     not be met. This could indicate potential vulnerabilities in the bank's risk management framework
     and may necessitate corrective actions to rebuild the buffer or address underlying risks as per
     Basel
     [... truncated]

  ── Agent 2 — + YAML Data Contract  [1/5] ──
     Our current CET1 ratio as of the latest reporting date is 14.83%. This exceeds the minimum Basel III
     Common Equity Tier 1 (CET1) capital requirement of 4.5%, indicating a strong regulatory buffer
     relative to requirements.  The entity "BANK_HOLDCO" owns this data. The table housing this
     information, `capital_position`, is refreshed quarterly and sourced from the core banking system via
     a bootstrapping script.  If our buffer headroom turns negative, it means that the combined buffer
     requirement (CCB + G-SII + countercyclical) becomes larger than the CET1 capital held by the entity.
     While there a
     [... truncated]

  ── Agent 3 — + ODCS Governance Contract  [2/5] ──
     Based on the most recent data available (as of March 31, 2026):  - Our current CET1 ratio is 14.83%.
     The Basel III minimum requirement for the CET1 ratio is 4.5% under Pillar 1 of the Capital Adequacy
     Regulation.  ### Ownership and Certification - **Owner**: Treasury Risk Team. - The document does
     not provide specific details on when it was last certified, but according to the service level
     agreements (SLAs) outlined in the governance contract:   - Support SLA states that the Treasury Risk
     Team responds within one business day from receipt of request or issue.   - However, for more
     precise ce
     [... truncated]

  ── Agent 4 — + OWL/SKOS Domain Ontology  [4/5] ──
     Based on the data from the `capital_position` table as of 2026-03-31:  - The Current CET1 ratio is
     **14.83%**. - This compared to the Basel III minimum requirement, which is **4.5%**, our bank’s
     current CET1 ratio significantly exceeds the required threshold by a margin of **(14.83 - 4.5) =
     10.33 percentage points**.  The data for BANK_HOLDCO was last certified on 2026-03-31, which aligns
     with the internal regulatory schedule. The ownership of this data is under the Treasury Risk Team as
     stated in the ODCS contract.  Regarding service levels and certifications, according to the provided
     govern
     [... truncated]

  ── Agent 5 — Full Stack (all layers)  [5/5] ──
     Based on the metric query result, the current CET1 ratio for each quarter-end date is as follows:  -
     **2025-12-31**: 14.66% - **2025-09-30**: 14.39% - **2026-03-31**: 14.83%  The specific Basel III
     article that governs the CET1 ratio minimum is [Basel III Article
     92(1)(a)](https://www.bankingregulation.org/basel-iii/regulatory-capital/tier-1-capital/#cet1).
     According to this article, the minimum required CET1 ratio is 4.5%.  The exact data owner name from
     the ODCS contract is **Treasury Risk Team**.  The exact freshness SLA (freshness threshold) from the
     ODCS contract specifies that the data m
     [... truncated]

════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
  SCORING — which parts each context layer answered
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
  Criterion                               Baseline (schema only)        + YAML Data Contract          + ODCS Governance Contract    + OWL/SKOS Domain Ontology    Full Stack (all layers)     
  --------------------------------------  ----------------------------  ----------------------------  ----------------------------  ----------------------------  ----------------------------
  CET1 ratio value (14.83%)               ✅                             ✅                             ✅                             ✅                             ✅                           
  Regulation cited (Basel III Art. 92)    ❌                             ❌                             ❌                             ❌                             ✅                           
  Owner: Treasury Risk Team               ❌                             ❌                             ✅                             ✅                             ✅                           
  Freshness SLA (5 business days)         ❌                             ❌                             ❌                             ✅                             ✅                           
  Negative headroom → Art. 141            ❌                             ❌                             ❌                             ✅                             ✅                           
  --------------------------------------  ----------------------------  ----------------------------  ----------------------------  ----------------------------  ----------------------------
  TOTAL                                   1/5                           1/5                           2/5                           4/5                           5/5                         
════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
```
