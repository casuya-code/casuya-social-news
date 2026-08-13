"""Tests for the community voting economy (Feature #35)."""

import pytest

from economy.vote_service import (
    ALLOWED_DIRECTIONS,
    DEFAULT_DIRECTION,
    InvalidDirectionError,
    client_influence,
    record_vote,
    resolve_direction,
    tally,
    total_votes,
)


@pytest.fixture(autouse=True)
def clean_votes(tmp_path, monkeypatch):
    """Point the vote store at a throwaway file (fresh per test)."""
    target = tmp_path / "votes.json"
    monkeypatch.setattr("economy.vote_store.votes_path", lambda: target)
    yield target


def test_record_and_tally_votes(clean_votes):
    record_vote("script-1", "client-a", "furaha")
    record_vote("script-1", "client-b", "furaha")
    record_vote("script-1", "client-c", "wasiwasi")
    assert tally("script-1") == {
        "msisimko": 0,
        "furaha": 2,
        "wasiwasi": 1,
        "utulivu": 0,
    }
    assert total_votes("script-1") == 3
    assert resolve_direction("script-1") == "furaha"


def test_changing_vote_only_counts_latest(clean_votes):
    assert record_vote("script-1", "client-a", "msisimko") is True
    assert record_vote("script-1", "client-a", "utulivu") is True
    assert tally("script-1")["msisimko"] == 0
    assert tally("script-1")["utulivu"] == 1
    assert total_votes("script-1") == 1


def test_repeat_vote_is_not_counted(clean_votes):
    record_vote("script-1", "client-a", "msisimko")
    assert record_vote("script-1", "client-a", "msisimko") is False
    assert total_votes("script-1") == 1


def test_default_direction_when_no_votes(clean_votes):
    assert resolve_direction("script-ghost") == DEFAULT_DIRECTION
    assert tally("script-ghost") == {d: 0 for d in ALLOWED_DIRECTIONS}


def test_rejects_unknown_direction(clean_votes):
    with pytest.raises(InvalidDirectionError):
        record_vote("script-1", "client-a", "siasa")


def test_client_influence_counts_distinct_scripts(clean_votes):
    record_vote("script-1", "client-a", "furaha")
    record_vote("script-2", "client-a", "wasiwasi")
    record_vote("script-2", "client-b", "msisimko")
    assert client_influence("client-a") == 2
    assert client_influence("client-b") == 1
    assert client_influence("nobody") == 0


def test_votes_persist_across_store_reloads(tmp_path, monkeypatch):
    import economy.vote_store as store

    store.save_votes({"script-1": {"client-a": "furaha"}})
    target = store.votes_path()
    assert target.exists()

    assert store.load_votes() == {"script-1": {"client-a": "furaha"}}
