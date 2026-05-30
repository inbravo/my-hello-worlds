"""
CE Example 10 — Full Stack Comparison (Ollama / qwen2.5)

One question. Five agents. Increasing context richness. Scored comparison.

The question:
  "What is our current CET1 ratio, how does it compare to the Basel III
   minimum, who owns this data, when was it last certified, and what
   happens if our buffer headroom turns negative?"

No single earlier example answers all five parts. This demo runs all
context layers and shows exactly which parts each layer unlocks:

  Agent 1 — Baseline (schema only)          → answers 1/5 parts
  Agent 2 — + YAML Data Contract            → answers 1/5 parts
  Agent 3 — + ODCS Governance Contract      → answers 3/5 parts
  Agent 4 — + OWL/SKOS Ontology             → answers 4/5 parts
  Agent 5 — Full Stack (all layers)         → answers 5/5 parts

Usage:
    python3 bootstrap_full_stack.py   (once — seeds the DB)
    python3 run_comparison.py
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/inbravo/
# ─────────────────────────────────────────────────────

import os
import sys
import json
import textwrap
import subprocess
import duckdb
import yaml
import structlog
from openai import OpenAI
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from rdflib.namespace import SKOS

log = structlog.get_logger()

# ── Config ────────────────────────────────────────────────────────
OLLAMA_BASE  = "http://localhost:11434/v1"
OLLAMA_MODEL = "qwen2.5"
DB_FILE      = "capital_bfsi.duckdb"
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))

# Paths to sibling example context files
YAML_CONTRACT = os.path.join(
    SCRIPT_DIR, "../../[ce]-[hello-world]-[2026-05]/code/contracts/capital_risk.yaml"
)
ODCS_CONTRACT = os.path.join(
    SCRIPT_DIR, "../../[ce]-[odcs]-[bfsi]-[2026-05]/code/contracts/capital_risk_odcs.yaml"
)
ONTOLOGY_TTL  = os.path.join(
    SCRIPT_DIR, "../../[ce]-[ontology]-[bfsi]-[2026-05]/ontology/bfsi_capital.ttl"
)
DBT_PROJECT   = os.path.join(
    SCRIPT_DIR, "../../[ce]-[metrics]-[bfsi]-[2026-05]/dbt_project"
)

BFSI = Namespace("https://github.com/inbravo/ce-series/ontology/bfsi#")

# ── The test question ─────────────────────────────────────────────
QUESTION = (
    "What is our current CET1 ratio, how does it compare to the Basel III "
    "minimum requirement, who owns this data and when was it last certified, "
    "and what happens if our buffer headroom turns negative?"
)

# ── Scoring rubric ────────────────────────────────────────────────
# Criteria use EXACT strings from context files — not general knowledge.
# "Treasury Risk Team" only exists in the ODCS contract.
# "5 business days" only exists in the ODCS freshness SLA.
# "Article 141" / "141" is specific enough to require the ontology.
# "14.83" must appear verbatim — model must cite the actual data value.
# "4.5" alone is too common; require it adjacent to "minimum" or "floor".
RUBRIC = {
    # Must cite the exact value from the database query
    "CET1 ratio value (14.83%)":       lambda a: "14.83" in a,
    # "Article 92" only appears in the OWL ontology — not general LLM knowledge
    "Regulation cited (Basel III Art. 92)": lambda a: any(p in a.lower() for p in
                                               ["article 92", "art. 92", "art 92",
                                                "92(1)", "article 92(1)"]),
    # "Treasury Risk Team" is the exact ODCS owner string — not guessable
    "Owner: Treasury Risk Team":       lambda a: "treasury risk team" in a.lower(),
    # "5 business days" is the exact ODCS freshness SLA — not guessable
    "Freshness SLA (5 business days)": lambda a: any(p in a.lower() for p in
                                           ["5 business day", "five business day",
                                            "p5d", "within 5 business"]),
    # "141" or "dividend/buyback" is specific enough to require the ontology
    "Negative headroom → Art. 141":    lambda a: any(w in a.lower() for w in
                                           ["article 141", "141", "dividend",
                                            "buyback", "bonus restriction",
                                            "distribution restriction"]),
}

# ── Shared SQL tool ───────────────────────────────────────────────
def make_sql_tool(description: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": "query_capital_position",
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {"type": "string",
                            "description": "A valid DuckDB SQL SELECT statement."}
                },
                "required": ["sql"]
            }
        }
    }

# ── Shared mf query tool ──────────────────────────────────────────
def make_mf_tool(description: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": "query_metric",
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Metric names: cet1_ratio, buffer_headroom, cet1_capital, rwa, combined_buffer_requirement"
                    },
                    "group_by": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Dimensions: metric_time__month, entity"
                    }
                },
                "required": ["metrics"]
            }
        }
    }

# ── Execute SQL ───────────────────────────────────────────────────
def run_sql(sql: str) -> str:
    os.chdir(SCRIPT_DIR)
    try:
        con  = duckdb.connect(DB_FILE)
        rows = con.execute(sql).fetchall()
        cols = [d[0] for d in con.description]
        con.close()
        if not rows:
            return "No rows returned."
        header = " | ".join(cols)
        body   = "\n".join(" | ".join(str(v) for v in row) for row in rows)
        return f"{header}\n{'-'*len(header)}\n{body}"
    except Exception as e:
        return f"SQL ERROR: {e}"

# ── Execute mf query ──────────────────────────────────────────────
def run_mf(metrics: list, group_by: list | None = None) -> str:
    cmd = ["mf", "query", "--metrics", ",".join(metrics)]
    if group_by:
        cmd += ["--group-by", ",".join(group_by)]
    try:
        r = subprocess.run(cmd, cwd=DBT_PROJECT, capture_output=True, text=True, timeout=30)
        lines = [l for l in r.stdout.splitlines()
                 if not l.startswith(("⠋","⠙","✔","⠸","⠼","⠹","⠺","⠻"))]
        return "\n".join(lines).strip() or r.stderr.strip()
    except Exception as e:
        return f"mf query ERROR: {e}"

# ── Two-turn agent call ───────────────────────────────────────────
def call_agent(system: str, tool: dict, tool_fn, client: OpenAI) -> str:
    """Run two-turn agent: Turn 1 = tool call, Turn 2 = answer."""
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": QUESTION}
    ]
    r1 = client.chat.completions.create(
        model=OLLAMA_MODEL, messages=messages,
        tools=[tool], tool_choice="auto"
    )
    msg = r1.choices[0].message

    if not msg.tool_calls:
        return msg.content or "(no answer)"

    tc     = msg.tool_calls[0]
    params = json.loads(tc.function.arguments)
    result = tool_fn(params)

    messages += [
        {"role": "assistant", "content": None, "tool_calls": [tc]},
        {"role": "tool",      "content": result, "tool_call_id": tc.id},
        {"role": "user",      "content":
         "Answer the question fully. Include the exact numeric values from the "
         "tool result. Use the context in your system prompt for regulatory details, "
         "ownership, SLA, and consequences. Do not call any tools."}
    ]
    r2 = client.chat.completions.create(
        model=OLLAMA_MODEL, messages=messages,
        tools=[tool], tool_choice="none"
    )
    return r2.choices[0].message.content or "(no answer)"

# ─────────────────────────────────────────────────────────────────
# AGENT 1 — Baseline: schema only
# ─────────────────────────────────────────────────────────────────
def agent_baseline(client: OpenAI) -> str:
    system = (
        "You are a data analyst. Use the SQL tool to query the capital_position table.\n"
        "IMPORTANT: Answer ONLY from the tool result. "
        "Do NOT use any external knowledge about banking, Basel III, regulations, "
        "ownership, SLAs, or industry standards. If the data does not contain it, say so.\n\n"
        "Table: capital_position\n"
        "Columns: reporting_date, entity, cet1_capital_mm, rwa_mm, "
        "cet1_ratio_pct, combined_buffer\n"
        "Latest date: 2026-03-31"
    )
    tool = make_sql_tool("Query the capital_position table in DuckDB.")
    return call_agent(system, tool, lambda p: run_sql(p["sql"]), client)

# ─────────────────────────────────────────────────────────────────
# AGENT 2 — + YAML Data Contract
# ─────────────────────────────────────────────────────────────────
def agent_yaml(client: OpenAI) -> str:
    with open(YAML_CONTRACT) as f:
        contract = yaml.safe_load(f)
    ctx = json.dumps(contract, indent=2)
    system = (
        "You are a data analyst. Use the SQL tool to query the capital_position table.\n"
        "IMPORTANT: Answer ONLY from the tool result and the DATA CONTRACT below. "
        "Do NOT use any external knowledge about Basel III regulations, ownership, "
        "SLAs, or regulatory consequences beyond what is explicitly in the contract.\n\n"
        f"DATA CONTRACT:\n{ctx}"
    )
    tool = make_sql_tool(
        "Query the capital_position table. "
        "The data contract in your system prompt describes the columns."
    )
    return call_agent(system, tool, lambda p: run_sql(p["sql"]), client)

# ─────────────────────────────────────────────────────────────────
# AGENT 3 — + ODCS Governance Contract
# ─────────────────────────────────────────────────────────────────
def agent_odcs(client: OpenAI) -> str:
    with open(ODCS_CONTRACT) as f:
        odcs = yaml.safe_load(f)
    ctx = json.dumps(odcs, indent=2)
    system = (
        "You are a data analyst with access to the full ODCS governance contract. "
        "Use the SQL tool for data. Answer governance questions from the contract.\n\n"
        f"ODCS CONTRACT:\n{ctx}"
    )
    tool = make_sql_tool(
        "Query the capital_position table. "
        "Use the ODCS contract in your system prompt for governance context."
    )
    return call_agent(system, tool, lambda p: run_sql(p["sql"]), client)

# ─────────────────────────────────────────────────────────────────
# AGENT 4 — + OWL/SKOS Ontology
# ─────────────────────────────────────────────────────────────────
def load_ontology() -> str:
    g = Graph()
    g.parse(ONTOLOGY_TTL, format="turtle")
    lines = []
    for cls in g.subjects(RDF.type, OWL.Class):
        label  = g.value(cls, RDFS.label)
        defn   = g.value(cls, SKOS.definition)
        parent = g.value(cls, RDFS.subClassOf)
        minreq = g.value(cls, BFSI.minimumRequirement)
        art    = g.value(cls, BFSI.basedOnArticle)
        col    = g.value(cls, BFSI.columnMapping)
        if not label:
            continue
        b = [f"Concept: {label}"]
        if parent:
            pl = g.value(parent, RDFS.label)
            if pl: b.append(f"  Subclass of : {pl}")
        if defn:   b.append(f"  Definition  : {defn}")
        if minreq: b.append(f"  Min required: {minreq}")
        if art:    b.append(f"  Regulation  : {art}")
        if col:    b.append(f"  DB column   : {col}")
        lines.append("\n".join(b))
    return "\n\n".join(lines)

def agent_ontology(client: OpenAI) -> str:
    with open(ODCS_CONTRACT) as f:
        odcs = yaml.safe_load(f)
    odcs_ctx = json.dumps(odcs, indent=2)
    onto_ctx = load_ontology()
    system = (
        "You are a Basel III capital adequacy analyst. "
        "You have governance context from an ODCS contract AND a formal domain ontology.\n\n"
        f"ODCS CONTRACT:\n{odcs_ctx}\n\n"
        f"OWL/SKOS ONTOLOGY:\n{onto_ctx}"
    )
    tool = make_sql_tool(
        "Query the capital_position table.\n"
        "Use the ODCS contract for governance context and the ontology for domain knowledge.\n"
        "Table: capital_position | Latest date: 2026-03-31\n"
        "Columns: reporting_date, entity, cet1_capital_mm, rwa_mm, cet1_ratio_pct, combined_buffer"
    )
    return call_agent(system, tool, lambda p: run_sql(p["sql"]), client)

# ─────────────────────────────────────────────────────────────────
# AGENT 5 — Full Stack (ODCS + Ontology + Metric Layer)
# ─────────────────────────────────────────────────────────────────
FULL_STACK_TURN2 = (
    "Answer the question completely. You must include:\n"
    "1. The exact CET1 ratio value from the metric query result\n"
    "2. The specific Basel III article that governs the CET1 ratio minimum\n"
    "3. The exact data owner name from the ODCS contract\n"
    "4. The exact freshness SLA (how many business days) from the ODCS contract\n"
    "5. What happens under Basel III Article 141 if buffer headroom turns negative\n"
    "Do not call any tools."
)

def agent_full_stack(client: OpenAI) -> str:
    with open(ODCS_CONTRACT) as f:
        odcs = yaml.safe_load(f)
    odcs_ctx = json.dumps(odcs, indent=2)
    onto_ctx = load_ontology()

    metric_catalogue = textwrap.dedent("""
        Metrics (via dbt MetricFlow — never write raw SQL for these):
          cet1_ratio              — CET1 Ratio (%). Min 4.5% per Basel III Art. 92.
          combined_buffer_requirement — Combined Buffer (%). Basel III Art. 128-131.
          buffer_headroom         — Derived: cet1_ratio - combined_buffer_requirement (pp).
                                    If negative, Basel III Art. 141 restricts dividends/bonuses.
          cet1_capital            — CET1 Capital (MM). Basel III Art. 26-50.
          rwa                     — Risk-Weighted Assets (MM).
        Dimensions: metric_time__month, entity
    """).strip()

    system = (
        "You are a Basel III capital adequacy analyst with access to ALL context layers:\n"
        "1. ODCS governance contract (ownership, certification, SLA)\n"
        "2. OWL/SKOS domain ontology (concept hierarchy, regulatory articles)\n"
        "3. dbt Metric Layer (governed metric definitions)\n\n"
        f"ODCS CONTRACT:\n{odcs_ctx}\n\n"
        f"DOMAIN ONTOLOGY:\n{onto_ctx}\n\n"
        f"METRIC CATALOGUE:\n{metric_catalogue}\n\n"
        "Use the query_metric tool to retrieve metric values. "
        "Answer governance and domain questions directly from the context above."
    )
    tool = make_mf_tool(
        "Query governed business metrics via MetricFlow. "
        "Do NOT write SQL — use metric names instead.\n\n"
        + metric_catalogue
    )

    def tool_fn(params):
        return run_mf(params.get("metrics", []), params.get("group_by"))

    # Use a bespoke Turn 2 that explicitly surfaces all 5 rubric dimensions
    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": QUESTION}
    ]
    r1 = client.chat.completions.create(
        model=OLLAMA_MODEL, messages=messages,
        tools=[tool], tool_choice="auto"
    )
    msg = r1.choices[0].message
    if not msg.tool_calls:
        return msg.content or "(no answer)"

    tc     = msg.tool_calls[0]
    params = json.loads(tc.function.arguments)
    result = tool_fn(params)

    messages += [
        {"role": "assistant", "content": None, "tool_calls": [tc]},
        {"role": "tool",      "content": result, "tool_call_id": tc.id},
        {"role": "user",      "content": FULL_STACK_TURN2}
    ]
    r2 = client.chat.completions.create(
        model=OLLAMA_MODEL, messages=messages,
        tools=[tool], tool_choice="none"
    )
    return r2.choices[0].message.content or "(no answer)"

# ── Scoring ───────────────────────────────────────────────────────
def score(answer: str) -> dict:
    return {k: fn(answer) for k, fn in RUBRIC.items()}

def print_results(results: list[tuple[str, str, dict]]) -> None:
    criteria = list(RUBRIC.keys())
    crit_w   = max(len(c) for c in criteria) + 2
    # Agent column headers — short labels only
    labels = [n.split("—")[1].strip() if "—" in n else n for n in
              [r[0] for r in results]]
    col_w  = max(max(len(l) for l in labels) + 2, 10)

    sep = "═" * (crit_w + (col_w + 2) * len(results) + 4)

    print("\n" + sep)
    print("  CONTEXT ENGINEERING — FULL STACK COMPARISON")
    print(f"  Q: {QUESTION[:90]}...")
    print(sep)

    # Print each agent's answer (abbreviated)
    for name, answer, scores in results:
        total = sum(scores.values())
        print(f"\n  ── {name}  [{total}/{len(RUBRIC)}] ──")
        for line in textwrap.wrap(answer[:600], width=100):
            print(f"     {line}")
        if len(answer) > 600:
            print("     [... truncated]")

    # Scoring table
    print("\n" + sep)
    print("  SCORING — which parts each context layer answered")
    print(sep)

    # Header row
    hdr = f"  {'Criterion':<{crit_w}}"
    for label in labels:
        hdr += f"  {label:<{col_w}}"
    print(hdr)
    print(f"  {'-'*crit_w}" + (f"  {'-'*col_w}" * len(results)))

    # Criteria rows
    for criterion in criteria:
        row = f"  {criterion:<{crit_w}}"
        for _, _, scores in results:
            mark = "✅" if scores[criterion] else "❌"
            row += f"  {mark:<{col_w}}"
        print(row)

    # Total row
    print(f"  {'-'*crit_w}" + (f"  {'-'*col_w}" * len(results)))
    tot_row = f"  {'TOTAL':<{crit_w}}"
    for _, _, scores in results:
        total = sum(scores.values())
        tot_row += f"  {total}/{len(RUBRIC):<{col_w-2}}"
    print(tot_row)
    print(sep)

# ── Main ──────────────────────────────────────────────────────────
def main() -> None:
    os.chdir(SCRIPT_DIR)

    missing = []
    for label, path in [
        ("YAML contract",   YAML_CONTRACT),
        ("ODCS contract",   ODCS_CONTRACT),
        ("OWL ontology",    ONTOLOGY_TTL),
        ("dbt project",     DBT_PROJECT),
        ("DuckDB",          DB_FILE),
    ]:
        if not os.path.exists(path):
            missing.append(f"  {label}: {path}")
    if missing:
        print("ERROR — missing prerequisites:\n" + "\n".join(missing))
        print("\nRun: python3 bootstrap_full_stack.py")
        sys.exit(1)

    client = OpenAI(base_url=OLLAMA_BASE, api_key="ollama")

    agents = [
        ("Agent 1 — Baseline (schema only)",          agent_baseline),
        ("Agent 2 — + YAML Data Contract",            agent_yaml),
        ("Agent 3 — + ODCS Governance Contract",      agent_odcs),
        ("Agent 4 — + OWL/SKOS Domain Ontology",      agent_ontology),
        ("Agent 5 — Full Stack (all layers)",          agent_full_stack),
    ]

    results = []
    for name, fn in agents:
        print(f"\n▶ Running {name} ...")
        try:
            answer = fn(client)
            scores = score(answer)
            total  = sum(scores.values())
            print(f"  Score: {total}/{len(RUBRIC)}")
            results.append((name, answer, scores))
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append((name, f"ERROR: {e}", {k: False for k in RUBRIC}))

    print_results(results)

if __name__ == "__main__":
    main()
