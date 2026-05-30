"""
CE Example 8 — OWL/SKOS Ontology Agent (Anthropic Claude)

Parses the BFSI capital adequacy OWL/SKOS ontology at runtime using rdflib,
injects the full concept hierarchy and regulatory context into the tool
description, and answers both data and domain knowledge questions.

Usage:
    export ANTHROPIC_API_KEY=your_key
    python bootstrap_ontology.py
    python agent_ontology.py
    python agent_ontology.py "Is CET1 Capital a subset of Tier 1 Capital?"
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
import duckdb
import structlog
import anthropic
from rdflib import Graph, Namespace, RDF, RDFS, OWL
from rdflib.namespace import SKOS

log = structlog.get_logger()

MODEL         = "claude-opus-4-5"
DB_FILE       = "capital_bfsi.duckdb"
ONTOLOGY_FILE = "../ontology/bfsi_capital.ttl"
BFSI          = Namespace("https://github.com/inbravo/ce-series/ontology/bfsi#")
REG           = Namespace("https://github.com/inbravo/ce-series/ontology/regulation#")

DEFAULT_QUESTION = (
    "What is our current CET1 ratio and how much headroom do we have "
    "above the Basel III combined buffer requirement?"
)


def load_ontology(ttl_path: str) -> str:
    g = Graph()
    g.parse(ttl_path, format="turtle")

    lines = ["=== BFSI Capital Adequacy Ontology (OWL/SKOS) ===\n"]

    for cls in g.subjects(RDF.type, OWL.Class):
        label = g.value(cls, RDFS.label)
        if not label:
            continue
        defn       = g.value(cls, SKOS.definition)
        alt_label  = g.value(cls, SKOS.altLabel)
        parent     = g.value(cls, RDFS.subClassOf)
        formula    = g.value(cls, BFSI.formula)
        minimum    = g.value(cls, BFSI.minimumRequirement)
        article    = g.value(cls, BFSI.basedOnArticle)
        gov_by     = g.value(cls, BFSI.governedBy)
        col_map    = g.value(cls, BFSI.columnMapping)
        unit       = g.value(cls, BFSI.unit)
        fixed_rate = g.value(cls, BFSI.fixedRate)

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
            block.append(f"  Min required: {minimum}")
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

    lines.append("\n=== Regulations Referenced ===")
    for ind in g.subjects(RDF.type, OWL.NamedIndividual):
        label = g.value(ind, RDFS.label)
        defn  = g.value(ind, SKOS.definition)
        pub   = g.value(ind, BFSI.publisher)
        if label:
            block = [f"Regulation: {label}"]
            if defn: block.append(f"  Definition  : {defn}")
            if pub:  block.append(f"  Publisher   : {pub}")
            lines.append("\n".join(block))

    lines.append("\n=== DB Column → Ontology Concept Mapping ===")
    for s in g.subjects(BFSI.columnMapping, None):
        col   = g.value(s, BFSI.columnMapping)
        label = g.value(s, RDFS.label)
        if col and label:
            lines.append(f"  {str(col):<25} → {label}")

    return "\n\n".join(lines)


def build_tool(ontology_context: str) -> dict:
    return {
        "name": "query_capital_position",
        "description": textwrap.dedent(f"""
            Execute a SQL query against the capital_position table in DuckDB.

            Table: capital_position
            Columns:
              reporting_date  DATE      — quarter-end date
              entity          VARCHAR   — legal entity (BANK_HOLDCO)
              cet1_capital_mm DECIMAL   — CET1 Capital in millions
              rwa_mm          DECIMAL   — Risk-Weighted Assets in millions
              cet1_ratio_pct  DECIMAL   — CET1 Ratio as percentage
              combined_buffer DECIMAL   — Combined Buffer Requirement as percentage

            Latest reporting date: 2026-03-31

            ── DOMAIN ONTOLOGY CONTEXT ──────────────────────────────────
            {ontology_context}
            ─────────────────────────────────────────────────────────────
        """).strip(),
        "input_schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string", "description": "A valid DuckDB SQL SELECT statement."}
            },
            "required": ["sql"]
        }
    }


def run_sql(sql: str) -> str:
    log.info("ontology.sql", sql=sql)
    try:
        con  = duckdb.connect(DB_FILE)
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


def ask(question: str, tool: dict, client: anthropic.Anthropic) -> None:
    log.info("ontology.question", q=question)

    messages = [{"role": "user", "content": question}]

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=(
            "You are a Basel III capital adequacy analyst with deep knowledge of "
            "the BFSI domain ontology provided in your tool description. "
            "Use the tool for data queries. Answer conceptual questions from the ontology context."
        ),
        tools=[tool],
        messages=messages
    )

    # Check for tool use
    tool_use_block = next((b for b in response.content if b.type == "tool_use"), None)

    if not tool_use_block:
        # Direct answer from ontology context
        text = next((b.text for b in response.content if hasattr(b, "text")), "")
        print("\n" + "=" * 60)
        print(text)
        print("=" * 60)
        return

    sql    = tool_use_block.input.get("sql", "")
    result = run_sql(sql)
    log.info("ontology.result", rows=result[:200])

    messages += [
        {"role": "assistant", "content": response.content},
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tool_use_block.id, "content": result}
        ]}
    ]

    final = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=(
            "You are a Basel III capital adequacy analyst. "
            "Answer the question using both the query result and the ontology context. "
            "Reference Basel III articles and thresholds where relevant."
        ),
        tools=[tool],
        messages=messages
    )

    answer = next((b.text for b in final.content if hasattr(b, "text")), "(No answer generated.)")
    print("\n" + "=" * 60)
    print(answer)
    print("=" * 60)


def main() -> None:
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_QUESTION

    script_dir    = os.path.dirname(os.path.abspath(__file__))
    ontology_path = os.path.join(script_dir, ONTOLOGY_FILE)
    db_path       = os.path.join(script_dir, DB_FILE)

    if not os.path.exists(ontology_path):
        print(f"ERROR: ontology not found at {ontology_path}")
        sys.exit(1)
    if not os.path.exists(db_path):
        print(f"ERROR: {db_path} not found — run bootstrap_ontology.py first.")
        sys.exit(1)

    os.chdir(script_dir)

    log.info("ontology.load", path=ontology_path)
    ontology_context = load_ontology(ontology_path)
    tool   = build_tool(ontology_context)
    client = anthropic.Anthropic()

    ask(question, tool, client)


if __name__ == "__main__":
    main()
