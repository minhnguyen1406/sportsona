# Sportsona — working notes for AI agents

F1-first, multi-sport companion app. Product thesis: an AI-native stats
product (natural language → Claude-written SQL → real rows, always with
provenance), plus daily stat, race recaps, and community threads. Owner is
building it both as a real product and as an interview portfolio piece.

## Run / test

```bash
docker compose up -d                      # db + backend (:8000) + nightly scheduler
cd web && yarn dev                        # frontend on :4000
cd web && yarn typecheck                  # svelte-check — must be 0 errors, 0 warnings
docker exec sportsona-backend sh -c "pip install -q pytest pytest-mock; python -m pytest tests/ -q"
docker exec sportsona-backend alembic upgrade head
docker exec sportsona-backend python -m scripts.sync_f1_data --year 2026 --results --qualifying --sprints --standings
```

Backend hot-reloads (code is volume-mounted). Anthropic key lives in the
root `.env` (`ANTHROPIC_API_KEY`); `RESEND_API_KEY`/`ALERT_EMAIL` optional.
DB user is `sportsona_user` (`docker exec sportsona-db psql -U sportsona_user -d sportsona`).

## Architecture (domain-first)

Backend `backend/app/`:
- `core/` config + database · `common/` errors, `sql_safety.py`, `email.py`,
  `algorithms/` (pure, unit-tested data structures: trie, graph/BFS,
  disjoint_set, lru_cache, bloom_filter, streaks, intervals, prefix_sum,
  knapsack, binary_search, brackets, fenwick, topo_sort)
- `auth/`, `users/` — accounts, follows, dashboard
- `sports/f1/{models,schemas,routers,services}/` — THE sport template. A new
  sport = a sibling folder with the same shape + its models re-exported from
  `app/models/__init__.py` (the registry; definitions never live there).
- `features/{ask,recap,stat_of_day,comments,search,connections}/` — flat
  feature modules (router/schemas/service + helpers). Feature `__init__.py`
  files are import-free (avoids registry ↔ service circular imports).

Frontend `web/src/lib/api/`: `client.ts` (apiFetch, auto-refresh) + one file
per domain (`f1.ts`, `ask.ts`, …) + `index.ts` barrel. Routes stay URL-based.
Components in `lib/components/` (+ `ui/` primitives), stores in `lib/stores/`.

Layering is strict: routers = HTTP only → services = logic → models.
Dependency-inject external clients (LLM, email) behind ABCs so tests stub them.

## Conventions the owner cares about

- Big-company, boring, readable code. Explicit over clever. Docstrings say *why*.
  Handle IntegrityError/races explicitly, no bare excepts, map errors at the edge.
- Mirror existing structure when adding features; don't invent a parallel one.
- Every algorithm feature is also an interview talking point: name the
  structure, the brute-force → optimal step, and a LeetCode analog in the
  docstring.
- **Git:** author is `minhnguyen1406 <minhnguyen1406@users.noreply.github.com>`
  (set in repo config). Commit messages are ONE short human line, imperative,
  no body, **no Co-Authored-By / AI trailers ever**. Split unrelated changes
  into separate commits. Push after verified work.
- Verify before reporting: run tests + typecheck; screenshot UI changes with
  headless Chrome (`google-chrome --headless=new --screenshot=… http://localhost:4000/…`;
  note it can't hold an authed session).

## Brand (v3, "The Rise")

Figtree only, no gradients. Grape 900/800/700/600 = #150724/#1F0D35/#2A1247/#3A2159;
Rose 500/400/700 = #E8607F/#F0839B/#B0304F; Sand 100/50 = #F3EEE2/#FBF7EF;
Teal #16B8A3, Volt #C8E63C, Warning #E39A0B. Raw tokens are `--sp-*` in
`web/src/app.css`; rose text on light uses `text-rose-ink`; tabular numerals via
`.sp-stat`/`.sp-fig`. One rose accent per view. Brand source of truth is the
Claude Design "Sportsona" project.

## Data facts

- Race + qualifying results 2010–2026, entry lists back to 1950, sprint
  results 2021+ (`f1.sprint_results`; `races.format` LIKE 'sprint%' marks
  sprint weekends). Sources: FastF1 (2018+) and Ergast (pre-2018), see
  `sports/f1/services/sync_service.py`. Ergast rate-limits — back off.
- Nightly sync at 04:00 UTC (`scripts/scheduled_sync.py`); on boot it
  self-heals missed race weekends and emails `ALERT_EMAIL` on failures.
- Circuit names for modern seasons come from FastF1 `Location`, never the
  sponsored `OfficialEventName`.
- `/ask` answers are cached 24h (in-process LRU + DB table, both TTL'd) and
  carry three-state provenance derived from the SQL.
- `Landing.svelte` hardcodes `SEASON` — bump each January.

## Status (as of 2026-09-18)

Phases 1–6 shipped (recaps, email, caching, upsert sync + scheduler, /ask
history + share + CI, domain-first restructure, brand v3 redesign, all
algorithm tiers, sprints, security + bug audits). **Not done: deployment** —
everything is localhost-only. Next after deploy: second sport, live race
threads.
