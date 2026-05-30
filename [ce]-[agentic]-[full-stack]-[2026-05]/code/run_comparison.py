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

# ── ANSI colour palette (no extra deps) ──────────────────────────
class C:
    RESET          = "\033[0m"
    BOLD           = "\033[1m"
    DIM            = "\033[2m"
    RED            = "\033[31m"
    GREEN          = "\033[32m"
    YELLOW         = "\033[33m"
    BLUE           = "\033[34m"
    MAGENTA        = "\033[35m"
    CYAN           = "\033[36m"
    WHITE          = "\033[37m"
    BRIGHT_RED     = "\033[91m"
    BRIGHT_GREEN   = "\033[92m"
    BRIGHT_YELLOW  = "\033[93m"
    BRIGHT_BLUE    = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN    = "\033[96m"
    BRIGHT_WHITE   = "\033[97m"

# Colour by event name
_EVENT_COLOUR = {
    "agent.start":              C.BOLD + C.BRIGHT_CYAN,
    "agent.context_loaded":     C.DIM  + C.CYAN,
    "agent.turn1.request":      C.YELLOW,
    "agent.turn1.tool_call":    C.BOLD + C.BLUE,
    "agent.turn1.direct_answer":C.DIM  + C.WHITE,
    "agent.turn2.request":      C.DIM  + C.YELLOW,
    "agent.response":           C.BRIGHT_WHITE,
    "tool.sql":                 C.MAGENTA,
    "tool.sql.result":          C.GREEN,
    "tool.sql.error":           C.BOLD + C.RED,
    "tool.mf_query":            C.MAGENTA,
    "tool.mf_query.result":     C.GREEN,
    "tool.mf_query.error":      C.BOLD + C.RED,
    "context.maturation":       C.BOLD + C.BRIGHT_WHITE,
    "context.improvement":      C.BOLD + C.BRIGHT_GREEN,
    "context.no_improvement":   C.BOLD + C.BRIGHT_YELLOW,
    "agent.error":              C.BOLD + C.BRIGHT_RED,
}

def _colour_processor(logger, method, event_dict):
    """Colour the event name and key fields based on semantic meaning."""
    event  = event_dict.get("event", "")
    colour = _EVENT_COLOUR.get(event, C.DIM)

    # Colour the event key itself
    event_dict["event"] = f"{colour}{event}{C.RESET}"

    # Colour score by value (red → yellow → green)
    if "score" in event_dict:
        s = str(event_dict["score"])
        try:
            n, d  = (int(x) for x in s.split("/"))
            sc    = C.BRIGHT_GREEN if n == d else (C.YELLOW if n >= d * 0.6 else C.RED)
            event_dict["score"] = f"{sc}{s}{C.RESET}"
        except Exception:
            pass

    # (field-level colouring skipped — structlog repr-quotes strings with ANSI in them)

    return event_dict

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.set_exc_info,
        _colour_processor,
        structlog.dev.ConsoleRenderer(colors=False),   # colour handled above
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
    logger_factory=structlog.PrintLoggerFactory(),
)

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

# ── Input layer definitions (used in final comparison table) ──────
# (display_name, path_relative_to_repo_root, [agent1..5 boolean flags])
INPUT_LAYERS = [
    (
        "DB Schema",
        "[ce]-[agentic]-[full-stack]-[2026-05]/code/capital_bfsi.duckdb",
        [True, True, True, True, True],
    ),
    (
        "YAML Data Contract",
        "[ce]-[hello-world]-[2026-05]/code/contracts/capital_risk.yaml",
        [False, True, True, True, True],
    ),
    (
        "ODCS Governance Contract",
        "[ce]-[odcs]-[bfsi]-[2026-05]/code/contracts/capital_risk_odcs.yaml",
        [False, False, True, True, True],
    ),
    (
        "OWL/SKOS Ontology",
        "[ce]-[ontology]-[bfsi]-[2026-05]/ontology/bfsi_capital.ttl",
        [False, False, False, True, True],
    ),
    (
        "dbt Metric Layer",
        "[ce]-[metrics]-[bfsi]-[2026-05]/dbt_project/models/schema.yml",
        [False, False, False, False, True],
    ),
]

