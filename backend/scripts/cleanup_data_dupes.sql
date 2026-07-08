-- Sportsona data cleanup migration.
--
-- Fixes three classes of issue:
--   1. Duplicate drivers — 25 drivers existed with both "long" (first_last)
--      and "short" (last) ids; long form is canonical (modern sync uses it).
--   2. Duplicate constructors — `Haas F1 Team` and `Alfa Romeo` each had
--      a long+short pair. Keep long.
--   3. Inconsistent country/nationality strings — 3-letter ISO codes mixed
--      with demonyms (GBR vs British); circuits use both UK and United
--      Kingdom; constructors have empty-string nationalities.
--
-- Single transaction. Idempotent (re-running on clean data is a no-op).
--
-- HOW TO RUN
--   From host (with docker compose up):
--     docker compose exec -T sportsona-db psql -U sportsona_user -d sportsona \
--       < backend/scripts/cleanup_data_dupes.sql
--
--   Or interactively inside the container:
--     docker compose exec sportsona-db psql -U sportsona_user -d sportsona
--     \i /tmp/cleanup_data_dupes.sql  -- after `docker cp`'ing the file
--
-- HISTORICAL CONTEXT
--   Dupes were introduced because an earlier version of sync_f1_data.py
--   used short-form ids (`hamilton`, `alfa`) while the current version uses
--   long-form (`lewis_hamilton`, `alfa_romeo`). Future syncs only write
--   long-form, so this script is mostly archival — but safe to re-run if
--   you ever sync from an older source.

BEGIN;

-- ─────────── 1. Driver dedup ───────────
-- Build mapping of {dupe -> canonical} where canonical = LONGER id.
DROP TABLE IF EXISTS _driver_dupe_map;
CREATE TEMP TABLE _driver_dupe_map AS
WITH dupes AS (
  SELECT
    given_name,
    family_name,
    -- Tiebreaker order: prefer pure-ASCII ids over diacritic ids, then
    -- longer over shorter. Without the first key, two ids of equal
    -- character length (kimi_raikkonen vs kimi_räikkönen — both 14 chars)
    -- pick arbitrarily and the merge can go the wrong way.
    array_agg(driver_id ORDER BY (driver_id ~ '[^a-z0-9_]'),
                                  length(driver_id) DESC,
                                  driver_id) AS ids
  FROM f1.drivers
  GROUP BY given_name, family_name
  HAVING COUNT(*) > 1
)
SELECT ids[1] AS canonical, ids[2] AS dupe FROM dupes;

-- For each FK table: move rows whose dupe ref doesn't already collide with
-- the canonical's existing row, then delete the rest (collisions).

-- driver_entries: UNIQUE(season, driver_id, constructor_id)
UPDATE f1.driver_entries de
SET driver_id = m.canonical
FROM _driver_dupe_map m
WHERE de.driver_id = m.dupe
  AND NOT EXISTS (
    SELECT 1 FROM f1.driver_entries de2
    WHERE de2.driver_id = m.canonical
      AND de2.season = de.season
      AND de2.constructor_id = de.constructor_id
  );
DELETE FROM f1.driver_entries de
USING _driver_dupe_map m
WHERE de.driver_id = m.dupe;

-- race_results: UNIQUE(race_id, driver_id)
UPDATE f1.race_results rr
SET driver_id = m.canonical
FROM _driver_dupe_map m
WHERE rr.driver_id = m.dupe
  AND NOT EXISTS (
    SELECT 1 FROM f1.race_results rr2
    WHERE rr2.driver_id = m.canonical AND rr2.race_id = rr.race_id
  );
DELETE FROM f1.race_results rr USING _driver_dupe_map m WHERE rr.driver_id = m.dupe;

-- driver_standings: UNIQUE(season, round, driver_id)
UPDATE f1.driver_standings ds
SET driver_id = m.canonical
FROM _driver_dupe_map m
WHERE ds.driver_id = m.dupe
  AND NOT EXISTS (
    SELECT 1 FROM f1.driver_standings ds2
    WHERE ds2.driver_id = m.canonical
      AND ds2.season = ds.season
      AND ds2.round = ds.round
  );
