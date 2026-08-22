"""Build the teammate graph from the database and find shortest connections.

Graph model:
  - node  = a driver
  - edge  = the two drivers were teammates: they shared a (season, constructor).
            Label = that (season, constructor), so the path can be narrated
            ("Hamilton → Button: McLaren, 2012").

Edge sources are unioned for coverage:
  - ``driver_entries`` — season rosters, every season 1950→today.
  - ``race_results`` joined to races — every (driver, team, season) that
    actually raced, which also catches mid-season swaps.

Built once and cached in-process with a TTL (data changes nightly). ~430
drivers / a few thousand edges — tiny; BFS answers in microseconds.
"""

from __future__ import annotations

import time
from itertools import combinations
from typing import NamedTuple

from sqlalchemy.orm import Session

from app.common.algorithms.graph import Graph
from app.models import Constructor, Driver, DriverEntry, Race, RaceResult


class Via(NamedTuple):
    season: int
    constructor_id: str
    constructor: str


class Hop(NamedTuple):
    driver_id: str
    name: str
    via: Via | None   # the shared team that links this hop to the previous one


class Connection(NamedTuple):
    degrees: int      # number of edges; 0 = same driver, 1 = direct teammates
    path: list[Hop]


_TTL_SECONDS = 600
_cache: tuple[float, Graph[str, Via], dict[str, str]] | None = None


def build_graph(db: Session) -> tuple[Graph[str, Via], dict[str, str]]:
    """Returns (graph, driver_id → display name)."""
    names = {
        d.driver_id: f"{d.given_name} {d.family_name}".strip()
        for d in db.query(Driver).all()
    }
    team_names = {c.constructor_id: c.name for c in db.query(Constructor).all()}

    # (season, constructor) → set of driver ids. Two sources, one bucket map.
    rosters: dict[tuple[int, str], set[str]] = {}

    for season, constructor_id, driver_id in db.query(
        DriverEntry.season, DriverEntry.constructor_id, DriverEntry.driver_id
    ):
        rosters.setdefault((season, constructor_id), set()).add(driver_id)

    for season, constructor_id, driver_id in (
        db.query(Race.season, RaceResult.constructor_id, RaceResult.driver_id)
        .join(Race, Race.id == RaceResult.race_id)
    ):
        rosters.setdefault((season, constructor_id), set()).add(driver_id)

    graph: Graph[str, Via] = Graph()
    # Earliest season first so a repeated pair keeps its first shared season
    # as the label (Graph.add_edge keeps the first label it sees).
    for (season, constructor_id), drivers in sorted(rosters.items()):
        via = Via(season, constructor_id, team_names.get(constructor_id, constructor_id))
        for a, b in combinations(sorted(drivers), 2):
            graph.add_edge(a, b, via)

    return graph, names


def get_graph(db: Session) -> tuple[Graph[str, Via], dict[str, str]]:
    global _cache
    now = time.monotonic()
    if _cache is None or now - _cache[0] > _TTL_SECONDS:
        graph, names = build_graph(db)
        _cache = (now, graph, names)
    return _cache[1], _cache[2]


class ConnectionError_(Exception):
    """Unknown driver, or the two drivers are not connected."""


def connect(db: Session, from_id: str, to_id: str) -> Connection:
    graph, names = get_graph(db)
    for d in (from_id, to_id):
        if d not in names:
            raise ConnectionError_(f"Unknown driver: {d}")
        if not graph.has_node(d):
            raise ConnectionError_(f"{names[d]} has no recorded teammates.")

    path = graph.shortest_path(from_id, to_id)
    if path is None:
        raise ConnectionError_(f"No teammate chain links {names[from_id]} and {names[to_id]}.")

    hops = [Hop(driver_id=d, name=names[d], via=via) for d, via in path]
    return Connection(degrees=len(hops) - 1, path=hops)


def graph_stats(db: Session) -> dict[str, int]:
    graph, _ = get_graph(db)
    return {"drivers": graph.node_count(), "teammate_links": graph.edge_count()}