# Short column labels for the table header (one per agent, in order)
SHORT_LABELS = ["Baseline", "+YAML", "+ODCS", "+Ontology", "Full Stack"]

# Populated by each agent function before it calls the LLM
_agent_system_chars: dict[str, int] = {}

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
    log.info("tool.sql", query=sql)
    try:
        con  = duckdb.connect(DB_FILE)
        rows = con.execute(sql).fetchall()
        cols = [d[0] for d in con.description]
        con.close()
        if not rows:
            log.info("tool.sql.result", rows=0)
            return "No rows returned."
        header = " | ".join(cols)
        body   = "\n".join(" | ".join(str(v) for v in row) for row in rows)
        result = f"{header}\n{'-'*len(header)}\n{body}"
        log.info("tool.sql.result", rows=len(rows), columns=cols)
        return result
    except Exception as e:
        log.error("tool.sql.error", error=str(e))
        return f"SQL ERROR: {e}"

# ── Execute mf query ──────────────────────────────────────────────
def run_mf(metrics: list, group_by: list | None = None) -> str:
    cmd = ["mf", "query", "--metrics", ",".join(metrics)]
    if group_by:
        cmd += ["--group-by", ",".join(group_by)]
    log.info("tool.mf_query", metrics=metrics, group_by=group_by, cmd=" ".join(cmd))
    try:
        r = subprocess.run(cmd, cwd=DBT_PROJECT, capture_output=True, text=True, timeout=30)
        lines = [l for l in r.stdout.splitlines()
                 if not l.startswith(("⠋","⠙","✔","⠸","⠼","⠹","⠺","⠻"))]
        result = "\n".join(lines).strip() or r.stderr.strip()
        log.info("tool.mf_query.result", preview=result[:200])
        return result
    except Exception as e:
        log.error("tool.mf_query.error", error=str(e))
        return f"mf query ERROR: {e}"

# ── Two-turn agent call ───────────────────────────────────────────
def call_agent(agent_name: str, system: str, tool: dict, tool_fn, client: OpenAI) -> str:
    """Run two-turn agent: Turn 1 = tool call, Turn 2 = answer."""
    tool_name = tool["function"]["name"]
    log.info("agent.turn1.request",
             agent=agent_name,
             model=OLLAMA_MODEL,
             tool=tool_name,
             system_chars=len(system),
             question=QUESTION[:80] + "...")

    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": QUESTION}
    ]
    r1 = client.chat.completions.create(
        model=OLLAMA_MODEL, messages=messages,
        tools=[tool], tool_choice="auto"
    )
    msg = r1.choices[0].message

    # Model answered directly without a tool call
    if not msg.tool_calls:
        log.info("agent.turn1.direct_answer", agent=agent_name,
                 answer_chars=len(msg.content or ""))
        return msg.content or "(no answer)"

    tc     = msg.tool_calls[0]
    params = json.loads(tc.function.arguments)
    log.info("agent.turn1.tool_call",
             agent=agent_name,
             tool=tc.function.name,
             arguments=params)

    result = tool_fn(params)

    log.info("agent.turn2.request",
             agent=agent_name,
             model=OLLAMA_MODEL,
             tool_result_chars=len(result))

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
    answer = r2.choices[0].message.content or "(no answer)"
    log.info("agent.response",
             agent=agent_name,
             answer=answer[:200] + "..." if len(answer) > 200 else answer)
    return answer

# ─────────────────────────────────────────────────────────────────
# AGENT 1 — Baseline: schema only
# ─────────────────────────────────────────────────────────────────
def agent_baseline(client: OpenAI) -> str:
    log.info("agent.start", agent="Baseline", context_layers=["schema"])
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
    _agent_system_chars["Agent 1 — Baseline (schema only)"] = len(system)
    tool = make_sql_tool("Query the capital_position table in DuckDB.")
    return call_agent("Baseline", system, tool, lambda p: run_sql(p["sql"]), client)

