"""Unit tests for the comment-thread service — the tree reconstruction,
parent validation, and tombstone-on-delete behaviour."""

from __future__ import annotations

from datetime import date

import pytest

from app.features.comments import service
from app.features.comments.models import Comment
from app.models import Circuit, Race, Season, User


@pytest.fixture
def user(db_session):
    u = User(email="a@example.com", username="alice", hashed_password="x")
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def other_user(db_session):
    u = User(email="b@example.com", username="bob", hashed_password="x")
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def race(db_session):
    db_session.add(Season(year=2026))
    db_session.add(Circuit(circuit_id="monaco", name="Monaco"))
    r = Race(season=2026, round=1, name="Monaco GP", circuit_id="monaco", date=date(2026, 5, 24))
    db_session.add(r)
    db_session.commit()
    return r


def _add(db, race, user, body, parent_id=None):
    return service.add_comment(
        db, race_id=race.id, user_id=user.id, body=body, parent_id=parent_id
    )


class TestBuildThread:
    def test_empty_race_has_no_comments(self, db_session, race):
        assert service.build_thread(db_session, race.id) == []

    def test_reconstructs_nested_tree(self, db_session, race, user):
        root = _add(db_session, race, user, "root")
        reply = _add(db_session, race, user, "reply", parent_id=root.id)
        _add(db_session, race, user, "nested", parent_id=reply.id)
        _add(db_session, race, user, "second root")

        forest = service.build_thread(db_session, race.id)

        assert [n.body for n in forest] == ["root", "second root"]
        assert [n.body for n in forest[0].replies] == ["reply"]
        assert [n.body for n in forest[0].replies[0].replies] == ["nested"]
        assert forest[1].replies == []

    def test_author_username_is_surfaced(self, db_session, race, user):
        _add(db_session, race, user, "hi")
        forest = service.build_thread(db_session, race.id)
        assert forest[0].author == "alice"

    def test_scoped_to_one_race(self, db_session, race, user):
        # A comment on another race must not leak into this thread.
        db_session.add(Race(season=2026, round=2, name="Spain GP", circuit_id="monaco", date=date(2026, 6, 1)))
        db_session.commit()
        other = db_session.query(Race).filter_by(round=2).one()
        _add(db_session, race, user, "here")
        _add(db_session, other, user, "there")
        assert [n.body for n in service.build_thread(db_session, race.id)] == ["here"]


class TestAddComment:
    def test_reply_to_missing_parent_raises(self, db_session, race, user):
        with pytest.raises(service.CommentError):
            _add(db_session, race, user, "orphan", parent_id=9999)

    def test_reply_to_parent_in_other_race_raises(self, db_session, race, user):
        db_session.add(Race(season=2026, round=3, name="UK GP", circuit_id="monaco", date=date(2026, 7, 1)))
        db_session.commit()
        other = db_session.query(Race).filter_by(round=3).one()
        parent = _add(db_session, other, user, "elsewhere")
        with pytest.raises(service.CommentError):
            _add(db_session, race, user, "cross-race reply", parent_id=parent.id)


class TestDeleteComment:
    def test_tombstones_and_preserves_subtree(self, db_session, race, user):
        root = _add(db_session, race, user, "delete me")
        _add(db_session, race, user, "surviving reply", parent_id=root.id)

        service.delete_comment(db_session, comment_id=root.id, user_id=user.id)

        forest = service.build_thread(db_session, race.id)
        assert forest[0].is_deleted is True
        assert forest[0].author == "[deleted]"
        assert forest[0].body == "[deleted]"
        # The reply lives on.
        assert [n.body for n in forest[0].replies] == ["surviving reply"]

    def test_only_owner_can_delete(self, db_session, race, user, other_user):
        c = _add(db_session, race, user, "mine")
        with pytest.raises(service.CommentError):
            service.delete_comment(db_session, comment_id=c.id, user_id=other_user.id)
        # Untouched.
        assert db_session.query(Comment).filter_by(id=c.id).one().is_deleted is False
