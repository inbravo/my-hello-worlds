# Context Engineering — ODPS Trade Finance Demo

**Example 4 of the CE series.** Introduces the **Open Data Product Standard
(ODPS 2.0)** as the agent's context layer. Steps up from a table-level
contract (Example 3 — ODCS) to a **product-level definition** that describes
a business capability — including input ports, output ports, ownership, SLAs,
use cases, and quality rules.

New domain: **Trade Finance** — counterparty exposure, settlement risk,
credit concentration. Shows CE is not capital adequacy-specific.

```
products/trade_exposure_product.yaml  — ODPS 2.0 data product definition
bootstrap_odps.py                     — seed trade_odps.duckdb
agent_odps_ollama.py                  — Option A: Ollama (qwen2.5) — recommended
agent_odps.py                         — Option B: Claude via Anthropic SDK
```

---

## What is ODPS?

**Open Data Product Standard (ODPS)** is an open specification for describing data products in a standard, machine-readable format. Think of it as **OpenAPI for data products** — the same way OpenAPI describes a REST API (endpoints, inputs, outputs, auth), ODPS describes a data product (where data comes from, how it is accessed, who owns it, what SLAs apply, what it is built to answer).

Maintained by the **Open Data Product Initiative** under the Linux Foundation Data & AI. Version 2.0 is the current stable specification.

| Analogy | Describes |
|---|---|
| OpenAPI (Swagger) | A REST API — endpoints, request/response, auth |
| ODCS (Bitol) | A data table — schema, quality, SLA, ownership |
| **ODPS** | **A data product — ports, use cases, SLAs, pricing, governance** |

ODPS is the right standard when you are operating a **data mesh** or **data product marketplace** — where teams publish and consume governed data products rather than raw tables. The agent in this demo reads the product definition the same way a developer reads an OpenAPI spec before calling an API.

---

## ODCS vs ODPS — and why choose ODPS

ODCS asks: *"What does this table mean and who governs it?"*
ODPS asks: *"What does this data product deliver, to whom, and how?"*

| | ODCS (Bitol) | ODPS 2.0 |
|---|---|---|
| **Unit** | A table or dataset | A business capability / data product |
| **Audience** | Data engineers, analysts | Data product owners, consumers, AI agents |
| **Describes** | Schema, quality, SLA, ownership | Ports, use cases, pricing, contracts, SLAs |
| **Input ports** | No | Yes — where data originates |
| **Output ports** | No | Yes — how data is consumed |
| **Use cases** | No | Yes — explicit list of approved questions |
| **Pricing / chargeback** | No | Yes |
| **Data mesh fit** | Partial | Native — built for mesh architecture |
| **Discovery / catalogue** | Not designed for it | Designed for data product marketplaces |
| **Maturity level** | Table governance | Product governance |

**When to use which:**

| Situation | Use |
|---|---|
| Govern one table — schema, quality, SLA, owner | ODCS |
| Publish a data product consumed by multiple teams | ODPS |
| Building a data mesh with product ownership | ODPS |
| AI agent needs to know *what problem the data solves* | ODPS |
| Need input/output port definitions for lineage | ODPS |
| Running a data product catalogue or marketplace | ODPS |

**The simplest way to explain it:**

> ODCS is a governed label on a jar — it tells you what is inside, who made it, and whether it is fresh.
> ODPS is the full product spec — what problem it solves, who it is for, how to get it, what it costs, and what you can build with it.

Both belong in the semantic stack. ODCS sits closer to the engineering layer. ODPS sits at the product and business layer — exactly where AI agents need to operate at scale.

---

## What changes from Example 3 (ODCS)

| | Example 3 — ODCS (Bitol) | Example 4 — ODPS 2.0 |
|---|---|---|
| Standard | Bitol ODCS 0.9.3 | Open Data Product Standard 2.0 |
| Level | Table / schema | Business capability / product |
| Defines | One table with governance | A data product with ports, SLAs, use cases |
| Input ports | Not defined | Source system, refresh cadence |
| Output ports | Not defined | DuckDB path, table definitions |
| Use cases | Not defined | Explicit list of approved use cases |
| Domain | BFSI — capital adequacy | Trade Finance — new domain |
| Agent answers | Data + governance questions | Data + product + use case questions |