DELETE FROM f1.driver_standings ds USING _driver_dupe_map m WHERE ds.driver_id = m.dupe;

-- qualifying_results: UNIQUE(race_id, driver_id)
UPDATE f1.qualifying_results qr
SET driver_id = m.canonical
FROM _driver_dupe_map m
WHERE qr.driver_id = m.dupe
  AND NOT EXISTS (
    SELECT 1 FROM f1.qualifying_results qr2
    WHERE qr2.driver_id = m.canonical AND qr2.race_id = qr.race_id
  );
DELETE FROM f1.qualifying_results qr USING _driver_dupe_map m WHERE qr.driver_id = m.dupe;

-- user_driver_follows: UNIQUE(user_id, driver_id)
UPDATE public.user_driver_follows udf
SET driver_id = m.canonical
FROM _driver_dupe_map m
WHERE udf.driver_id = m.dupe
  AND NOT EXISTS (
    SELECT 1 FROM public.user_driver_follows udf2
    WHERE udf2.driver_id = m.canonical AND udf2.user_id = udf.user_id
  );
DELETE FROM public.user_driver_follows udf USING _driver_dupe_map m WHERE udf.driver_id = m.dupe;

-- Drop the dupe driver rows themselves
DELETE FROM f1.drivers d USING _driver_dupe_map m WHERE d.driver_id = m.dupe;


-- ─────────── 2. Constructor dedup ───────────
DROP TABLE IF EXISTS _ctor_dupe_map;
CREATE TEMP TABLE _ctor_dupe_map AS
WITH dupes AS (
  SELECT name, array_agg(constructor_id ORDER BY length(constructor_id) DESC) AS ids
  FROM f1.constructors
  GROUP BY name
  HAVING COUNT(*) > 1
)
SELECT ids[1] AS canonical, ids[2] AS dupe FROM dupes;

-- driver_entries: UNIQUE(season, driver_id, constructor_id)
UPDATE f1.driver_entries de
SET constructor_id = m.canonical
FROM _ctor_dupe_map m
WHERE de.constructor_id = m.dupe
  AND NOT EXISTS (
    SELECT 1 FROM f1.driver_entries de2
    WHERE de2.constructor_id = m.canonical
      AND de2.season = de.season
      AND de2.driver_id = de.driver_id
  );
DELETE FROM f1.driver_entries de USING _ctor_dupe_map m WHERE de.constructor_id = m.dupe;

-- race_results: no UNIQUE on constructor_id, just update
UPDATE f1.race_results SET constructor_id = m.canonical FROM _ctor_dupe_map m WHERE constructor_id = m.dupe;

-- qualifying_results: same
UPDATE f1.qualifying_results SET constructor_id = m.canonical FROM _ctor_dupe_map m WHERE constructor_id = m.dupe;

-- constructor_standings: UNIQUE(season, round, constructor_id)
UPDATE f1.constructor_standings cs
SET constructor_id = m.canonical
FROM _ctor_dupe_map m
WHERE cs.constructor_id = m.dupe
  AND NOT EXISTS (
    SELECT 1 FROM f1.constructor_standings cs2
    WHERE cs2.constructor_id = m.canonical
      AND cs2.season = cs.season
      AND cs2.round = cs.round
  );
DELETE FROM f1.constructor_standings cs USING _ctor_dupe_map m WHERE cs.constructor_id = m.dupe;

-- user_constructor_follows: UNIQUE(user_id, constructor_id)
UPDATE public.user_constructor_follows ucf
SET constructor_id = m.canonical
FROM _ctor_dupe_map m
WHERE ucf.constructor_id = m.dupe
  AND NOT EXISTS (
    SELECT 1 FROM public.user_constructor_follows ucf2
    WHERE ucf2.constructor_id = m.canonical AND ucf2.user_id = ucf.user_id
  );
