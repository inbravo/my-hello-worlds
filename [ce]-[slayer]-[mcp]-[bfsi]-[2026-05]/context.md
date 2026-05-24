# Context — CE SLayer MCP BFSI Demo

## What this is
BFSI-specific MCP demo. The same capital adequacy data from Example 3
(`[ce]-[slayer]-[bfsi]-[2026-05]`) — but now accessed via SLayer's MCP
server instead of the REST API. No Python agent. Claude Desktop is the agent.

## What it shows
- SLayer MCP server exposes capital_position model as native Claude tools
- Claude Desktop answers CET1 / buffer headroom questions with zero code
- The same semantic layer works over REST (Example 3) AND MCP (this)
- The transport changes — the semantic context does not

## Run order
1. `python bootstrap_mcp_bfsi.py`  — seed capital_bfsi.duckdb (once)
2. `uvx ... slayer serve`           — start REST server (for registration only)
3. `python setup_mcp_bfsi.py`       — register datasource into SLayer storage
4. Stop REST server
5. Add `config/claude_desktop_bfsi.json` to Claude Desktop config
6. Restart Claude Desktop
7. Ask: "What is our current CET1 ratio and buffer headroom?"

## Stack
| Layer         | Component                          |
|---------------|-------------------------------------|
| Semantic layer | SLayer (motley-slayer[all])        |
| Transport     | MCP stdio                           |
| MCP client    | Claude Desktop / Claude Code        |
| Data          | DuckDB (capital_bfsi.duckdb)        |
| Storage       | ~/.local/share/slayer (default)     |

## Series position
| Demo | Folder | Semantic component |
|------|--------|--------------------|
| 1 | [ce]-[hello-world]-[2026-05]              | YAML contract |
| 2 | [ce]-[slayer]-[hello-world]-[2026-05]     | SLayer REST — generic |
| 3 | [ce]-[slayer]-[bfsi]-[2026-05]            | SLayer REST — BFSI |
| 4 | [ce]-[odcs]-[bfsi]-[2026-05]              | ODCS contract |
| 5 | [ce]-[odps]-[trade]-[2026-05]             | ODPS data product |
| 6 | [ce]-[slayer]-[mcp]-[2026-05]             | SLayer MCP — generic |
| **7** | **[ce]-[slayer]-[mcp]-[bfsi]-[2026-05]** | **SLayer MCP — BFSI** |
| 8 | [ce]-[ontology]-[bfsi]-[2026-05]          | Ontology — coming |
| 9 | [ce]-[metrics]-[bfsi]-[2026-05]           | Metric layer — coming |
| 10 | [ce]-[agentic]-[full-stack]-[2026-05]    | Full stack — coming |
