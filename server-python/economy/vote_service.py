"""Community voting economy (Feature #35).

Each client votes for the direction they want the drama to take. Votes are
tallied per script; the winning direction can be fed back into the next
story so the community literally steers the narrative.
"""

from __future__ import annotations

from economy.vote_store import load_votes, save_votes

ALLOWED_DIRECTIONS = ("msisimko", "furaha", "wasiwasi", "utulivu")

DEFAULT_DIRECTION = "utulivu"


class InvalidDirectionError(ValueError):
    """Raised when a vote targets an unknown direction."""


def record_vote(script_id: str, client_id: str, direction: str) -> bool:
    """Record a vote. Returns True if it changed anything.

    A client may change their vote for a script, but only the latest counts.
    """
    if direction not in ALLOWED_DIRECTIONS:
        raise InvalidDirectionError(f"direction must be one of {', '.join(ALLOWED_DIRECTIONS)}")

    votes = load_votes()
    per_script = votes.setdefault(script_id, {})
    if per_script.get(client_id) == direction:
        return False  # repeat of the same vote — nothing changed

    per_script[client_id] = direction
    save_votes(votes)
    return True


def tally(script_id: str) -> dict[str, int]:
    """Count votes per direction for a script."""
    votes = load_votes()
    per_script = votes.get(script_id, {})
    counts = {direction: 0 for direction in ALLOWED_DIRECTIONS}
    for direction in per_script.values():
        counts[direction] += 1
    return counts


def total_votes(script_id: str) -> int:
    """Total number of distinct clients who voted on a script."""
    return sum(tally(script_id).values())


def resolve_direction(script_id: str) -> str:
    """Winning direction, or the neutral default when there are no votes."""
    counts = tally(script_id)
    if total_votes(script_id) == 0:
        return DEFAULT_DIRECTION
    return max(counts, key=counts.get)


def client_influence(client_id: str) -> int:
    """Number of distinct scripts a client has voted on (engagement metric)."""
    votes = load_votes()
    return sum(1 for per_script in votes.values() if client_id in per_script)