**The key shift:** ODCS governs a table. ODPS governs a **business capability**.
The agent now understands not just what the data contains, but what problem
the data product is built to solve — and for whom.

---

## The ODPS Product Structure

`products/trade_exposure_product.yaml` follows the ODPS 2.0 spec:

```
openDataProductSpecification: 2.0.0
product:
  name, productID, domain, status, version
  description       — what this product delivers
  owner             — team and contact email
  useCases          — what questions this product is built to answer
  inputPorts        — where data originates (core trading system)
  outputPorts       — how data is accessed (DuckDB table + column definitions)
  slaProperties     — freshness (T+1), completeness (100%), uptime (99.9%)
  dataQuality       — validity and completeness checks
  terms             — usage policy, retention, notice period
  pricing           — internal / free
```

The agent reads all sections and builds a product-aware tool description —
so it understands the business capability, not just the schema.

---

## Quick Start

**Step 1 — Install dependencies:**

```bash
cd code/
pip install openai anthropic duckdb pyyaml structlog
```

**Step 2 — Bootstrap the database (once):**

```bash
python bootstrap_odps.py
```

```
Created : trade_odps.duckdb
Path    : /your/absolute/path/trade_odps.duckdb
Seeded  : 10 rows → trade_exposure
         Counterparties : GOLDMAN_SACHS, DEUTSCHE_BANK, BARCLAYS, JPMORGAN,
                          CREDIT_SUISSE, CITIBANK, HSBC
         Instruments    : FX_FORWARD, BOND, DERIVATIVE
         Regions        : EUROPE, NORTH_AMERICA
```

**Step 3A — Run with Ollama (recommended):**

```bash
ollama serve && ollama pull qwen2.5
python agent_odps_ollama.py
```

**Step 3B — Run with Anthropic:**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python agent_odps.py
```

**Step 4 — Capture the trace:**

```bash
python agent_odps_ollama.py > trace.jsonl
```

---

## The Question

Both agents ask:

> *"What is our total trade exposure by counterparty for all open trades?
> Which trades are settling within the next 30 days? Is this data fresh
> and who is responsible for it?"*

Three parts — **exposure**, **settlement risk**, **governance**.
All three are answerable from the ODPS product definition + the data.

---

## The Data

`trade_odps.duckdb` — `trade_exposure` table:

| trade_id | counterparty | instrument_type | notional_usd_mm | settlement_date | credit_rating | region | status |
|---|---|---|---|---|---|---|---|
| T001 | GOLDMAN_SACHS | FX_FORWARD | 450.00 | 2026-05-30 | AA | NORTH_AMERICA | OPEN |
| T002 | DEUTSCHE_BANK | BOND | 320.00 | 2026-06-15 | A | EUROPE | OPEN |
| T003 | BARCLAYS | DERIVATIVE | 180.00 | 2026-05-28 | AA | EUROPE | OPEN |
| T004 | JPMORGAN | FX_FORWARD | 890.00 | 2026-06-01 | AAA | NORTH_AMERICA | OPEN |
| T005 | CREDIT_SUISSE | BOND | 220.00 | 2026-05-25 | BB | EUROPE | OPEN |
| T006 | CITIBANK | DERIVATIVE | 560.00 | 2026-06-20 | A | NORTH_AMERICA | OPEN |
| T007 | GOLDMAN_SACHS | BOND | 340.00 | 2026-07-01 | AA | NORTH_AMERICA | OPEN |
| T008 | HSBC | FX_FORWARD | 410.00 | 2026-05-29 | AA | EUROPE | OPEN |
| T009 | DEUTSCHE_BANK | DERIVATIVE | 150.00 | 2026-06-10 | A | EUROPE | SETTLED |
| T010 | BARCLAYS | FX_FORWARD | 280.00 | 2026-07-15 | AA | EUROPE | OPEN |

---

## What ODPS Adds Over ODCS

**Input port — where data comes from:**
```yaml
inputPorts:
  - name: core_trading_system
    type: operational_db
    refreshCadence: daily
    refreshTime: "06:00 GMT"