DELETE FROM public.user_constructor_follows ucf USING _ctor_dupe_map m WHERE ucf.constructor_id = m.dupe;

DELETE FROM f1.constructors c USING _ctor_dupe_map m WHERE c.constructor_id = m.dupe;


-- ─────────── 3. Normalize driver nationality (3-letter codes → demonyms) ───────────
UPDATE f1.drivers
SET nationality = CASE nationality
  WHEN 'GBR' THEN 'British'
  WHEN 'USA' THEN 'American'
  WHEN 'AUS' THEN 'Australian'
  WHEN 'CAN' THEN 'Canadian'
  WHEN 'CHN' THEN 'Chinese'
  WHEN 'DEN' THEN 'Danish'
  WHEN 'ESP' THEN 'Spanish'
  WHEN 'FIN' THEN 'Finnish'
  WHEN 'FRA' THEN 'French'
  WHEN 'GER' THEN 'German'
  WHEN 'JPN' THEN 'Japanese'
  WHEN 'MEX' THEN 'Mexican'
  WHEN 'NED' THEN 'Dutch'
  WHEN 'MON' THEN 'Monegasque'
  WHEN 'THA' THEN 'Thai'
  WHEN 'ITA' THEN 'Italian'
  WHEN 'BEL' THEN 'Belgian'
  WHEN 'NZL' THEN 'New Zealander'
END
WHERE nationality IN ('GBR','USA','AUS','CAN','CHN','DEN','ESP','FIN','FRA','GER','JPN','MEX','NED','MON','THA','ITA','BEL','NZL');

-- Empty-string nationality → NULL for cleanliness
UPDATE f1.drivers SET nationality = NULL WHERE nationality = '';


-- ─────────── 4. Normalize circuit country (alias variants → canonical) ───────────
UPDATE f1.circuits SET country = 'United Kingdom' WHERE country IN ('UK', 'Great Britain');
UPDATE f1.circuits SET country = 'United States' WHERE country IN ('USA', 'US');
UPDATE f1.circuits SET country = 'United Arab Emirates' WHERE country = 'UAE';


-- ─────────── 5. Normalize constructor nationality (empty → NULL) ───────────
UPDATE f1.constructors SET nationality = NULL WHERE nationality = '';


-- ─────────── 6. Fill known nationalities for modern teams ───────────
-- These were NULL because an older sync ingested constructors without
-- nationality. Hand-curated from each team's F1-registered nationality
-- (which sometimes differs from operating HQ — e.g. Red Bull is registered
-- Austrian despite being based in Milton Keynes, UK).
UPDATE f1.constructors SET nationality = 'Swiss'    WHERE constructor_id = 'alfa_romeo'        AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'Swiss'    WHERE constructor_id = 'alfa_romeo_racing' AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'Italian'  WHERE constructor_id = 'alphatauri'        AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'French'   WHERE constructor_id = 'alpine'            AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'British'  WHERE constructor_id = 'aston_martin'      AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'Italian'  WHERE constructor_id = 'ferrari'           AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'American' WHERE constructor_id = 'haas_f1_team'      AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'Swiss'    WHERE constructor_id = 'kick_sauber'       AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'British'  WHERE constructor_id = 'mclaren'           AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'German'   WHERE constructor_id = 'mercedes'          AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'Italian'  WHERE constructor_id = 'rb'                AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'Italian'  WHERE constructor_id = 'racing_bulls'      AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'British'  WHERE constructor_id = 'racing_point'      AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'Austrian' WHERE constructor_id = 'red_bull_racing'   AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'French'   WHERE constructor_id = 'renault'           AND nationality IS NULL;
UPDATE f1.constructors SET nationality = 'British'  WHERE constructor_id = 'williams'          AND nationality IS NULL;


