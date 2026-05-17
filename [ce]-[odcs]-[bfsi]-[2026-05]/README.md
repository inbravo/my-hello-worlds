# Context Engineering — ODCS BFSI Demo

**Demo 3 of the CE series.** Upgrades the hand-written YAML data contract from
[Demo 1](../[ce]-[hello-world]-[2026-05]/README.md) to a formal
**Bitol/ACRYL Open Data Contract Standard (ODCS 0.9.3)** contract.
Same CET1 capital adequacy data. Same DuckDB + Ollama runtime. Richer,
governed, standard-compliant context delivered to the LLM.

```
contracts/capital_risk_odcs.yaml  — formal ODCS 0.9.3 contract
bootstrap_odcs.py                 — seed capital_odcs.duckdb
agent_odcs_ollama.py              — Option A: Ollama (qwen2.5) — recommended
agent_odcs.py                     — Option B: Claude via Anthropic SDK
```

---

## What changes from Demo 1

| | Demo 1 — Hand-written YAML | Demo 3 — ODCS (Bitol) |
|---|---|---|
| Standard | None (informal) | Bitol ODCS 0.9.3 |
| Governance | Owner email only | Owner, status, usage terms, notice period |
| Quality | Not defined | SodaCL quality checks |
| SLA | Not defined | Availability, freshness, retention, support |
| Agent context | Table description + columns | All of the above — governance + data |
| Questions agent can answer | Data questions only | Data questions + governance questions |

**The upgrade is not just structural.** The agent now has enough context to
answer: *"Is this data certified?"*, *"Who owns it?"*, *"How fresh is it?"* —
alongside the usual CET1 / buffer headroom questions. This is what a governed
data contract enables.

---

## The ODCS Contract Structure

The `contracts/capital_risk_odcs.yaml` follows the Bitol ODCS 0.9.3 spec:

```
dataContractSpecification: 0.9.3
id:           unique URN for this contract
info:         title, version, status, owner, contact, tags
servers:      where the data lives (DuckDB path in this demo)
terms:        usage policy, limitations, notice period
models:       table definitions with field descriptions and examples
quality:      SodaCL data quality checks
servicelevels: availability, freshness, retention, support, backup SLAs
```

The agent reads all seven sections and injects the relevant context into its
tool description — so it understands not just the schema, but the governance
layer around it.

---

## Quick Start

**Step 1 — Install dependencies:**

```bash
cd code/
pip install openai anthropic duckdb pyyaml structlog
```

**Step 2 — Bootstrap the database (once):**

```bash
python bootstrap_odcs.py
```

```
Created : capital_odcs.duckdb
Path    : /your/absolute/path/capital_odcs.duckdb
Seeded  : 3 rows → capital_position
```

**Step 3A — Run with Ollama (recommended):**

```bash
ollama serve && ollama pull qwen2.5
python agent_odcs_ollama.py
```

**Step 3B — Run with Anthropic:**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python agent_odcs.py
```

**Step 4 — Capture the trace:**

```bash
python agent_odcs_ollama.py > trace.jsonl
```

---

## The Question

Both agents ask:

> *"What is our current CET1 ratio and buffer headroom? Is this data
> certified, and who should I contact if I have questions?"*

This question has two parts — a **data question** and a **governance question**.
Demo 1 could only answer the first. Demo 3 answers both, because the ODCS
contract supplies the governance context.

---

## The Data

`capital_odcs.duckdb` contains one table — identical to Demo 1:

| reporting_date | entity | cet1_capital_mm | rwa_mm | cet1_ratio_pct | combined_buffer |
|---|---|---|---|---|---|
| 2025-09-30 | BANK_HOLDCO | 27,410 | 190,500 | 14.39 | 9.75 |
| 2025-12-31 | BANK_HOLDCO | 28,150 | 192,000 | 14.66 | 9.75 |
| 2026-03-31 | BANK_HOLDCO | 29,273 | 197,400 | 14.83 | 9.75 |

---

## What the ODCS Contract Adds

**Quality checks (SodaCL):**
```yaml
checks for capital_position:
  - row_count > 0
  - duplicate_count(reporting_date, entity) = 0
  - missing_count(cet1_ratio_pct) = 0
  - min(cet1_ratio_pct) > 0
  - max(combined_buffer) < 25
