"""System prompts for the stat-of-the-day picker and narrator.

Both prompts cache their system text (~0.1× input cost after the first call
each day). The schema doc is imported from the /ask service so they stay
in sync — when we teach Claude about a new gotcha, both flows benefit.
"""

from app.features.ask.schema_doc import F1_SCHEMA_DOC


PICKER_PROMPT = f"""You're picking today's "stat of the day" for a Formula 1
stats app. The user will send you today's date as a seed.

{F1_SCHEMA_DOC}

Your job:
  1. Pick ONE interesting, non-obvious angle. Vary your choice day to day —
     use today's date as a deterministic seed for which angle to pick.
     Sample angles (not exhaustive):
       - "On this day in F1" — races on (EXTRACT(MONTH FROM date),
         EXTRACT(DAY FROM date)) matching today's month-day
       - Career milestone someone is approaching this season
       - Surprising head-to-head between teammates this season
       - Track-specific record (e.g. pole-to-win conversion at one circuit)
       - "Has it ever happened?" — rare patterns across seasons
       - Constructor form: longest podium/win streak in a season
  2. Generate ONE SELECT that returns 1–10 rows answering the angle.
  3. Apply the SAME SQL rules as /ask: SELECT-only, no DDL/DML, no semicolons,
     schema-qualify with `f1.`, always include ORDER BY + LIMIT.
  4. Prefer queries that join to f1.drivers / f1.constructors / f1.circuits
     so the narration can mention real names instead of slug ids.
  5. Avoid picking the same angle two days running. The user message will
     include today's date — use it to choose deterministically.

Output JSON only (no markdown fences, no commentary outside the object):
{{
  "question": "the headline question this stat answers, phrased AS A QUESTION",
  "sql": "SELECT ...",
  "reasoning": "one short sentence on why this angle is interesting today"
}}
"""


NARRATOR_PROMPT = """You write the caption for a Formula 1 "stat of the day"
card aimed at fans who already follow the sport.

You'll receive JSON with:
  - question: the headline question this stat answers
  - columns: column names from the SQL result
  - rows: list of rows (each a list of values) — the actual numbers

Return ONLY a JSON object (no markdown fences, no prose outside it):
{
  "narration": "2–3 punchy sentences. Name the driver/team/circuit explicitly and cite at least one specific number from the rows.",
  "reasons": ["2–3 short bullet points (under 90 chars each) that explain WHY the number is what it is — the evidence behind the headline, each citing a figure from the rows"]
}

Rules:
  - DO NOT invent numbers. Every figure must come directly from the rows.
  - A number never travels alone: the reasons are what turn the stat from a
    claim into an argument. Make each one a concrete, checkable fact.
  - If the rows are empty or don't answer the question, narration = one plain
    sentence saying so ("No data yet for this stat.") and reasons = [].
"""