-- ─────────── 6b. Diacritic-mismatch driver dupes ───────────
-- Two upstreams disagree on accents: Ergast keeps Hülkenberg / Pérez,
-- FastF1 strips them to Hulkenberg / Perez. The section-1 dedup grouped
-- by exact family_name match so it missed these. Handle the known pairs
-- explicitly — keep the ASCII (long-form) row as canonical.
DROP TABLE IF EXISTS _accent_dupe_map;
CREATE TEMP TABLE _accent_dupe_map (canonical text, dupe text);
INSERT INTO _accent_dupe_map VALUES
  ('nico_hulkenberg', 'hulkenberg'),
  ('sergio_perez',    'perez');
-- Only apply for pairs where BOTH rows actually exist in this DB.
DELETE FROM _accent_dupe_map m
WHERE NOT EXISTS (SELECT 1 FROM f1.drivers WHERE driver_id = m.canonical)
   OR NOT EXISTS (SELECT 1 FROM f1.drivers WHERE driver_id = m.dupe);

-- Same FK-migration pattern as section 1.
UPDATE f1.driver_entries de SET driver_id = m.canonical FROM _accent_dupe_map m
WHERE de.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.driver_entries de2
  WHERE de2.driver_id = m.canonical AND de2.season = de.season AND de2.constructor_id = de.constructor_id
);
DELETE FROM f1.driver_entries de USING _accent_dupe_map m WHERE de.driver_id = m.dupe;

UPDATE f1.race_results rr SET driver_id = m.canonical FROM _accent_dupe_map m
WHERE rr.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.race_results rr2 WHERE rr2.driver_id = m.canonical AND rr2.race_id = rr.race_id
);
DELETE FROM f1.race_results rr USING _accent_dupe_map m WHERE rr.driver_id = m.dupe;

UPDATE f1.driver_standings ds SET driver_id = m.canonical FROM _accent_dupe_map m
WHERE ds.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.driver_standings ds2
  WHERE ds2.driver_id = m.canonical AND ds2.season = ds.season AND ds2.round = ds.round
);
DELETE FROM f1.driver_standings ds USING _accent_dupe_map m WHERE ds.driver_id = m.dupe;

UPDATE f1.qualifying_results qr SET driver_id = m.canonical FROM _accent_dupe_map m
WHERE qr.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.qualifying_results qr2 WHERE qr2.driver_id = m.canonical AND qr2.race_id = qr.race_id
);
DELETE FROM f1.qualifying_results qr USING _accent_dupe_map m WHERE qr.driver_id = m.dupe;

UPDATE public.user_driver_follows udf SET driver_id = m.canonical FROM _accent_dupe_map m
WHERE udf.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM public.user_driver_follows udf2 WHERE udf2.driver_id = m.canonical AND udf2.user_id = udf.user_id
);
DELETE FROM public.user_driver_follows udf USING _accent_dupe_map m WHERE udf.driver_id = m.dupe;

DELETE FROM f1.drivers d USING _accent_dupe_map m WHERE d.driver_id = m.dupe;


-- ─────────── 6c. Generic diacritic-dupe sweep (auto-detected) ───────────
-- For ANY driver_id containing diacritics: compute its ASCII fold as the
-- target canonical. If the canonical row already exists → merge FKs into
-- it and delete the diacritic row. If not → INSERT a canonical row first,
-- migrate FKs, delete the diacritic row. This both fixes existing splits
-- AND repairs the case where section 1 picked the diacritic row as canonical
-- (kimi_raikkonen and kimi_räikkönen both happen to be 14 chars long).
CREATE EXTENSION IF NOT EXISTS unaccent;

DROP TABLE IF EXISTS _diacritic_dupe_map;
CREATE TEMP TABLE _diacritic_dupe_map AS
SELECT driver_id AS dupe,
       unaccent(driver_id) AS canonical
FROM f1.drivers
WHERE driver_id ~ '[^a-z0-9_]';

-- If the canonical ASCII row doesn't exist yet, INSERT it by copying the
-- diacritic row's attributes (given/family/dob/nationality stay the same).
INSERT INTO f1.drivers (driver_id, given_name, family_name, date_of_birth, nationality)
SELECT m.canonical, d.given_name, d.family_name, d.date_of_birth, d.nationality
FROM _diacritic_dupe_map m
JOIN f1.drivers d ON d.driver_id = m.dupe
WHERE NOT EXISTS (SELECT 1 FROM f1.drivers c WHERE c.driver_id = m.canonical)
ON CONFLICT (driver_id) DO NOTHING;

