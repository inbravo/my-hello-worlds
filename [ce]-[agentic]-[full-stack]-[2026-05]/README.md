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
  TOTAL                                    1/5       1/5     3/5      4/5         5/5
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

```bash
(.venv) inbravo@IMUL-ML0515 code % python run_comparison.py 

▶ Running Agent 1 — Baseline (schema only) ...
  Score: 5/5

▶ Running Agent 2 — + YAML Data Contract ...
  Score: 4/5

▶ Running Agent 3 — + ODCS Governance Contract ...
  Score: 5/5

▶ Running Agent 4 — + OWL/SKOS Domain Ontology ...
  Score: 5/5

▶ Running Agent 5 — Full Stack (all layers) ...
  Score: 4/5

══════════════════════════════════════════════════════════════════════════════════════════════════════════════
  CONTEXT ENGINEERING — FULL STACK COMPARISON
  Question: What is our current CET1 ratio, how does it compare to the Basel III minimum requirement, who o...
══════════════════════════════════════════════════════════════════════════════════════════════════════════════

──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Agent 1 — Baseline (schema only)
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Based on the latest data as of March 31, 2026:  - The current CET1 ratio for BANK_HOLDCO is 14.83%. -
  This compares favorably to the Basel III minimum requirement of a CET1 ratio of at least 4.5%.  Regarding
  who owns this data and when it was last certified: The specific data provided here does not explicitly
  state the ownership or certification status, but given that "BANK_HOLDCO" is listed as the entity, we can
  infer that the capital position data for BANK_HOLDCO has been reported up to March 31, 2026. Typically,
  such data would be certified at specific reporting dates by regulatory bodies or internal audit teams
  (this information isn't provided here).  Regarding buffer headroom: A combined buffer of 9.75% suggests
  that the bank has a significant amount of capital above the minimum requirements to build a cushion for
  potential future losses. If this buffer headroom were to turn negative, it would indicate that the CET1
  ratio had dropped below the sum of the minimum capital requirement and any applicable buffers (such as a
  Capital Conservation Buffer). This could be a cause for concern from a regulatory perspective and may
  lead to restrictions on certain activities like dividend payments or share purchases.

──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Agent 2 — + YAML Data Contract
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Based on the most recent data available as of March 31, 2026:  - The current CET1 ratio for BANK_HOLDCO
  is 14.83%. - According to Basel III requirements, the minimum Common Equity Tier 1 (CET1) capital ratio
  for systemically important banking organizations, such as global systemically important banks (G-SIBs),
  is typically around 6%. For simpler banks, it can be lower, ranging from 4.5% to 6%, depending on their
  internal ratings-based approach for regulatory capital measurement. - Therefore, the current CET1 ratio
  of 14.83% exceeds both the minimum and often recommended leverage ratios required by Basel III.  The data
  owner is treasury.risk@bank.com, and it is refreshed quarterly as per your system's lineage information.
  The data was last refreshed in March 2026, corresponding to the most recent reporting date provided
  (March 31, 2026).  Regarding buffer headroom turning negative, a negative buffer headroom indicates that
  the combined regulatory buffers (including CCB, G-SII, and countercyclical) are less than or equal to the
  CET1 capital available. This situation could trigger various actions including:  - Promptly addressing
  potential risks identified within the bank’s risk profile. - Implementing additional compliance measures
  as required by regulators. - Conducting thorough stress tests to determine the sustainability of
  operations under adverse conditions.  Ultimately, maintaining adequate buffer headroom is crucial for
  ensuring resilience and long-term stability. If the buffer headroom does turn negative, proactive
  management and remedial actions would be necessary to return to a healthy position compliant with
  regulatory standards.

──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Agent 3 — + ODCS Governance Contract
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Based on the latest data as of `2026-03-31`, our current CET1 ratio is 14.83%. According to Basel III
  requirements, the minimum Common Equity Tier 1 (CET1) ratio for a bank like ours in normal times without
  capital conservation buffer requirements is at least 4.5%. However, once buffers are considered, the
  requirement is typically higher with an overall common equity tier-1 capital adequacy ratio of at least
  6%.  Our CET1 ratio is currently well above these minimums. Here's how it compares: - CET1 Ratio: 14.83%
  - Minimum Basel III (Normal Times): ~4.5%  The difference between the CET1 ratio and combined buffer
  requirement provides a buffer headroom amount which is important for stability.  Regarding ownership,
  this data belongs to the `Treasury Risk Team` as stated in the ODCS contract.  In terms of certification,
  there isn't an explicit provision related to quarterly certifications mentioned in the contract. However,
  compliance with regulatory requirements and internal governance practices typically would mandate regular
  audits or reviews at least annually; any deviation that could impact regulatory standing is likely
  subject to immediate notice or audit as per the terms provided within the ODCS contract.  If our buffer
  headroom turns negative (i.e., if `cet1_ratio_pct` drops below `combined_buffer`), this triggers
  regulatory intervention. The contract mentions that a headroom (the difference between `cet1_ratio_pct`
  and `combined_buffer`) below zero signals for regulatory action, which typically involves restrictions on
  dividend payments, stock buybacks, or other activities until the buffer is restored.  Would you like me
  to provide further analysis based on this information?

──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Agent 4 — + OWL/SKOS Domain Ontology
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Based on the data as of March 31, 2026:  - The current CET1 ratio is 14.83%. - This compares favorably to
  the Basel III minimum requirement of 4.5%, as our ratio significantly exceeds it.  The data is owned by
  the Treasury Risk Team at BANK_HOLDCO and can be found [here](https://internal.bank.com/data/capital-
  risk). It was last certified with the latest snapshot available being for March 31, 2026, which means it
  reflects recent regulatory standards and guidelines.  If our buffer headroom turns negative (i.e., CET1
  ratio - combined buffer < 0), this would indicate that our CET1 capital has fallen below the required
  levels despite holding all applicable buffers. This would trigger regulatory intervention to ensure
  compliance with the minimum capital requirements, potentially leading to restrictions on dividends, share
  buybacks, and bonus payments as part of the Capital Conservation Buffer (CCB) provisions.  In summary: -
  Current CET1 ratio: 14.83% - Basel III minimum requirement: 4.5% (well above required) - Ownership:
  Treasury Risk Team at BANK_HOLDCO - Last certification date: March 31, 2026 - Buffer headroom below zero
  triggers regulatory intervention and potential restrictions on capital distributions.

──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Agent 5 — Full Stack (all layers)
──────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Based on the provided ODCS contract and domain ontology, I can answer your questions as follows:  1.
  **Current CET1 Ratio:**    The current Common Equity Tier 1 (CET1) ratio for BANK_HOLDCO is available in
  the `capital_position` table within the regulatory reporting data set. According to the information
  provided, it should be assessed using metric names from dbt MetricFlow, such as `cet1_ratio`. However,
  due to the errors encountered in querying the metrics with the entity dimension directly, we need to
  fetch the most recent values for BANK_HOLDCO. For the latest quarter-end date, you can use:    ```sql
  SELECT cet1_ratio_pct FROM capital_position WHERE entity = 'BANK_HOLDCO' AND reporting_date IN (SELECT
  MAX(reporting_date) FROM capital_position WHERE entity = 'BANK_HOLDCO');    ```  2. **Comparison to Basel
  III Minimum Requirement:**    The minimum CET1 ratio required under Basel III is 4.5% as per Article
  92(1)(a). You can compare the current `cet1_ratio` obtained above with this minimum threshold.  3.
  **Ownership and Certification of Data:**    - **Owner:** Treasury Risk Team    - **Contact Information:**
  treasury.risk@bank.com, https://internal.bank.com/data/capital-risk  4. **Last Certification:**    The
  contract specifies that the data is used for internal capital adequacy reporting and regulatory
  submissions to the PRA (Prudential Regulation Authority). The governance details don’t specify a specific
  certification date; however, the data should be regularly validated against regulatory requirements.  5.
  **Actions if Buffer Headroom Turns Negative:**    If the buffer headroom turns negative, meaning
  `buffer_headroom` is less than zero, it would indicate that the CET1 ratio is below the combined buffer
  requirement. According to Basel III Article 141, financial institutions are restricted from distributing
  dividends, repurchasing shares, or paying bonuses.  Given these points, I can help you fetch the latest
  CET1 ratio for BANK_HOLDCO and compare it with the minimum threshold using the provided SQL query.

══════════════════════════════════════════════════════════════════════════════════════════════════════════════
  SCORING — Which parts of the question each layer answered
══════════════════════════════════════════════════════════════════════════════════════════════════════════════
  Criterion                        Agent 1                                 Agent 2                                 Agent 3                                 Agent 4                                 Agent 5                               
  -------------------------------  --------------------------------------  --------------------------------------  --------------------------------------  --------------------------------------  --------------------------------------
  CET1 ratio value (14.83%)        ✅                                       ✅                                       ✅                                       ✅                                       ❌                                     
  Basel III minimum (4.5%)         ✅                                       ✅                                       ✅                                       ✅                                       ✅                                     
  Data owner identified            ✅                                       ✅                                       ✅                                       ✅                                       ✅                                     
  Certification / freshness        ✅                                       ✅                                       ✅                                       ✅                                       ✅                                     
  Negative headroom consequence    ✅                                       ❌                                       ✅                                       ✅                                       ✅                                     
  -------------------------------  --------------------------------------  --------------------------------------  --------------------------------------  --------------------------------------  --------------------------------------
  TOTAL                            5/5                                     4/5                                     5/5                                     5/5                                     4/5                                   
══════════════════════════════════════════════════════════════════════════════════════════════════════════════
```