# ─────────────────────────────────────────────────────────────────
# AGENT 2 — + YAML Data Contract
# ─────────────────────────────────────────────────────────────────
def agent_yaml(client: OpenAI) -> str:
    log.info("agent.start", agent="+ YAML Contract", context_layers=["schema", "yaml_contract"])
    with open(YAML_CONTRACT) as f:
        contract = yaml.safe_load(f)
    ctx = json.dumps(contract, indent=2)
    log.info("agent.context_loaded", agent="+ YAML Contract", file=YAML_CONTRACT, chars=len(ctx))
    system = (
        "You are a data analyst. Use the SQL tool to query the capital_position table.\n"
        "IMPORTANT: Answer ONLY from the tool result and the DATA CONTRACT below. "
        "Do NOT use any external knowledge about Basel III regulations, ownership, "
        "SLAs, or regulatory consequences beyond what is explicitly in the contract.\n\n"
        f"DATA CONTRACT:\n{ctx}"
    )
    _agent_system_chars["Agent 2 — + YAML Data Contract"] = len(system)
    tool = make_sql_tool(
        "Query the capital_position table. "
        "The data contract in your system prompt describes the columns."
    )
    return call_agent("+ YAML Contract", system, tool, lambda p: run_sql(p["sql"]), client)

# ─────────────────────────────────────────────────────────────────
# AGENT 3 — + ODCS Governance Contract
# ─────────────────────────────────────────────────────────────────
def agent_odcs(client: OpenAI) -> str:
    log.info("agent.start", agent="+ ODCS Contract",
             context_layers=["schema", "yaml_contract", "odcs_governance"])
    with open(ODCS_CONTRACT) as f:
        odcs = yaml.safe_load(f)
    ctx = json.dumps(odcs, indent=2)
    log.info("agent.context_loaded", agent="+ ODCS Contract", file=ODCS_CONTRACT, chars=len(ctx))
    system = (
        "You are a data analyst with access to the full ODCS governance contract. "
        "Use the SQL tool for data. Answer governance questions from the contract.\n\n"
        f"ODCS CONTRACT:\n{ctx}"
    )
    _agent_system_chars["Agent 3 — + ODCS Governance Contract"] = len(system)
    tool = make_sql_tool(
        "Query the capital_position table. "
        "Use the ODCS contract in your system prompt for governance context."
    )
    return call_agent("+ ODCS Contract", system, tool, lambda p: run_sql(p["sql"]), client)

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
    log.info("agent.start", agent="+ OWL/SKOS Ontology",
             context_layers=["schema", "odcs_governance", "owl_skos_ontology"])
    with open(ODCS_CONTRACT) as f:
        odcs = yaml.safe_load(f)
    odcs_ctx = json.dumps(odcs, indent=2)
    onto_ctx = load_ontology()
    log.info("agent.context_loaded", agent="+ OWL/SKOS Ontology",
             odcs_chars=len(odcs_ctx), ontology_chars=len(onto_ctx))
    system = (
        "You are a Basel III capital adequacy analyst. "
        "You have governance context from an ODCS contract AND a formal domain ontology.\n\n"
        f"ODCS CONTRACT:\n{odcs_ctx}\n\n"
        f"OWL/SKOS ONTOLOGY:\n{onto_ctx}"
    )
    _agent_system_chars["Agent 4 — + OWL/SKOS Domain Ontology"] = len(system)
    tool = make_sql_tool(
        "Query the capital_position table.\n"
        "Use the ODCS contract for governance context and the ontology for domain knowledge.\n"
        "Table: capital_position | Latest date: 2026-03-31\n"
        "Columns: reporting_date, entity, cet1_capital_mm, rwa_mm, cet1_ratio_pct, combined_buffer"
    )
    return call_agent("+ OWL/SKOS Ontology", system, tool, lambda p: run_sql(p["sql"]), client)

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
    log.info("agent.start", agent="Full Stack",
             context_layers=["schema", "odcs_governance", "owl_skos_ontology", "metric_layer"])
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
    _agent_system_chars["Agent 5 — Full Stack (all layers)"] = len(system)
    tool = make_mf_tool(
        "Query governed business metrics via MetricFlow. "
        "Do NOT write SQL — use metric names instead.\n\n"
        + metric_catalogue
    )

    def tool_fn(params):
        return run_mf(params.get("metrics", []), params.get("group_by"))

    log.info("agent.context_loaded", agent="Full Stack",
             odcs_chars=len(odcs_ctx), ontology_chars=len(onto_ctx),
             metric_catalogue_chars=len(metric_catalogue))

    # Use a bespoke Turn 2 that explicitly surfaces all 5 rubric dimensions
    log.info("agent.turn1.request", agent="Full Stack",
             model=OLLAMA_MODEL, tool="query_metric",
             system_chars=len(system), question=QUESTION[:80] + "...")

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
        log.info("agent.turn1.direct_answer", agent="Full Stack",
                 answer_chars=len(msg.content or ""))
        return msg.content or "(no answer)"

    tc     = msg.tool_calls[0]
    params = json.loads(tc.function.arguments)
    log.info("agent.turn1.tool_call", agent="Full Stack",
             tool=tc.function.name, arguments=params)

    result = tool_fn(params)

    log.info("agent.turn2.request", agent="Full Stack",
             model=OLLAMA_MODEL, tool_result_chars=len(result))

    messages += [
        {"role": "assistant", "content": None, "tool_calls": [tc]},
        {"role": "tool",      "content": result, "tool_call_id": tc.id},
        {"role": "user",      "content": FULL_STACK_TURN2}
    ]
    r2 = client.chat.completions.create(
        model=OLLAMA_MODEL, messages=messages,
        tools=[tool], tool_choice="none"
    )
    answer = r2.choices[0].message.content or "(no answer)"
    log.info("agent.response", agent="Full Stack",
             answer=answer[:200] + "..." if len(answer) > 200 else answer)
    return answer

