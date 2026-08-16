"""Community voting economy (Feature #35).

Each client votes for the direction they want the drama to take. Votes are
tallied per script; the winning direction can be fed back into the next
story so the community literally steers the narrative.
"""

from __future__ import annotations

from economy.vote_store import load_votes, save_votes
from monitoring.metrics import VOTES_RECORDED

ALLOWED_DIRECTIONS = ("msisimko", "furaha", "wasiwasi", "utulivu")
DIRECTION_PATTERN = f"^({'|'.join(ALLOWED_DIRECTIONS)})$"

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
    VOTES_RECORDED.labels(direction=direction).inc()
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
    total = sum(counts.values())
    if total == 0:
        return DEFAULT_DIRECTION
    return max(counts, key=counts.get)


def community_pulse() -> str:
    """Steering signal for the next batch of stories.

    The most recently voted script's winning direction becomes the tone for
    upcoming generated drama. Neutral default until the community votes.
    """
    votes = load_votes()
    if not votes:
        return DEFAULT_DIRECTION
    latest_script_id = next(reversed(votes))
    return resolve_direction(latest_script_id)


def client_influence(client_id: str) -> int:
    """Number of distinct scripts a client has voted on (engagement metric)."""
    votes = load_votes()
    return sum(1 for per_script in votes.values() if client_id in per_script)