```

**Service levels:**
```yaml
freshness:  Updated within 5 business days of each quarter-end
retention:  Rolling 3-year retention of quarterly snapshots
support:    Treasury Risk Team responds within 1 business day
```

These are injected into the tool description so the agent can state:
*"The data is governed under an active contract, quality-checked, and
refreshed within 5 business days of quarter-end."*

---

## Sample Trace

```jsonl
{"event":"agent.start","odcs_version":"0.9.3","contract_status":"active","contract_owner":"treasury.risk@bank.com","timestamp":"..."}
{"event":"agent.turn1","stop_reason":"tool_calls","latency_ms":812,"timestamp":"..."}
{"event":"tool.call","sql":"SELECT * FROM capital_position ORDER BY reporting_date DESC LIMIT 1","timestamp":"..."}
{"event":"tool.result","rows":1,"data":[{"reporting_date":"2026-03-31","cet1_ratio_pct":14.83,"combined_buffer":9.75}],"timestamp":"..."}
{"event":"agent.answer","latency_ms":634,"timestamp":"..."}
```

---

## Trying Different Questions

```python
QUESTION = "What is our latest CET1 ratio and how much buffer headroom do we have?"
QUESTION = "Is this capital data certified and current? Who is the data owner?"
QUESTION = "Show me the CET1 ratio trend across all three quarters."
QUESTION = "What quality checks apply to this data and are there any SLA commitments?"
QUESTION = "How long is this data retained and what are the usage restrictions?"
```

The last two questions are only answerable because the ODCS contract supplies
the governance context. Demo 1 could not answer them.

---

## CE Series

| Demo | Semantic component | New concept introduced |
|------|--------------------|------------------------|
| [Demo 1](../[ce]-[hello-world]-[2026-05]/README.md) | Hand-written YAML contract | Data contract as context |
| [Demo 2](../[ce]-[slayer]-[bfsi]-[2026-05]/README.md) | Semantic model (SLayer) | Semantic layer as context |
| **Demo 3 (this)** | **Formal ODCS contract (Bitol)** | **Governed, standard-compliant contract** |
| Demo 4 | Data Product (DPDS) | Data product definition as context |
| Demo 5 | Ontology (OWL/RDF + OBML) | Domain knowledge as context |
| Demo 6 | Metric layer | Named business metrics as context |
| Demo 7 | Full stack comparison | Measurable quality difference |

---

## Stack

| Layer | Component |
|---|---|
| Contract standard | Bitol ODCS 0.9.3 |
| Contract file | `contracts/capital_risk_odcs.yaml` |
| Data | DuckDB (`capital_odcs.duckdb`) |
| Agent (local) | Ollama (`qwen2.5`) |
| Agent (cloud) | Claude (`claude-sonnet-4-6`) |
| Observability | structlog JSON |


## Sample Output (qwen2.5 via Ollama)

```bash
(.venv) inbravo@IMUL-ML0515 code % python agent_odcs_ollama.py
{"question": "What is our current CET1 ratio and buffer headroom? Is this data certified, and who should I contact if I have questions?", "contract": "contracts/capital_risk_odcs.yaml", "odcs_version": "0.9.3", "contract_status": "active", "contract_owner": "treasury.risk@bank.com", "ollama_model": "qwen2.5", "event": "agent.start", "timestamp": "2026-05-15T15:31:25.376618Z"}
{"stop_reason": "tool_calls", "latency_ms": 6351, "event": "agent.turn1", "timestamp": "2026-05-15T15:31:31.764646Z"}
{"sql": "SELECT cet1_ratio_pct, combined_buffer, (cet1_ratio_pct - combined_buffer) as buffer_headroom FROM capital_position ORDER BY reporting_date DESC LIMIT 1", "event": "tool.call", "timestamp": "2026-05-15T15:31:31.764811Z"}
{"rows": 1, "data": [{"cet1_ratio_pct": "Decimal('14.8300')", "combined_buffer": "Decimal('9.7500')", "buffer_headroom": "Decimal('5.0800')"}], "event": "tool.result", "timestamp": "2026-05-15T15:31:31.803598Z"}
{"latency_ms": 7538, "event": "agent.answer", "timestamp": "2026-05-15T15:31:39.342488Z"}

============================================================
Based on the latest available data as of [reporting_date], our current CET1 ratio is 14.83%, and the buffer headroom, which is the difference between the CET1 ratio and the combined regulatory buffer, is 5.08%.

This data is certified for internal capital adequacy reporting, regulatory submissions, and AI-assisted analysis by authorised Treasury Risk personnel.

For any questions or further clarification, you can contact the Treasury Risk Team at treasury.risk@bank.com.

If these results are accurate and up-to-date according to your needs, please let me know. If not, we might need to review the data with more detail or from a different perspective.
============================================================
```