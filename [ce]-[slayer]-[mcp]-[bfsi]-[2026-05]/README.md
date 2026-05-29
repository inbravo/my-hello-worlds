# Context Engineering — SLayer MCP BFSI Demo

**Example 7 of the CE series.** The same Basel III/IV capital adequacy data
from [Example 3](../[ce]-[slayer]-[bfsi]-[2026-05]/README.md) — now accessed
via **SLayer's MCP server** instead of the REST API. No Python agent. No tool
definitions. Claude Desktop is the agent.

```
code/bootstrap_mcp_bfsi.py   — seed capital_bfsi.duckdb
code/setup_mcp_bfsi.py       — register datasource into SLayer storage
config/claude_desktop_bfsi.json — Claude Desktop MCP config
```

---

## What changes from Example 3

| | Example 3 — SLayer REST | Example 7 — SLayer MCP |
|---|---|---|
| Agent | Python script (~170 lines) | None — Claude Desktop |
| Transport | HTTP REST `POST /query` | MCP stdio |
| Tool definition | Manual, in code | Auto-discovered |
| Payload shaping | Manual (measures/dimensions as dicts) | Handled by MCP |
| SQL visibility | structlog `slayer.sql` event | Claude tool call trace |
| Start command | `python agent_slayer_bfsi_ollama.py` | Open Claude Desktop |

**Same semantic layer. Same data. Zero agent code.**

---

## Quick Start

**Step 1 — Install dependencies:**
```bash
cd code/
pip install requests duckdb
pip install uv   # for uvx
```

**Step 2 — Bootstrap the database (once):**
```bash
python bootstrap_mcp_bfsi.py
```

```
Created : capital_bfsi.duckdb
Path    : /your/absolute/path/capital_bfsi.duckdb
Seeded  : 3 rows → capital_position
```

**Step 3 — Start SLayer REST server (needed for registration only):**
```bash
uvx --from 'motley-slayer[all]' slayer serve
```

**Step 4 — Register the BFSI datasource (new terminal):**
```bash
python setup_mcp_bfsi.py
```

```
[1/3] Checking SLayer REST server at http://127.0.0.1:5143 ...
      Server is up.
[2/3] Registering datasource 'capital_bfsi' → /your/path/capital_bfsi.duckdb
      Done: {"status": "ok"}
[3/3] Ingesting model 'capital_position' from 'capital_bfsi'
      Columns : ['reporting_date', 'entity', 'cet1_capital_mm', 'rwa_mm', 'cet1_ratio_pct', 'combined_buffer']
      Source  : capital_bfsi

Setup complete. capital_bfsi is now in ~/.local/share/slayer.
```

**Step 5 — Stop the REST server (Ctrl+C).**

**Step 6 — Add SLayer MCP to Claude Desktop:**

Open your Claude Desktop config:
```bash
# macOS
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add (or merge) the following:
```json
{
  "mcpServers": {
    "slayer": {
      "command": "uvx",
      "args": ["--from", "motley-slayer[all]", "slayer", "mcp"],
      "env": {}
    }
  }
}
```

> No `--demo` flag — you want your registered `capital_bfsi` datasource,
> not the Jaffle Shop demo data.

**Step 7 — Restart Claude Desktop.**

**Step 8 — Ask capital adequacy questions:**

```
What is our current CET1 ratio?
How much buffer headroom do we have as of the latest reporting date?
Show me the CET1 ratio trend across all three quarters.
What is our risk-weighted asset position as of Q1 2026?
How has CET1 capital grown since September 2025?
Is our CET1 ratio above the combined buffer requirement?
```

Claude calls SLayer MCP tools → SLayer compiles SQL → DuckDB executes →
answer in Claude Desktop chat. No Python. No agent loop.

---

## The Data

`capital_bfsi.duckdb` — `capital_position` table:

| reporting_date | entity | cet1_capital_mm | rwa_mm | cet1_ratio_pct | combined_buffer |
|---|---|---|---|---|---|
| 2025-09-30 | BANK_HOLDCO | 27,410 | 190,500 | 14.39 | 9.75 |
| 2025-12-31 | BANK_HOLDCO | 28,150 | 192,000 | 14.66 | 9.75 |
| 2026-03-31 | BANK_HOLDCO | 29,273 | 197,400 | 14.83 | 9.75 |

Buffer headroom at latest date: **14.83 − 9.75 = 5.08 pp**

---

## Architecture

```
┌──────────────────────────────────────────┐
│           Claude Desktop                 │
│  (LLM + MCP client — no Python needed)  │
└──────────────────┬───────────────────────┘
                   │  MCP stdio
                   │  auto-discovers capital_position model
                   ▼
┌──────────────────────────────────────────┐
│        SLayer MCP Server                 │
│   uvx ... slayer mcp                     │
│                                          │
│   Reads: ~/.local/share/slayer           │
│   Finds: capital_bfsi datasource         │
│   Exposes: capital_position model        │
└──────────────────┬───────────────────────┘
                   │  compiles SQL
                   ▼
┌──────────────────────────────────────────┐
│   DuckDB (capital_bfsi.duckdb)           │
│   capital_position — 3 quarters          │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  "Our current CET1 ratio is 14.83%       │
│   against a combined buffer of 9.75%,    │
│   giving 5.08pp of headroom."            │
└──────────────────────────────────────────┘
```

---

## How SLayer Storage Works

```
slayer serve  ──writes──►  ~/.local/share/slayer/  ◄──reads──  slayer mcp
```

Both commands share the same default storage directory. Running
`setup_mcp_bfsi.py` against the REST server writes the `capital_bfsi`
datasource definition to that directory — so the MCP server picks it up
automatically with no further configuration.

---

## Also Works in Claude Code

```bash
claude mcp add slayer -- uvx --from 'motley-slayer[all]' slayer mcp
```

Then ask the same capital adequacy questions directly in Claude Code.

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
| **Example 7 (this)** | **Semantic layer via MCP (BFSI)** | **Capital adequacy via MCP — no Python** |
| [Example 8](../[ce]-[ontology]-[bfsi]-[2026-05]/README.md) | OWL/SKOS domain ontology | Concept hierarchy, Basel III articles |
| [Example 9](../[ce]-[metrics]-[bfsi]-[2026-05]/README.md) | dbt Metric Layer (MetricFlow) | Named governed metrics |
| [Example 10](../[ce]-[agentic]-[full-stack]-[2026-05]/README.md) | Full stack comparison | One question, five agents, scored — CE's measurable payoff |

---

## Stack

| Layer | Component |
|---|---|
| Semantic layer | SLayer (`motley-slayer[all]`) |
| Transport | MCP stdio |
| MCP client | Claude Desktop / Claude Code |
| Data | DuckDB (`capital_bfsi.duckdb`) |
| Storage | `~/.local/share/slayer` (shared with REST server) |