UPDATE f1.driver_entries de SET driver_id = m.canonical FROM _diacritic_dupe_map m
WHERE de.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.driver_entries de2
  WHERE de2.driver_id = m.canonical AND de2.season = de.season AND de2.constructor_id = de.constructor_id
);
DELETE FROM f1.driver_entries de USING _diacritic_dupe_map m WHERE de.driver_id = m.dupe;

UPDATE f1.race_results rr SET driver_id = m.canonical FROM _diacritic_dupe_map m
WHERE rr.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.race_results rr2 WHERE rr2.driver_id = m.canonical AND rr2.race_id = rr.race_id
);
DELETE FROM f1.race_results rr USING _diacritic_dupe_map m WHERE rr.driver_id = m.dupe;

UPDATE f1.driver_standings ds SET driver_id = m.canonical FROM _diacritic_dupe_map m
WHERE ds.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.driver_standings ds2
  WHERE ds2.driver_id = m.canonical AND ds2.season = ds.season AND ds2.round = ds.round
);
DELETE FROM f1.driver_standings ds USING _diacritic_dupe_map m WHERE ds.driver_id = m.dupe;

UPDATE f1.qualifying_results qr SET driver_id = m.canonical FROM _diacritic_dupe_map m
WHERE qr.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.qualifying_results qr2 WHERE qr2.driver_id = m.canonical AND qr2.race_id = qr.race_id
);
DELETE FROM f1.qualifying_results qr USING _diacritic_dupe_map m WHERE qr.driver_id = m.dupe;

UPDATE public.user_driver_follows udf SET driver_id = m.canonical FROM _diacritic_dupe_map m
WHERE udf.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM public.user_driver_follows udf2 WHERE udf2.driver_id = m.canonical AND udf2.user_id = udf.user_id
);
DELETE FROM public.user_driver_follows udf USING _diacritic_dupe_map m WHERE udf.driver_id = m.dupe;

DELETE FROM f1.drivers d USING _diacritic_dupe_map m WHERE d.driver_id = m.dupe;

-- Same sweep for constructors (rare in practice — team names tend to be ASCII
-- already — but cheap to include and future-proof).
DROP TABLE IF EXISTS _diacritic_cons_map;
CREATE TEMP TABLE _diacritic_cons_map AS
SELECT constructor_id AS dupe,
       unaccent(constructor_id) AS canonical
FROM f1.constructors
WHERE constructor_id ~ '[^a-z0-9_]';

INSERT INTO f1.constructors (constructor_id, name, nationality)
SELECT m.canonical, c.name, c.nationality
FROM _diacritic_cons_map m
JOIN f1.constructors c ON c.constructor_id = m.dupe
WHERE NOT EXISTS (SELECT 1 FROM f1.constructors x WHERE x.constructor_id = m.canonical)
ON CONFLICT (constructor_id) DO NOTHING;

UPDATE f1.driver_entries de SET constructor_id = m.canonical FROM _diacritic_cons_map m
WHERE de.constructor_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.driver_entries de2
  WHERE de2.constructor_id = m.canonical AND de2.season = de.season AND de2.driver_id = de.driver_id
);
DELETE FROM f1.driver_entries de USING _diacritic_cons_map m WHERE de.constructor_id = m.dupe;

UPDATE f1.race_results rr SET constructor_id = m.canonical FROM _diacritic_cons_map m
WHERE rr.constructor_id = m.dupe;
UPDATE f1.qualifying_results qr SET constructor_id = m.canonical FROM _diacritic_cons_map m
WHERE qr.constructor_id = m.dupe;