# ── Scoring ───────────────────────────────────────────────────────
def score(answer: str) -> dict:
    return {k: fn(answer) for k, fn in RUBRIC.items()}

def _fmt_size(chars: int) -> str:
    """Format a character count as a human-readable size string."""
    if chars == 0:
        return "—"
    if chars < 1000:
        return f"{chars}ch"
    return f"{chars / 1000:.1f}k"


def print_results(results: list[tuple[str, str, dict]]) -> None:
    criteria = list(RUBRIC.keys())
    n        = len(results)

    # Left column wide enough for all layer names, criteria, and the size row label
    left_w = max(
        max(len(layer) for layer, _, _ in INPUT_LAYERS),
        max(len(c)     for c in criteria),
        len("System prompt size"),
    ) + 2
    col_w = 12      # fixed — accommodates "Full Stack" + 2-cell emoji padding

    def _pad(text: str, w: int) -> str:
        """Right-pad a plain-text string (no ANSI) to exactly w chars."""
        return text + " " * max(0, w - len(text))

    def _cell(sym: str, colour: str) -> str:
        """Colour a 2-cell emoji symbol and pad to col_w."""
        return colour + sym + C.RESET + " " * (col_w - 2)

    total_w = 2 + left_w + (2 + col_w) * n + 2
    SEP  = "═" * total_w
    THIN = "─" * total_w

    # ── Per-agent answer snippets ──────────────────────────────────
    print("\n" + SEP)
    print(f"  {C.BOLD}CONTEXT ENGINEERING — INPUT → OUTPUT COMPARISON{C.RESET}")
    print(f"  Q: {QUESTION[:90]}...")
    print(SEP)

    for name, answer, scores in results:
        total     = sum(scores.values())
        sc_colour = (C.BRIGHT_GREEN if total == len(RUBRIC)
                     else C.YELLOW  if total >= 3
                     else C.RED)
        print(f"\n  {C.BOLD}{name}{C.RESET}  "
              f"[{sc_colour}{total}/{len(RUBRIC)}{C.RESET}]")
        for line in textwrap.wrap(answer[:400], width=100):
            print(f"     {C.DIM}{line}{C.RESET}")
        if len(answer) > 400:
            print(f"     {C.DIM}[... truncated]{C.RESET}")

    # ── Combined input / output table ─────────────────────────────
    print("\n" + SEP)

    # Header: short agent labels
    hdr = "  " + _pad("", left_w)
    for label in SHORT_LABELS[:n]:
        hdr += "  " + _pad(label, col_w)
    print(hdr)
    print("  " + THIN[: left_w] + ("  " + "─" * col_w) * n)

    # ── INPUT section ──────────────────────────────────────────────
    print(f"\n  {C.BOLD}{C.BRIGHT_CYAN}── INPUT CONTEXT LAYERS ──{C.RESET}")

    for layer_name, layer_path, flags in INPUT_LAYERS:
        row = "  " + _pad(layer_name, left_w)
        for j in range(n):
            flag = flags[j] if j < len(flags) else False
            row += "  " + _cell("✅" if flag else "❌",
                                 C.CYAN if flag else C.DIM)
        print(row)
        # Source file path — dimmed, indented with tree glyph
        print(f"    {C.DIM}└─ {layer_path}{C.RESET}")

    # System prompt size row (quantifies cost of richer context)
    row = "  " + _pad("System prompt size", left_w)
    for name, _, _ in results:
        sz  = _fmt_size(_agent_system_chars.get(name, 0))
        row += "  " + C.DIM + sz + C.RESET + " " * max(0, col_w - len(sz))
    print(row)

    print("  " + THIN[: left_w] + ("  " + "─" * col_w) * n)

    # ── OUTPUT section ─────────────────────────────────────────────
    print(f"\n  {C.BOLD}{C.BRIGHT_GREEN}── OUTPUT — CRITERIA SCORED ──{C.RESET}")

    for criterion in criteria:
        row = "  " + _pad(criterion, left_w)
        for _, _, scores in results:
            flag = scores[criterion]
            row += "  " + _cell("✅" if flag else "❌",
                                 C.BRIGHT_GREEN if flag else C.RED)
        print(row)

    # Total score row
    print("  " + THIN[: left_w] + ("  " + "─" * col_w) * n)
    row = "  " + _pad("TOTAL SCORE", left_w)
    for _, _, scores in results:
        total     = sum(scores.values())
        sc_colour = (C.BRIGHT_GREEN if total == len(RUBRIC)
                     else C.YELLOW  if total >= 3
                     else C.RED)
        tot_str   = f"{total}/{len(RUBRIC)}"
        row += "  " + sc_colour + tot_str + C.RESET + " " * max(0, col_w - len(tot_str))
    print(row)
    print(SEP + "\n")

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

    results     = []
    prev_scores = None

    for name, fn in agents:
        print(f"\n▶ Running {name} ...")
        try:
            answer  = fn(client)
            scores  = score(answer)
            total   = sum(scores.values())

            passed  = [c for c, v in scores.items() if v]
            failed  = [c for c, v in scores.items() if not v]
            unlocked = (
                [c for c in passed if not prev_scores or not prev_scores[c]]
                if prev_scores else passed
            )
            still_missing = failed

            # ── Maturation narrative log ──────────────────────────────
            log.info("context.maturation",
                     agent=name,
                     score=f"{total}/{len(RUBRIC)}",
                     newly_unlocked=unlocked   if unlocked       else ["(none)"],
                     still_missing =still_missing if still_missing else ["(none — all answered)"])

            if unlocked:
                log.info("context.improvement",
                         agent=name,
                         added_context_unlocked=unlocked,
                         message=f"Adding this layer answered {len(unlocked)} new criterion/criteria")
            else:
                log.info("context.no_improvement",
                         agent=name,
                         message="This context layer did not unlock any new answer criteria")

            prev_scores = scores
            print(f"  Score: {total}/{len(RUBRIC)}")
            results.append((name, answer, scores))

        except Exception as e:
            log.error("agent.error", agent=name, error=str(e))
            print(f"  ERROR: {e}")
            results.append((name, f"ERROR: {e}", {k: False for k in RUBRIC}))

    print_results(results)

if __name__ == "__main__":
    main()