```

**Output port — how data is accessed:**
```yaml
outputPorts:
  - name: trade_exposure_db
    type: duckdb
    path: trade_odps.duckdb
    tables:
      - name: trade_exposure
        description: Open and settled trade positions per counterparty...
```

**SLA properties:**
```yaml
slaProperties:
  - dimension: freshness
    value: T+1
    description: Positions updated by 08:00 GMT each business day
  - dimension: completeness
    value: 100%
  - dimension: uptime
    value: 99.9%
```

**Use cases — explicit list of approved questions:**
```yaml
useCases:
  - Counterparty exposure monitoring and limit management
  - Settlement risk identification (trades due within N days)
  - Credit concentration analysis by rating band
  - Regional exposure breakdown (EMEA vs North America)
  - AI-assisted risk queries via natural language
```

---

## Sample Trace

```jsonl
{"event":"agent.start","odps_version":"2.0.0","product_status":"active","product_domain":"Trade Finance","product_owner":"trade.risk@bank.com","timestamp":"..."}
{"event":"agent.turn1","stop_reason":"tool_calls","latency_ms":743,"timestamp":"..."}
{"event":"tool.call","sql":"SELECT counterparty, SUM(notional_usd_mm) as total_exposure FROM trade_exposure WHERE status = 'OPEN' GROUP BY counterparty ORDER BY total_exposure DESC","timestamp":"..."}
{"event":"tool.result","rows":6,"data":[...],"timestamp":"..."}
{"event":"agent.answer","latency_ms":581,"timestamp":"..."}
```

---

## Trying Different Questions

```python
QUESTION = "What is our total exposure to European counterparties?"
QUESTION = "Which counterparties are rated BB or below and what is our exposure to them?"
QUESTION = "Break down our open exposure by instrument type."
QUESTION = "What trades are due for settlement this week?"
QUESTION = "What is this data product for and who owns it?"
QUESTION = "What are the SLA commitments for this data product?"
```

---

## CE Series

| Example | Semantic component | New concept introduced |
|---------|-------------------|------------------------|
| [Example 1](../[ce]-[hello-world]-[2026-05]/README.md) | Hand-written YAML contract | Data contract as context |
| [Example 2](../[ce]-[slayer]-[bfsi]-[2026-05]/README.md) | Semantic model (SLayer) | Semantic layer as context |
| [Example 3](../[ce]-[odcs]-[bfsi]-[2026-05]/README.md) | Formal ODCS contract (Bitol) | Governed, standard-compliant contract |
| **Example 4 (this)** | **Data product (ODPS 2.0)** | **Product-level context — ports, use cases, SLAs** |
| Example 5 | Ontology (OWL/RDF + OBML) | Domain knowledge as context |
| Example 6 | Metric layer | Named business metrics as context |
| Example 7 | Full stack comparison | Measurable quality difference across all layers |

---

## Stack

| Layer | Component |
|---|---|
| Product standard | Open Data Product Standard (ODPS) 2.0 |
| Product file | `products/trade_exposure_product.yaml` |
| Data | DuckDB (`trade_odps.duckdb`) |
| Agent (local) | Ollama (`qwen2.5`) |
| Agent (cloud) | Claude (`claude-sonnet-4-6`) |
| Observability | structlog JSON |

## Example Execution

```bash
python agent_odps.py
```

```json
{"question": "...", "event": "agent.start", ...}
{"stop_reason": "tool_use", "event": "agent.turn1", ...}
{"sql": "SELECT ...", "event": "tool.call", ...}
{"rows": 7, "data": [...], "event": "tool.result", ...}
{"event": "agent.answer", ...}
```

```
============================================================
<answer text here>
============================================================
```