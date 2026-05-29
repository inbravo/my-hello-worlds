"""
CE Example 8 — OWL/SKOS Ontology Agent (Ollama / qwen2.5)

What this demo adds over Example 4 (ODCS):
  - The context is not a hand-crafted YAML or data contract.
  - It is a formal OWL/SKOS ontology in Turtle format, parsed by rdflib.
  - The agent understands the concept hierarchy (CET1 ⊂ Tier1 ⊂ Regulatory Capital),
    formulas, regulatory article references, column-to-concept mappings, and
    minimum requirements — all extracted from the ontology at runtime.
  - It can answer both data questions (via DuckDB) AND domain knowledge
    questions (from the ontology) in a single turn.

Run order:
    python bootstrap_ontology.py
    python agent_ontology_ollama.py

Usage:
    python agent_ontology_ollama.py
    python agent_ontology_ollama.py "Is CET1 Capital a subset of Tier 1 Capital?"
"""
# ─────────────────────────────────────────────────────
# Author   : Amit Dixit
# GitHub   : https://github.com/inbravo
# Web      : https://inbravo.github.io
# LinkedIn : https://www.linkedin.com/in/amitnoida/
# ─────────────────────────────────────────────────────

import os
import sys
import json
import textwrap
import duckdb
import structlog
from openai import OpenAI
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from rdflib.namespace import SKOS, XSD

log = structlog.get_logger()

# ── Config ────────────────────────────────────────────────────────
OLLAMA_BASE   = "http://localhost:11434/v1"
OLLAMA_MODEL  = "qwen2.5"
DB_FILE       = "capital_bfsi.duckdb"
ONTOLOGY_FILE = "../ontology/bfsi_capital.ttl"
BFSI          = Namespace("https://github.com/inbravo/ce-series/ontology/bfsi#")
REG           = Namespace("https://github.com/inbravo/ce-series/ontology/regulation#")

DEFAULT_QUESTION = (
    "What is our current CET1 ratio and how much headroom do we have "
    "above the Basel III combined buffer requirement?"
)

# ── 1. Load and parse the OWL/SKOS ontology ──────────────────────
def load_ontology(ttl_path: str) -> str:
    """Parse the Turtle ontology and build a structured context string."""
    g = Graph()
    g.parse(ttl_path, format="turtle")

    lines = ["=== BFSI Capital Adequacy Ontology (OWL/SKOS) ===\n"]

    # Extract all named classes with their labels, definitions, and properties
    for cls in g.subjects(RDF.type, OWL.Class):
        label = g.value(cls, RDFS.label)
        if not label:
            continue

        defn      = g.value(cls, SKOS.definition)
        alt_label = g.value(cls, SKOS.altLabel)
        parent    = g.value(cls, RDFS.subClassOf)
        formula   = g.value(cls, BFSI.formula)
        minimum   = g.value(cls, BFSI.minimumRequirement)
        article   = g.value(cls, BFSI.basedOnArticle)
        gov_by    = g.value(cls, BFSI.governedBy)
        col_map   = g.value(cls, BFSI.columnMapping)
        unit      = g.value(cls, BFSI.unit)
        fixed_rate= g.value(cls, BFSI.fixedRate)

        block = [f"Concept: {label}"]
        if alt_label:
            block.append(f"  Alias       : {alt_label}")
        if parent:
            parent_label = g.value(parent, RDFS.label)
            if parent_label:
                block.append(f"  Subclass of : {parent_label}")
        if defn:
            block.append(f"  Definition  : {defn}")
        if formula:
            block.append(f"  Formula     : {formula}")
        if minimum:
            block.append(f"  Min required: {minimum} (Basel III regulatory floor)")
        if fixed_rate:
            block.append(f"  Fixed rate  : {fixed_rate}")
        if article:
            block.append(f"  Regulation  : {article}")
        if gov_by:
            reg_label = g.value(gov_by, RDFS.label)
            if reg_label:
                block.append(f"  Governed by : {reg_label}")
        if col_map:
            block.append(f"  DB column   : {col_map}")
        if unit:
            block.append(f"  Unit        : {unit}")
        lines.append("\n".join(block))

    # Extract regulations
    lines.append("\n=== Regulations Referenced ===")
    for ind in g.subjects(RDF.type, OWL.NamedIndividual):
        label = g.value(ind, RDFS.label)
        defn  = g.value(ind, SKOS.definition)
        pub   = g.value(ind, BFSI.publisher)
        eff   = g.value(ind, BFSI.effectiveDate)
        if label:
            block = [f"Regulation: {label}"]
            if defn:  block.append(f"  Definition  : {defn}")
            if pub:   block.append(f"  Publisher   : {pub}")
            if eff:   block.append(f"  Effective   : {eff}")
            lines.append("\n".join(block))

    # Column-to-concept mapping summary
    lines.append("\n=== DB Column → Ontology Concept Mapping ===")
    for s in g.subjects(BFSI.columnMapping, None):
        col   = g.value(s, BFSI.columnMapping)
        label = g.value(s, RDFS.label)
        if col and label:
            lines.append(f"  {str(col):<25} → {label}")

    return "\n\n".join(lines)


