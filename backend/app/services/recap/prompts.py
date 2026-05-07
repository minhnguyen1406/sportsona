"""Prompt templates and render functions for race recaps.

PROMPT_VERSION is bumped whenever the system prompt changes meaningfully —
stored alongside generated recaps so we can diff output across versions and
reproducibly regenerate against any historical prompt.

The system prompt is intentionally static (no per-user interpolation) so it
hits Anthropic's prompt cache: ~1.5k tokens cached at 0.1× cost after the
first call within a 5-minute window.
"""

from __future__ import annotations

from app.services.recap.context import RecapContext


PROMPT_VERSION = "v1.0.0"


SYSTEM_PROMPT = """\
You are writing a personalized post-race recap for a Formula 1 fan reading on Sportsona.

# Voice
Write like a sharp friend who watched the race and is now texting you about it.
Specific, opinionated when warranted, conversational. Not an analyst, not a
hype writer. Confident enough to call a driver's day disappointing if it was.

# Required structure
Markdown output. The first line is a 6-12 word headline (no leading "#"),
then a blank line, then 4-6 short paragraphs (2-4 sentences each).

The recap MUST cover, in this order:

1. **Hook (1 paragraph)**: Open on what mattered most for THIS user — usually
   their followed drivers' result, or a championship swing involving them.
   If they don't follow anyone notable, lead with the headline of the race.

2. **What happened (1-2 paragraphs)**: The shape of the race. Specific moves,
   lap numbers, gaps. Avoid reciting positions 1-20 — pick the moments that
   mattered.

3. **Followed drivers / teams (1-2 paragraphs)**: Each followed entity gets
   honest coverage. If a followed driver had a quiet race, say so plainly.
   Don't pad. Don't fabricate moments.

4. **Championship implications (≤1 paragraph, only if meaningful)**: How the
   standings moved. Include points gaps only when load-bearing.

5. **Forward look (1 paragraph)**: One specific thing to watch at the next
   race — a track that suits a followed driver, a teammate battle, or a
   regulation tweak. Concrete, not "tune in next week".

# Hard rules
- Never invent moments, lap numbers, or positions not present in the input.
- Status notes (DNF, collision, mechanical) are facts — use them when relevant.
- If the user follows nobody, lead with championship leaders or race drama.
- No cliches: avoid "battle royale", "edge of your seat", "in stunning fashion".
- No emoji unless explicitly in the input.
- Length: 250-400 words.

# Output format
Plain markdown. No preamble like "Here's the recap". Headline → blank line → body.
"""


def _format_followed(label: str, items: list[str]) -> str:
    if not items:
        return f"{label}: none"
    return f"{label}: {', '.join(items)}"


def render_user_message(ctx: RecapContext) -> str:
    """Render the typed context as a structured user message for the LLM.

    Deterministic ordering and formatting — same inputs produce identical
    bytes, so the output is safe to use as a cache key downstream.
    """
    lines: list[str] = []

    # Profile
    lines.append(f"USER: {ctx.user_username}")
    lines.append(_format_followed("Following drivers", ctx.followed_drivers))
    lines.append(_format_followed("Following teams", ctx.followed_constructors))

    # Race
    lines.append("")
    lines.append(f"RACE: {ctx.race_season} {ctx.race_name} (Round {ctx.race_round})")
    venue = ctx.circuit_name + (f", {ctx.circuit_country}" if ctx.circuit_country else "")
    lines.append(f"Venue: {venue}")
    lines.append(f"Date: {ctx.race_date.isoformat()}")

    # Qualifying (top 10 only — beyond that is rarely interesting)
    if ctx.qualifying:
        lines.append("")
        lines.append("QUALIFYING (top 10):")
        for q in ctx.qualifying[:10]:
            pos = q.position if q.position is not None else "—"
            time_part = f" — {q.q3_time}" if q.q3_time else ""
            lines.append(f"  {pos}. {q.driver_name} ({q.constructor_name}){time_part}")

    # Race results
    if ctx.results:
        lines.append("")
        lines.append("RACE RESULTS:")
        for r in ctx.results:
            pos = r.position_text or (str(r.position) if r.position is not None else "—")
            grid = f" — grid P{r.grid_position}" if r.grid_position is not None else ""
            gap = f" — {r.time_or_gap}" if r.time_or_gap else ""
            status = (
                f" [{r.status}]"
                if r.status and r.status not in ("Finished", "+1 Lap", "+2 Laps", "+3 Laps")
                else ""
            )
            lines.append(
                f"  {pos}. {r.driver_name} ({r.constructor_name}){grid} — {r.points}pt{gap}{status}"
            )

    # Notable incidents (DNFs, collisions, mechanical)
    if ctx.notable_status_events:
        lines.append("")
        lines.append("NOTABLE INCIDENTS:")
        for event in ctx.notable_status_events:
            lines.append(f"  - {event}")

    # Standings (top 5 — gives championship context without padding)
    if ctx.standings_after.drivers or ctx.standings_after.constructors:
        lines.append("")
        lines.append("STANDINGS AFTER THIS RACE:")
        if ctx.standings_after.drivers:
            lines.append("Drivers (top 5):")
            for s in ctx.standings_after.drivers[:5]:
                lines.append(f"  P{s.position} {s.name} — {s.points}pt ({s.wins}W)")
        if ctx.standings_after.constructors:
            lines.append("Constructors (top 5):")
            for s in ctx.standings_after.constructors[:5]:
                lines.append(f"  P{s.position} {s.name} — {s.points}pt ({s.wins}W)")

    # Next race
    if ctx.next_race:
        lines.append("")
        lines.append(
            f"NEXT RACE: {ctx.next_race.name} (Round {ctx.next_race.round}) on "
            f"{ctx.next_race.date.isoformat()} at {ctx.next_race.circuit}"
        )

    return "\n".join(lines)