UPDATE f1.constructor_standings cs SET constructor_id = m.canonical FROM _diacritic_cons_map m
WHERE cs.constructor_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.constructor_standings cs2
  WHERE cs2.constructor_id = m.canonical AND cs2.season = cs.season AND cs2.round = cs.round
);
DELETE FROM f1.constructor_standings cs USING _diacritic_cons_map m WHERE cs.constructor_id = m.dupe;

UPDATE public.user_constructor_follows ucf SET constructor_id = m.canonical FROM _diacritic_cons_map m
WHERE ucf.constructor_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM public.user_constructor_follows ucf2
  WHERE ucf2.constructor_id = m.canonical AND ucf2.user_id = ucf.user_id
);
DELETE FROM public.user_constructor_follows ucf USING _diacritic_cons_map m WHERE ucf.constructor_id = m.dupe;

DELETE FROM f1.constructors c USING _diacritic_cons_map m WHERE c.constructor_id = m.dupe;


-- ─────────── 6d. Short-slug → long-form rename for modern drivers ───────────
-- Ergast historically used single-word slugs like `rosberg` for any modern
-- driver without ambiguity in their era. Our convention everywhere else is
-- `given_family`. The list below is every short-slug driver who raced in our
-- data window (2010+) with NO long-form twin to merge into — so this is a
-- rename, not a merge. Antonelli is the one true merge here (both forms exist
-- for the same person; canonical = longer FastF1 form).
-- Hardcoded list because the auto-detection from family_name would need to
-- distinguish father/son etc., which requires human judgment per pair.
DROP TABLE IF EXISTS _short_slug_map;
CREATE TEMP TABLE _short_slug_map (dupe text, canonical text);
INSERT INTO _short_slug_map VALUES
  ('kimi_antonelli',    'andrea_kimi_antonelli'),   -- same person, merge
  ('massa',             'felipe_massa'),
  ('rosberg',           'nico_rosberg'),
  ('button',            'jenson_button'),
  ('webber',            'mark_webber'),
  ('kobayashi',         'kamui_kobayashi'),
  ('kovalainen',        'heikki_kovalainen'),
  ('petrov',            'vitaly_petrov'),
  ('glock',             'timo_glock'),
  ('maldonado',         'pastor_maldonado'),
  ('sutil',             'adrian_sutil'),
  ('resta',             'paul_di_resta'),
  ('buemi',             'sebastien_buemi'),
  ('barrichello',       'rubens_barrichello'),
  ('alguersuari',       'jaime_alguersuari'),
  ('trulli',            'jarno_trulli'),
  ('liuzzi',            'vitantonio_liuzzi'),
  ('vergne',            'jean_eric_vergne'),
  ('rosa',              'pedro_de_la_rosa'),
  ('pic',               'charles_pic'),
  ('karthikeyan',       'narain_karthikeyan'),
  ('ambrosio',          'jerome_d_ambrosio'),
  ('grassi',            'lucas_di_grassi'),
  ('gutierrez',         'esteban_gutierrez'),
  ('heidfeld',          'nick_heidfeld'),
  ('chilton',           'max_chilton'),
  ('garde',             'giedo_van_der_garde'),
  ('chandhok',          'karun_chandhok'),
  ('yamamoto',          'sakon_yamamoto'),
  ('nasr',              'felipe_nasr'),
  ('wehrlein',          'pascal_wehrlein'),
  ('klien',             'christian_klien'),
  ('haryanto',          'rio_haryanto'),
  ('stevens',           'will_stevens'),
  ('merhi',             'roberto_merhi'),
  ('rossi',             'alexander_rossi');

-- Only act on pairs where the dupe row actually exists in the current DB.
DELETE FROM _short_slug_map m
WHERE NOT EXISTS (SELECT 1 FROM f1.drivers WHERE driver_id = m.dupe);

-- If the canonical doesn't exist yet, copy the dupe row into it.
INSERT INTO f1.drivers (driver_id, given_name, family_name, date_of_birth, nationality)
SELECT m.canonical, d.given_name, d.family_name, d.date_of_birth, d.nationality
FROM _short_slug_map m
JOIN f1.drivers d ON d.driver_id = m.dupe
WHERE NOT EXISTS (SELECT 1 FROM f1.drivers c WHERE c.driver_id = m.canonical)
ON CONFLICT (driver_id) DO NOTHING;

