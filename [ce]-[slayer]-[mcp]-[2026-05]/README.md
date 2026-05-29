# Context Engineering — SLayer MCP Demo

**Example 6 of the CE series.** The same SLayer semantic layer from Examples
2 and 3, now exposed as an **MCP server**. No Python agent. No REST calls.
No tool definitions. Claude Desktop or Claude Code discovers SLayer tools
natively — the semantic layer becomes invisible infrastructure.

```
config/claude_desktop_jaffle.json  — Claude Desktop config (Jaffle Shop dataset)
config/claude_desktop_bfsi.json    — Claude Desktop config (BFSI capital position)
```

---

## What changes from Examples 2 & 3

| | Examples 2 & 3 — REST API | Example 6 — MCP |
|---|---|---|
| Agent code | Python script (~170 lines) | None |
| Tool definition | Manual, in code | Auto-discovered from SLayer |
| Transport | HTTP REST (`POST /query`) | stdio MCP |
| Client | Custom agent loop | Claude Desktop / Claude Code |
| SQL visibility | Logged via structlog | Visible in Claude's tool call trace |
| Payload format | Must shape measures/dimensions manually | Handled by MCP protocol |
| Setup | `python agent_slayer_*.py` | One config line in Claude Desktop |

**The key shift:** In Examples 2 & 3, you write an agent that calls SLayer.
In Example 6, Claude *is* the agent — SLayer tools appear in Claude Desktop
the same way any MCP server tool does. No glue code needed.

---

## How SLayer MCP Works

SLayer runs two server modes:

```
slayer serve   →  REST API at http://127.0.0.1:5143  (Examples 2 & 3)
slayer mcp     →  MCP server over stdio               (this example)
```

Both share the same default storage (`~/.local/share/slayer`), so any
datasource registered via `setup_bfsi.py` is automatically available in the
MCP server too — no re-registration needed.

When Claude Desktop connects to `slayer mcp`, SLayer exposes tools such as:
- `query_model` — query any registered semantic model with measures and dimensions
- `list_models` — discover available models and their columns
- `get_model` — inspect a model's schema and metadata

Claude uses these tools automatically when you ask a business question.

---

## Option A — Jaffle Shop (zero prerequisites, 2 steps)

**Step 1 — Add SLayer to Claude Desktop config:**

```bash
# macOS — open the config file
open ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

Add (or merge into any existing `mcpServers` block):
```json
{
  "mcpServers": {
    "slayer": {
      "command": "uvx",
      "args": ["--from", "motley-slayer[all]", "slayer", "mcp", "--demo"],
      "env": {}
    }
  }
}
```

> `uvx` is bundled with `uv`. If you don't have it: `pip install uv`.
> The `--demo` flag auto-ingests the Jaffle Shop dataset on first run — idempotent, nothing to bootstrap.

**Step 2 — Restart Claude Desktop and ask:**

```
What are the top 3 stores by total order revenue?
How many orders were placed in the last 30 days?
Which customers have placed more than 5 orders?
What is the average order value by store?
```

Claude calls SLayer MCP tools → SLayer compiles SQL → DuckDB executes → answer in chat.
No Python. No REST calls. No agent loop.

---

## Option B — BFSI Capital Position (requires Example 3 setup)

**Step 1 — Register the BFSI datasource (once):**
```bash
# Start SLayer REST server
uvx --from 'motley-slayer[all]' slayer serve --demo

