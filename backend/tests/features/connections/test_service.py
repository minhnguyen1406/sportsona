"""Teammate graph: built from rosters, BFS connection, error cases."""
from datetime import date

import pytest

from app.features.connections import service
from app.models import Circuit, Constructor, Driver, DriverEntry, Season


@pytest.fixture
def world(db_session):
    db_session.add_all([Season(year=2010), Season(year=2020)])
    db_session.add(Circuit(circuit_id="c", name="C"))
    db_session.add_all([Constructor(constructor_id="red", name="Red"), Constructor(constructor_id="blue", name="Blue")])
    for i, (g, f) in enumerate([("A", "One"), ("B", "Two"), ("C", "Three"), ("D", "Four")]):
        db_session.add(Driver(driver_id=f"d{i}", given_name=g, family_name=f))
    # 2010: d0 & d1 at Red. 2020: d1 & d2 at Blue. d3 never raced with anyone.
    db_session.add_all([
        DriverEntry(season=2010, driver_id="d0", constructor_id="red"),
        DriverEntry(season=2010, driver_id="d1", constructor_id="red"),
        DriverEntry(season=2020, driver_id="d1", constructor_id="blue"),
        DriverEntry(season=2020, driver_id="d2", constructor_id="blue"),
        DriverEntry(season=2020, driver_id="d3", constructor_id="red"),  # alone at Red in 2020
    ])
    db_session.commit()
    service._cache = None  # never reuse a graph built by another test
    yield
    service._cache = None


def test_two_hop_chain_with_via_labels(db_session, world):
    c = service.connect(db_session, "d0", "d2")
    assert c.degrees == 2
    assert [h.driver_id for h in c.path] == ["d0", "d1", "d2"]
    assert c.path[0].via is None
    assert c.path[1].via == service.Via(2010, "red", "Red")
    assert c.path[2].via == service.Via(2020, "blue", "Blue")


def test_direct_teammates_one_degree(db_session, world):
    assert service.connect(db_session, "d0", "d1").degrees == 1


def test_same_driver_zero_degrees(db_session, world):
    assert service.connect(db_session, "d1", "d1").degrees == 0


def test_isolated_driver_raises(db_session, world):
    with pytest.raises(service.ConnectionError_, match="no recorded teammates"):
        service.connect(db_session, "d0", "d3")


def test_unknown_driver_raises(db_session, world):
    with pytest.raises(service.ConnectionError_, match="Unknown driver"):
        service.connect(db_session, "d0", "ghost")


def test_stats(db_session, world):
    assert service.graph_stats(db_session) == {"drivers": 3, "teammate_links": 2}
