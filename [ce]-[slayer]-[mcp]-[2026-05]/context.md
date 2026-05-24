# Context — CE SLayer MCP Demo

## What this is
Demo 6 in the Context Engineering series (parallel to Examples 2 & 3).
Shows SLayer used as an **MCP server** instead of a REST API — no Python
agent code required. Claude Desktop or Claude Code discovers SLayer tools
natively and answers business questions directly.

## What it shows
- SLayer exposes the same semantic layer via MCP (stdio transport)
- Claude Desktop wires in as a native MCP client — zero agent code
- The semantic layer becomes invisible infrastructure
- Two datasets: Jaffle Shop (generic) and BFSI capital position

## Two options
| Option | Config file | Dataset | Use case |
|--------|-------------|---------|----------|
| Jaffle Shop | `config/claude_desktop_jaffle.json` | Demo orders/stores | Generic demo |
| BFSI | `config/claude_desktop_bfsi.json` | Capital position | Domain-specific |

## Prerequisites for BFSI option
Run Example 3 (`[ce]-[slayer]-[bfsi]-[2026-05]`) setup first:
```bash
cd ../[ce]-[slayer]-[bfsi]-[2026-05]/code
python bootstrap_bfsi.py && python setup_bfsi.py
```
This registers `capital_bfsi` into SLayer's default storage, which the
MCP server shares.

## Series position
| Demo | Folder | Semantic component |
|------|--------|--------------------|
| 1 | [ce]-[hello-world]-[2026-05]          | Hand-written YAML contract |
| 2 | [ce]-[slayer]-[hello-world]-[2026-05] | Semantic model — REST API |
| 3 | [ce]-[slayer]-[bfsi]-[2026-05]        | Semantic model — BFSI REST API |
| 4 | [ce]-[odcs]-[bfsi]-[2026-05]          | Formal ODCS contract |
| 5 | [ce]-[odps]-[trade]-[2026-05]         | Data product (ODPS 2.0) |
| **6** | **[ce]-[slayer]-[mcp]-[2026-05]**  | **SLayer via MCP — zero code** |
| 7 | [ce]-[ontology]-[bfsi]-[2026-05]      | Ontology OWL/RDF + OBML — coming |
| 8 | [ce]-[metrics]-[bfsi]-[2026-05]       | Metric layer — coming |
| 9 | [ce]-[agentic]-[full-stack]-[2026-05] | Quality comparison — coming |