# ── 2. Build the SQL tool with ontology-enriched description ──────
def build_tool(ontology_context: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name": "query_capital_position",
            "description": textwrap.dedent(f"""
                Execute a SQL query against the capital_position table in DuckDB.

                Table: capital_position
                Columns:
                  reporting_date  DATE      — quarter-end date (2025-09-30, 2025-12-31, 2026-03-31)
                  entity          VARCHAR   — legal entity (BANK_HOLDCO)
                  cet1_capital_mm DECIMAL   — CET1 Capital in millions
                  rwa_mm          DECIMAL   — Risk-Weighted Assets in millions
                  cet1_ratio_pct  DECIMAL   — CET1 Ratio as percentage
                  combined_buffer DECIMAL   — Combined Buffer Requirement as percentage

                Latest reporting date: 2026-03-31

                ── DOMAIN ONTOLOGY CONTEXT ──────────────────────────────────
                {ontology_context}
                ─────────────────────────────────────────────────────────────

                Use this ontology to:
                - Understand what each column represents in regulatory terms
                - Answer governance and conceptual questions from the definitions above
                - Compute buffer headroom as: cet1_ratio_pct - combined_buffer
                - Reference the correct Basel III article when explaining requirements
            """).strip(),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "A valid DuckDB SQL SELECT statement."
                    }
                },
                "required": ["sql"]
            }
        }
    }


# ── 3. Execute SQL against DuckDB ────────────────────────────────
def run_sql(sql: str) -> str:
    log.info("ontology.sql", sql=sql)
    try:
        con = duckdb.connect(DB_FILE)
        rows = con.execute(sql).fetchall()
        cols = [d[0] for d in con.description]
        con.close()
        if not rows:
            return "No rows returned."
        header = " | ".join(cols)
        sep    = "-" * len(header)
        body   = "\n".join(" | ".join(str(v) for v in row) for row in rows)
        return f"{header}\n{sep}\n{body}"
    except Exception as e:
        return f"SQL ERROR: {e}"


# ── 4. Two-turn agent loop ────────────────────────────────────────
def ask(question: str, tool: dict, client: OpenAI) -> None:
    log.info("ontology.question", q=question)

    # ── Turn 1: LLM decides query ──
    t1_messages = [
        {
            "role": "system",
            "content": (
                "You are a Basel III capital adequacy analyst with deep knowledge of "
                "the BFSI domain ontology provided in your tool description. "
                "Use the tool to query live data when needed. "
                "For purely conceptual questions (hierarchy, formulas, regulations), "
                "you may answer from the ontology context without querying."
            )
        },
        {"role": "user", "content": question}
    ]

    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=t1_messages,
        tools=[tool],
        tool_choice="auto"
    )
    msg = response.choices[0].message

    # Guard: model answered directly without a tool call
    if not msg.tool_calls:
        print("\n" + "=" * 60)
        print(msg.content)
        print("=" * 60)
        return

    tool_call = msg.tool_calls[0]
    params    = json.loads(tool_call.function.arguments)
    sql       = params.get("sql", "")
    result    = run_sql(sql)
    log.info("ontology.result", rows=result[:200])

    # ── Turn 2: LLM synthesises answer ──
    t2_messages = t1_messages + [
        {"role": "assistant",  "content": None, "tool_calls": [tool_call]},
        {"role": "tool",       "content": result, "tool_call_id": tool_call.id},
        {
            "role": "user",
            "content": (
                "Using the query result above and the ontology context in your tool description, "
                "answer the question in plain English. "
                "Reference the relevant Basel III articles, formulas, and regulatory thresholds where appropriate. "
                "Do not call any tools."
            )
        }
    ]

    final  = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=t2_messages,
        tools=[tool],
        tool_choice="none"
    )
    answer = final.choices[0].message.content

    # Guard: model issued a second tool call
    if not answer and final.choices[0].message.tool_calls:
        answer = "(Model issued a second tool call instead of answering — try a simpler question.)"
    if not answer:
        answer = "(No answer generated.)"

    print("\n" + "=" * 60)
    print(answer)
    print("=" * 60)


# ── 5. Main ───────────────────────────────────────────────────────
def main() -> None:
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_QUESTION

    # Resolve paths relative to this script
    script_dir    = os.path.dirname(os.path.abspath(__file__))
    ontology_path = os.path.join(script_dir, ONTOLOGY_FILE)
    db_path       = os.path.join(script_dir, DB_FILE)

    if not os.path.exists(ontology_path):
        print(f"ERROR: ontology not found at {ontology_path}")
        sys.exit(1)
    if not os.path.exists(db_path):
        print(f"ERROR: {db_path} not found — run bootstrap_ontology.py first.")
        sys.exit(1)

    # Change to script dir so DuckDB opens the local file
    os.chdir(script_dir)

    log.info("ontology.load", path=ontology_path)
    ontology_context = load_ontology(ontology_path)
    tool   = build_tool(ontology_context)
    client = OpenAI(base_url=OLLAMA_BASE, api_key="ollama")

    ask(question, tool, client)


if __name__ == "__main__":
    main()