-- Same FK-migration pattern as 6b/6c.
UPDATE f1.driver_entries de SET driver_id = m.canonical FROM _short_slug_map m
WHERE de.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.driver_entries de2
  WHERE de2.driver_id = m.canonical AND de2.season = de.season AND de2.constructor_id = de.constructor_id
);
DELETE FROM f1.driver_entries de USING _short_slug_map m WHERE de.driver_id = m.dupe;

UPDATE f1.race_results rr SET driver_id = m.canonical FROM _short_slug_map m
WHERE rr.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.race_results rr2 WHERE rr2.driver_id = m.canonical AND rr2.race_id = rr.race_id
);
DELETE FROM f1.race_results rr USING _short_slug_map m WHERE rr.driver_id = m.dupe;

UPDATE f1.driver_standings ds SET driver_id = m.canonical FROM _short_slug_map m
WHERE ds.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.driver_standings ds2
  WHERE ds2.driver_id = m.canonical AND ds2.season = ds.season AND ds2.round = ds.round
);
DELETE FROM f1.driver_standings ds USING _short_slug_map m WHERE ds.driver_id = m.dupe;

UPDATE f1.qualifying_results qr SET driver_id = m.canonical FROM _short_slug_map m
WHERE qr.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM f1.qualifying_results qr2 WHERE qr2.driver_id = m.canonical AND qr2.race_id = qr.race_id
);
DELETE FROM f1.qualifying_results qr USING _short_slug_map m WHERE qr.driver_id = m.dupe;

UPDATE public.user_driver_follows udf SET driver_id = m.canonical FROM _short_slug_map m
WHERE udf.driver_id = m.dupe AND NOT EXISTS (
  SELECT 1 FROM public.user_driver_follows udf2 WHERE udf2.driver_id = m.canonical AND udf2.user_id = udf.user_id
);
DELETE FROM public.user_driver_follows udf USING _short_slug_map m WHERE udf.driver_id = m.dupe;

DELETE FROM f1.drivers d USING _short_slug_map m WHERE d.driver_id = m.dupe;


-- ─────────── 7. Fill known nationalities for modern drivers ───────────
-- Drivers that came in via a sync that omitted nationality.
UPDATE f1.drivers SET nationality = 'Italian'       WHERE driver_id = 'andrea_kimi_antonelli' AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'British'       WHERE driver_id = 'oliver_bearman'        AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'Brazilian'     WHERE driver_id = 'gabriel_bortoleto'     AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'Australian'    WHERE driver_id = 'jack_doohan'           AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'Swedish'       WHERE driver_id = 'marcus_ericsson'       AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'Italian'       WHERE driver_id = 'antonio_giovinazzi'    AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'French'        WHERE driver_id = 'romain_grosjean'       AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'French'        WHERE driver_id = 'isack_hadjar'          AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'New Zealander' WHERE driver_id = 'brendon_hartley'       AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'Polish'        WHERE driver_id = 'robert_kubica'         AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'Russian'       WHERE driver_id = 'daniil_kvyat'          AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'Canadian'      WHERE driver_id = 'nicholas_latifi'       AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'New Zealander' WHERE driver_id = 'liam_lawson'           AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'Russian'       WHERE driver_id = 'nikita_mazepin'        AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'Finnish'       WHERE driver_id = 'kimi_räikkönen'        AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'German'        WHERE driver_id = 'mick_schumacher'       AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'Russian'       WHERE driver_id = 'sergey_sirotkin'       AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'Belgian'       WHERE driver_id = 'stoffel_vandoorne'     AND nationality IS NULL;
UPDATE f1.drivers SET nationality = 'German'        WHERE driver_id = 'sebastian_vettel'      AND nationality IS NULL;


COMMIT;
