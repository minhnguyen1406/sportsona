"""Stats service over real rows — each test pins one algorithm's wiring."""
from datetime import date

import pytest

from app.models import Circuit, Driver, DriverEntry, DriverStanding, QualifyingResult, Race, RaceResult, Season
from app.sports.f1.services import stats


@pytest.fixture
def season(db_session):
    db_session.add(Season(year=2024))
    db_session.add(Circuit(circuit_id="c", name="C"))
    db_session.add_all([
        Driver(driver_id="ver", given_name="Max", family_name="Verstappen"),
        Driver(driver_id="nor", given_name="Lando", family_name="Norris"),
        Driver(driver_id="old", given_name="Old", family_name="Timer"),
    ])
    races = [Race(id=i, season=2024, round=i, name=f"R{i}", circuit_id="c", date=date(2024, 3, i)) for i in range(1, 7)]
    db_session.add_all(races)
    # ver: 1,1,1,4,2,1  (25,25,25,12,18,25) ; nor: 2,2,2,1,1,2 (18,18,18,25,25,18)
    ver = [(1, 25), (1, 25), (1, 25), (4, 12), (2, 18), (1, 25)]
    nor = [(2, 18), (2, 18), (2, 18), (1, 25), (1, 25), (2, 18)]
    for i, ((vp, vpt), (np_, npt)) in enumerate(zip(ver, nor), start=1):
        db_session.add(RaceResult(race_id=i, driver_id="ver", constructor_id="rb", position=vp, points=vpt))
        db_session.add(RaceResult(race_id=i, driver_id="nor", constructor_id="mcl", position=np_, points=npt))
    db_session.add_all([
        DriverStanding(season=2024, round=6, driver_id="ver", position=1, points=130, wins=4),
        DriverStanding(season=2024, round=6, driver_id="nor", position=2, points=122, wins=2),
    ])
    db_session.add_all([
        DriverEntry(season=2024, driver_id="ver", constructor_id="rb"),
        DriverEntry(season=2024, driver_id="nor", constructor_id="mcl"),
        DriverEntry(season=1990, driver_id="old", constructor_id="x"),
        DriverEntry(season=1995, driver_id="old", constructor_id="x"),
    ])
    db_session.add_all([
        QualifyingResult(race_id=1, driver_id="ver", constructor_id="rb", position=1, q3_time="1:10.000"),
        QualifyingResult(race_id=1, driver_id="nor", constructor_id="mcl", position=2, q3_time="1:10.500"),
    ])
    db_session.commit()
    # rb/mcl/x constructors aren't needed for these paths (no joins on them).


def test_form_guide_rolling_average_and_momentum(db_session, season):
    f = stats.form_guide(db_session, "ver", k=3)
    assert f["season"] == 2024 and f["window"] == 3
    # last 3 = 12,18,25 → 18.33 ; window 3 earlier = 25,25,25 → 25 ; momentum −6.67
    assert f["current_avg"] == 18.33 and f["momentum"] == -6.67
    assert [p["rolling_avg"] for p in f["series"]][:3] == [25.0, 25.0, 25.0]


def test_streaks_and_hottest_stretch(db_session, season):
    s = stats.career_streaks(db_session, "ver")
    assert s["longest_win_streak"]["length"] == 3
    assert s["longest_win_streak"]["from"]["race"] == "R1"
    assert s["longest_podium_streak"]["length"] == 3     # broken by P4 at R4
    assert s["longest_points_streak"]["length"] == 6
    assert s["hottest_stretch"]["points_above_average"] > 0


def test_progression_prefix_sums(db_session, season):
    p = stats.progression(db_session, "nor", 2024)
    assert [r["cumulative"] for r in p["rounds"]] == [18, 36, 54, 79, 104, 122]
    assert p["total"] == 122


def test_career_overlap_and_active(db_session, season):
    o = stats.career_overlap(db_session, "ver", "nor")
    assert o["overlap"] == {"from": 2024, "to": 2024, "seasons": 1}
    assert stats.career_overlap(db_session, "ver", "old")["overlap"] is None
    a = stats.active_in(db_session, 1992)
    assert a["driver_ids"] == ["old"] and a["count"] == 1


def test_title_math_alive_and_clinched(db_session, season):
    # 6 rounds total, standings after round 6 → 0 remaining → leader clinched.
    t = stats.title_math(db_session, 2024)
    assert t["remaining_rounds"] == 0 and t["clinched"] is True
    assert t["drivers"][1]["alive"] is False
    # Add two future rounds: nor max = 122 + 50 = 172 ≥ 130 → alive, not clinched.
    db_session.add_all([Race(id=7, season=2024, round=7, name="R7", circuit_id="c", date=date(2024, 4, 1)),
                        Race(id=8, season=2024, round=8, name="R8", circuit_id="c", date=date(2024, 4, 8))])
    db_session.commit()
    t = stats.title_math(db_session, 2024)
    assert t["remaining_rounds"] == 2 and t["clinched"] is False
    assert t["drivers"][1]["alive"] is True and t["drivers"][1]["needs_per_round"] == 4.0


def test_fantasy_knapsack_respects_budget_and_size(db_session, season):
    # costs: P1 → 29, P2 → 28. Budget 30 fits only one → picks ver (130 pts).
    f = stats.fantasy_optimize(db_session, 2024, budget=30, max_drivers=5)
    assert [r["driver_id"] for r in f["roster"]] == ["ver"] and f["total_points"] == 130
    f = stats.fantasy_optimize(db_session, 2024, budget=100, max_drivers=1)
    assert len(f["roster"]) == 1


def test_lap_rank_binary_search(db_session, season):
    r = stats.lap_rank(db_session, 1, "1:10.250")
    assert r["rank"] == 2 and r["field_size"] == 2 and r["beats_percent"] == 50.0
    assert r["pole_time"] == 70.0 and r["gap_to_pole"] == 0.25
    assert stats.parse_lap_time("72.5") == 72.5


def test_unknown_driver_raises(db_session, season):
    with pytest.raises(stats.StatsError):
        stats.form_guide(db_session, "ghost")
