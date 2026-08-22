"""Union-find duplicate clustering over real model rows (SQLite harness)."""
from datetime import date

from app.models import Constructor, Driver
from app.sports.f1.services import duplicates


def test_same_person_different_ids_cluster_together(db_session):
    # short-form Ergast id, long-form FastF1 id, diacritic variant — one person.
    db_session.add_all([
        Driver(driver_id="raikkonen", given_name="Kimi", family_name="Räikkönen"),
        Driver(driver_id="kimi_raikkonen", given_name="Kimi", family_name="Raikkonen"),
        Driver(driver_id="kimi_räikkönen", given_name="Kimi", family_name="Räikkönen"),
    ])
    db_session.commit()

    clusters = duplicates.find_duplicate_drivers(db_session)

    assert len(clusters) == 1
    assert clusters[0].ids == ["kimi_raikkonen", "kimi_räikkönen", "raikkonen"]
    assert clusters[0].suggested_canonical == "kimi_raikkonen"   # equals the full-name slug
    assert any(s.startswith("name:kimi_raikkonen") for s in clusters[0].signals)


def test_father_and_son_are_not_merged(db_session):
    # Same surname, different people — must NOT cluster.
    db_session.add_all([
        Driver(driver_id="keke_rosberg", given_name="Keke", family_name="Rosberg", date_of_birth=date(1948, 12, 6)),
        Driver(driver_id="nico_rosberg", given_name="Nico", family_name="Rosberg", date_of_birth=date(1985, 6, 27)),
    ])
    db_session.commit()
    assert duplicates.find_duplicate_drivers(db_session) == []


def test_dob_plus_surname_ties_rows_with_different_given_name_spelling(db_session):
    db_session.add_all([
        Driver(driver_id="a", given_name="Nicolas", family_name="Hulkenberg", date_of_birth=date(1987, 8, 19)),
        Driver(driver_id="b", given_name="Nico", family_name="Hülkenberg", date_of_birth=date(1987, 8, 19)),
    ])
    db_session.commit()
    clusters = duplicates.find_duplicate_drivers(db_session)
    assert len(clusters) == 1 and clusters[0].ids == ["a", "b"]
    assert any(s.startswith("dob:1987-08-19") for s in clusters[0].signals)


def test_alias_table_ties_rows(db_session):
    # _DRIVER_ALIASES maps kimi_antonelli → andrea_kimi_antonelli.
    db_session.add_all([
        Driver(driver_id="kimi_antonelli", given_name="Kimi", family_name="Antonelli"),
        Driver(driver_id="andrea_kimi_antonelli", given_name="Andrea Kimi", family_name="Antonelli"),
    ])
    db_session.commit()
    clusters = duplicates.find_duplicate_drivers(db_session)
    assert len(clusters) == 1
    assert clusters[0].suggested_canonical == "andrea_kimi_antonelli"
    assert "alias:andrea_kimi_antonelli" in clusters[0].signals


def test_constructor_duplicates_by_name(db_session):
    db_session.add_all([
        Constructor(constructor_id="haas", name="Haas F1 Team"),
        Constructor(constructor_id="haas_f1_team", name="Haas F1 Team"),
        Constructor(constructor_id="ferrari", name="Ferrari"),
    ])
    db_session.commit()
    clusters = duplicates.find_duplicate_constructors(db_session)
    assert len(clusters) == 1
    assert clusters[0].ids == ["haas", "haas_f1_team"]
    assert clusters[0].suggested_canonical == "haas_f1_team"
