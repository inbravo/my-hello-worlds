# Context Engineering — SLayer BFSI Use Case

A capital adequacy agent that registers a DuckDB datasource with a running SLayer instance, auto-ingests the `capital_position` model, and answers Basel III/IV questions. Extends the [SLayer Hello World](../[ce]-[slayer]-[hello-world]-[2026-05]/README.md) with a real BFSI data layer.

```
bootstrap_bfsi.py            — create and seed capital_bfsi.duckdb
setup_bfsi.py                — register datasource + ingest model into SLayer
agent_slayer_bfsi.py         — Option A: Claude via Anthropic SDK
agent_slayer_bfsi_ollama.py  — Option B: same loop via Ollama (qwen2.5)
```

---

## Quick Start

**Step 1 — Start SLayer (keep this terminal running):**

```bash
uvx --from 'motley-slayer[all]' slayer serve --demo
```

**Step 2 — Install dependencies:**

```bash
cd code/
pip install anthropic openai requests duckdb structlog
```

**Step 3 — Bootstrap the database (once):**

```bash
python bootstrap_bfsi.py
```

```
Created : capital_bfsi.duckdb
Path    : /your/absolute/path/capital_bfsi.duckdb
Seeded  : 3 rows → capital_position
```

**Step 4 — Register with SLayer (once):**

```bash
python setup_bfsi.py
```

```
[1/3] Registering datasource 'capital_bfsi' → /your/path/capital_bfsi.duckdb
      Done: {"status": "ok"}
[2/3] Ingesting models from 'capital_bfsi' (table: capital_position)
      Done: {...}
[3/3] Verifying model 'capital_position' is available
      Columns : ['reporting_date', 'entity', 'cet1_capital_mm', 'rwa_mm', 'cet1_ratio_pct', 'combined_buffer']
      Source  : capital_bfsi

Ready. Run agent_slayer_bfsi.py to ask questions.
```

**Step 5A — Run with Anthropic:**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python agent_slayer_bfsi.py
```

**Step 5B — Run with Ollama:**

```bash
ollama serve && ollama pull qwen2.5
python agent_slayer_bfsi_ollama.py
```

**Step 6 — Capture the trace:**

```bash
python agent_slayer_bfsi.py > trace.jsonl          # Anthropic
python agent_slayer_bfsi_ollama.py > trace.jsonl   # Ollama
```

---

## The Banking Use Case

Under Basel III/IV, banks must hold Common Equity Tier 1 (CET1) capital above a stacked set of regulatory buffers:

- **CET1 ratio** = CET1 capital ÷ Risk-Weighted Assets × 100
- **Combined buffer** = Capital Conservation Buffer (2.5%) + G-SII buffer + Countercyclical buffer
- **Headroom** = CET1 ratio − combined buffer (must remain positive)

A CET1 of **14.83%** against a combined buffer of **9.75%** gives **5.08 pp of headroom**. Breaching this triggers regulatory intervention — dividend restrictions, mandatory capital rebuild.

The agent asks and answers this in two turns. SLayer handles the SQL. The trace records both the metric name the agent requested *and* the SQL SLayer compiled — the full chain is observable.

---

## The Data

`capital_bfsi.duckdb` contains one table:

| reporting_date | entity | cet1_capital_mm | rwa_mm | cet1_ratio_pct | combined_buffer |
|---|---|---|---|---|---|
| 2025-09-30 | BANK_HOLDCO | 27,410 | 190,500 | 14.39 | 9.75 |
| 2025-12-31 | BANK_HOLDCO | 28,150 | 192,000 | 14.66 | 9.75 |
| 2026-03-31 | BANK_HOLDCO | 29,273 | 197,400 | 14.83 | 9.75 |

---

## How the Agent Loop Works

```
Turn 1 — agent requests capital metrics by formula
→ tool_call: {
      measures:   ["cet1_ratio_pct:max", "combined_buffer:max"],
      dimensions: ["reporting_date"],
      order:      [{"column": "reporting_date", "direction": "desc"}],
      limit:      1
  }

SLayer compiles to SQL → queries DuckDB → returns result + the SQL it generated

Turn 2 — agent reads metric values → plain-English answer
```

---

## Useful Formulas for Capital Queries

| Formula | Meaning |
|---|---|
| `cet1_ratio_pct:max` | Latest CET1 ratio |
| `combined_buffer:max` | Combined buffer requirement |
| `cet1_ratio_pct:max - combined_buffer:max` | Buffer headroom (inline) |
| `cet1_capital_mm:sum` | Total CET1 capital (GBP millions) |
| `rwa_mm:sum` | Total risk-weighted assets |
| `*:count` | Number of reporting periods |

---

## Sample Trace

```jsonl
{"event":"agent.start","question":"What is our current CET1 ratio...","slayer_model":"capital_position","data_source":"capital_bfsi","columns":["reporting_date","entity","cet1_capital_mm","rwa_mm","cet1_ratio_pct","combined_buffer"],"timestamp":"2026-05-09T10:01:00Z"}
{"event":"agent.turn1","stop_reason":"tool_use","latency_ms":698,"timestamp":"2026-05-09T10:01:01Z"}
{"event":"slayer.query","measures":["cet1_ratio_pct:max","combined_buffer:max"],"dimensions":["reporting_date"],"order":[{"column":"reporting_date","direction":"desc"}],"limit":1,"timestamp":"2026-05-09T10:01:01Z"}
{"event":"slayer.result","rows":1,"data":[{"capital_position.reporting_date":"2026-03-31","capital_position.cet1_ratio_pct_max":14.83,"capital_position.combined_buffer_max":9.75}],"timestamp":"2026-05-09T10:01:01Z"}
{"event":"slayer.sql","sql":"SELECT MAX(cet1_ratio_pct), MAX(combined_buffer), reporting_date FROM capital_position GROUP BY reporting_date ORDER BY reporting_date DESC LIMIT 1","timestamp":"2026-05-09T10:01:01Z"}
{"event":"agent.answer","latency_ms":541,"timestamp":"2026-05-09T10:01:02Z"}
```

The `slayer.sql` line is the key demo artefact — it shows the SQL SLayer compiled from the agent's metric request. The agent never wrote SQL. SLayer did.

---

## Trying Different Questions

Change `QUESTION` in either agent file:

```python
QUESTION = "Show me the CET1 ratio trend across all three quarters."
QUESTION = "How much has our CET1 capital grown since September 2025?"
QUESTION = "What is our buffer headroom as of the latest reporting date?"
QUESTION = "How do our risk-weighted assets compare quarter over quarter?"
```

---

## Stack

| Layer | Component |
|---|---|
| Data | DuckDB (`capital_bfsi.duckdb`) |
| Datasource registration | `POST /datasources` → SLayer REST API |
| Model ingestion | `POST /ingest` → auto-generated from table schema |
| Semantic Layer | SLayer HTTP server — `http://127.0.0.1:5143` |
| Agent (cloud) | Claude (`claude-sonnet-4-6`) via Anthropic SDK |
| Agent (local) | Ollama (`qwen2.5`) via OpenAI-compatible endpoint |
| Observability | structlog — logs metric request, result, and generated SQL |
