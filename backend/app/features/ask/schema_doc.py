"""Hand-written description of the ``f1`` schema for the LLM.

Lives separately from the SQLAlchemy models because the LLM needs prose-
shaped hints (NULL semantics, slug conventions, gotchas) that don't map
to column metadata. Keep this in sync when columns are added.
"""

F1_SCHEMA_DOC = """\
PostgreSQL schema `f1` — Formula 1 historical data (1950–present).
Always qualify table names with `f1.`.

f1.seasons
  year (int, PK)                         -- e.g. 2023

f1.circuits
  circuit_id (text, PK)                  -- slug, e.g. 'monaco', 'silverstone'
  name (text)                            -- e.g. 'Circuit de Monaco'
  locality (text)                        -- city
  country (text)                         -- normalised, e.g. 'United Kingdom' (never 'UK')

f1.drivers
  driver_id (text, PK)                   -- long-form slug, e.g. 'max_verstappen', 'lewis_hamilton'
  given_name (text)
  family_name (text)
  date_of_birth (date)
  nationality (text)                     -- e.g. 'British', 'Dutch' (never 'GBR')

f1.constructors
  constructor_id (text, PK)              -- slug, e.g. 'ferrari', 'red_bull'
  name (text)                            -- e.g. 'Ferrari'
  nationality (text)                     -- e.g. 'Italian'

f1.driver_entries
  id (int, PK)
  season (int)  → f1.seasons.year
  driver_id (text)  → f1.drivers
  constructor_id (text)  → f1.constructors
  driver_number (int)
  driver_code (text)                     -- 3-letter code, e.g. 'VER'

f1.races
  id (int, PK)
  season (int)  → f1.seasons.year
  round (int)                            -- 1-based round number in the season
  name (text)                            -- e.g. 'Monaco Grand Prix'
  circuit_id (text)  → f1.circuits
  date (date)
  time (time)                            -- UTC start time

f1.race_results
  id (int, PK)
  race_id (int)  → f1.races
  driver_id (text)  → f1.drivers
  constructor_id (text)  → f1.constructors
  grid_position (int)                    -- starting position
  position (int)                         -- finishing position; NULL if DNF
  position_text (text)                   -- '1', '2', 'R' (retired), 'D' (disqualified), 'W' (withdrew)
  points (double precision)              -- championship points
  laps (int)
  time (text)                            -- race time or gap behind winner
  fastest_lap_time (text)
  fastest_lap_rank (int)                 -- 1 if this driver set the race's fastest lap
  status (text)                          -- 'Finished', '+1 Lap', 'Collision', etc.

f1.qualifying_results
  id (int, PK)
  race_id (int)  → f1.races
  driver_id (text)  → f1.drivers
  constructor_id (text)  → f1.constructors
  position (int)                         -- qualifying position (1 = pole)
  q1_time, q2_time, q3_time (text)       -- session lap times as strings

f1.driver_standings
  id (int, PK)
  season (int)  → f1.seasons.year
  round (int)                            -- standings AFTER this round
  driver_id (text)  → f1.drivers
  position (int)                         -- championship position
  points (double precision)
  wins (int)

f1.constructor_standings
  same shape as driver_standings, with constructor_id instead

Domain conventions and gotchas:
  - A "win" = f1.race_results.position = 1.
  - A "pole position" = f1.qualifying_results.position = 1.
  - A "podium" = f1.race_results.position IN (1, 2, 3).
  - DNFs have position IS NULL; inspect position_text/status for cause.
  - "Latest standings" for a season = row with max(round) for that season.
  - Driver lookups by name should be case-insensitive across given_name,
    family_name, or driver_id — users say 'Hamilton' or 'lewis_hamilton'.
  - Coverage: results are most complete for 2010–2024 plus partial 2025–2026.
    Older races have schedules but no results yet.

Race lookups — DO NOT guess circuit_id slugs:
  - Circuit ids are inconsistent (Monaco is 'monte_carlo' not 'monaco';
    São Paulo is 'são_paulo'; Mexico is 'mexico_city'). Never filter by
    a guessed circuit_id slug.
  - Instead, match races by race NAME or circuit locality, case-insensitive:
      WHERE r.name ILIKE '%monaco%'           -- preferred
        OR  c.locality ILIKE '%monte carlo%'
  - "Monaco" / "the Monaco GP" / "Monte Carlo" all map to races.name
    ILIKE '%monaco%'.

Time references — DO NOT use CURRENT_DATE directly for "today":
  - The DB stores race dates in their local race-day (no time zone), and
    CURRENT_DATE is the server's UTC date — they can disagree by ±1 day.
  - "today" / "today's race" / "the race just now" → the most recent race
    that already has results, not r.date = CURRENT_DATE. Use:
      ORDER BY r.date DESC LIMIT 1
      AND EXISTS (SELECT 1 FROM f1.race_results rr WHERE rr.race_id = r.id)
  - "this weekend" / "the latest race" / "the last race" → same as above.
  - "next race" / "upcoming" → earliest race in the CURRENT season with
    no results. The current season = max(season) among races that already
    have at least one result. Scope explicitly — historical seasons also
    contain rows with no results (e.g. 1950 races we haven't synced).
      WITH current_season AS (
        SELECT MAX(r2.season) AS yr FROM f1.races r2
        WHERE EXISTS (SELECT 1 FROM f1.race_results rr WHERE rr.race_id = r2.id)
      )
      SELECT ... FROM f1.races r, current_season cs
      WHERE r.season = cs.yr
        AND NOT EXISTS (SELECT 1 FROM f1.race_results rr WHERE rr.race_id = r.id)
      ORDER BY r.date ASC LIMIT 1
"""