# In a new terminal — register capital_bfsi datasource
cd ../[ce]-[slayer]-[bfsi]-[2026-05]/code
python bootstrap_bfsi.py && python setup_bfsi.py
```

This writes the `capital_bfsi` datasource to SLayer's default storage
(`~/.local/share/slayer`) — shared with the MCP server.

**Step 2 — Stop the REST server. Add SLayer MCP to Claude Desktop:**

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

> No `--demo` flag here — you want your registered `capital_bfsi`
> datasource, not just the Jaffle Shop demo.

**Step 3 — Restart Claude Desktop.**

**Step 4 — Ask capital adequacy questions:**
```
What is our current CET1 ratio?
How much buffer headroom do we have as of the latest reporting date?
Show me the CET1 ratio trend across all three quarters.
What is our risk-weighted asset position as of Q1 2026?
```

---

## Option C — Claude Code (CLI, no GUI needed)

Add SLayer as an MCP server directly in Claude Code:

```bash
# Jaffle Shop
claude mcp add slayer -- uvx --from 'motley-slayer[all]' slayer mcp --demo

# BFSI (after setup_bfsi.py has been run)
claude mcp add slayer -- uvx --from 'motley-slayer[all]' slayer mcp
```

Then start Claude Code and ask the same business questions. SLayer tools
appear automatically in the tool list.

---

## Architecture

```
┌──────────────────────────────────────┐
│         Claude Desktop / Code        │
│  (LLM + MCP client built-in)         │
└──────────────────┬───────────────────┘
                   │  MCP protocol (stdio)
                   │  auto-discovers tools
                   ▼
┌──────────────────────────────────────┐
│           SLayer MCP Server          │
│      slayer mcp --demo               │
│                                      │
│  Tools exposed:                      │
│  • query_model   (measures/dims)     │
│  • list_models   (discovery)         │
│  • get_model     (schema inspect)    │
└──────────────────┬───────────────────┘
                   │  compiles SQL
                   ▼
┌──────────────────────────────────────┐
│              DuckDB                  │
│  Jaffle Shop  /  capital_bfsi        │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  Answer — in Claude Desktop chat     │
│  No Python. No agent loop. No REST.  │
└──────────────────────────────────────┘
```

---

## CE Series

| Example | Semantic component | Agent code required |
|---------|-------------------|---------------------|
| [Example 1](../[ce]-[hello-world]-[2026-05]/README.md) | Hand-written YAML contract | Yes — `agent.py` |
| [Example 2](../[ce]-[slayer]-[hello-world]-[2026-05]/README.md) | Semantic model — SLayer REST (generic) | Yes — `agent_slayer_hw.py` |
| [Example 3](../[ce]-[slayer]-[bfsi]-[2026-05]/README.md) | Semantic model — SLayer REST (BFSI) | Yes — `agent_slayer_bfsi.py` |
| [Example 4](../[ce]-[odcs]-[bfsi]-[2026-05]/README.md) | Formal ODCS contract | Yes — `agent_odcs.py` |
| [Example 5](../[ce]-[odps]-[trade]-[2026-05]/README.md) | Data product (ODPS 2.0) | Yes — `agent_odps.py` |
| **Example 6 (this)** | **Semantic layer via MCP (generic)** | **No — Claude Desktop / Claude Code** |
| [Example 7](../[ce]-[slayer]-[mcp]-[bfsi]-[2026-05]/README.md) | Semantic layer via MCP (BFSI) | No — Claude Desktop |
| [Example 8](../[ce]-[ontology]-[bfsi]-[2026-05]/README.md) | OWL/SKOS domain ontology | Yes — `agent_ontology_ollama.py` |
| [Example 9](../[ce]-[metrics]-[bfsi]-[2026-05]/README.md) | dbt Metric Layer (MetricFlow) | Yes — `agent_metrics_ollama.py` |
| [Example 10](../[ce]-[agentic]-[full-stack]-[2026-05]/README.md) | Full stack comparison | One question, five agents, scored — CE's measurable payoff |

---

## Stack

| Layer | Component |
|---|---|
| Semantic layer | SLayer (`motley-slayer[all]`) |
| Transport | MCP stdio |
| MCP client | Claude Desktop / Claude Code |
| Dataset A | Jaffle Shop (built-in demo) |
| Dataset B | `capital_bfsi` (from Example 3) |
| Storage | `~/.local/share/slayer` (default, shared) |
