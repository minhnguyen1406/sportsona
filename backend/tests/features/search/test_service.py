"""Autocomplete over real rows: word-prefix, ascii-fold, kinds, limit."""
import pytest

from app.features.search import service
from app.models import Constructor, Driver


@pytest.fixture
def rows(db_session):
    db_session.add_all([
        Driver(driver_id="lewis_hamilton", given_name="Lewis", family_name="Hamilton", nationality="British"),
        Driver(driver_id="kimi_raikkonen", given_name="Kimi", family_name="Räikkönen", nationality="Finnish"),
        Driver(driver_id="fernando_alonso", given_name="Fernando", family_name="Alonso"),
        Constructor(constructor_id="ferrari", name="Ferrari", nationality="Italian"),
    ])
    db_session.commit()
    service._cache = None
    yield
    service._cache = None


def test_surname_prefix(db_session, rows):
    assert [h.label for h in service.suggest(db_session, "ham")] == ["Lewis Hamilton"]


def test_given_name_prefix_and_full_name(db_session, rows):
    assert [h.label for h in service.suggest(db_session, "lewis")] == ["Lewis Hamilton"]
    assert [h.label for h in service.suggest(db_session, "lewis ham")] == ["Lewis Hamilton"]


def test_ascii_fold_matches_diacritics(db_session, rows):
    assert [h.label for h in service.suggest(db_session, "raikk")] == ["Kimi Räikkönen"]


def test_mixed_kinds_and_sublabels(db_session, rows):
    hits = service.suggest(db_session, "fer")
    assert {h.label for h in hits} == {"Ferrari", "Fernando Alonso"}
    by_label = {h.label: h for h in hits}
    assert by_label["Ferrari"].kind == "constructor" and by_label["Ferrari"].href == "/constructors/ferrari"
    assert by_label["Ferrari"].sublabel == "Team · Italian"
    assert by_label["Fernando Alonso"].sublabel == "Driver"   # no nationality


def test_limit_and_blank(db_session, rows):
    assert len(service.suggest(db_session, "f", limit=1)) == 1
    assert service.suggest(db_session, "   ") == []
