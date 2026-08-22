"""Three-state provenance derived from SQL."""
from app.features.ask import provenance as pv


def _states(items):
    return [i.state for i in items]


def test_confirmed_tables_listed_once(db_session):
    sql = "SELECT d.family_name, COUNT(*) FROM f1.race_results rr JOIN f1.drivers d ON d.driver_id = rr.driver_id JOIN f1.race_results x ON x.id = rr.id GROUP BY 1"
    items = pv.provenance_for(db_session, sql, "who has the most wins")
    labels = [i.label for i in items if i.state == "confirmed"]
    assert any(l.startswith("Official race results") for l in labels)
    assert any(l.startswith("Driver records") for l in labels)
    assert sum(l.startswith("Official race results") for l in labels) == 1   # de-duplicated


def test_aggregate_marks_derived(db_session):
    items = pv.provenance_for(db_session, "SELECT AVG(points) FROM f1.race_results", "average points")
    assert "derived" in _states(items)
    assert items[-1].source == "Derived by us"


def test_plain_select_is_not_derived(db_session):
    items = pv.provenance_for(db_session, "SELECT position FROM f1.race_results ORDER BY position LIMIT 5", "top positions")
    assert "derived" not in _states(items)


def test_unmodelled_topic_flagged_unavailable(db_session):
    items = pv.provenance_for(db_session, "SELECT * FROM f1.race_results LIMIT 1", "fastest pit stop at Monaco")
    assert items[-1].state == "unavailable" and "Pit-stop" in items[-1].label


def test_schema_doc_note_fallback(db_session):
    items = pv.provenance_for(db_session, "SELECT 'Lap-by-lap data is not in the database yet'::text AS note", "lap times")
    assert items == [pv.ProvenanceItem("unavailable", "This isn't in the database yet", "Not available")]
