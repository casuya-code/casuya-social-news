"""Community voting economy endpoints (Feature #35).

POST /api/v1/economy/vote          — cast or change a vote on a script
GET  /api/v1/economy/stats/{id}    — tally + winning direction for a script
GET  /api/v1/economy/influence/{client_id} — how many stories a client steered
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from api.errors import InvalidInputError
from config.logging_config import get_logger
from database.engine import SessionLocal
from database.models import Vote
from economy import vote_service
from security.api_key_auth import verify_api_key

_logger = get_logger("api.economy")

router = APIRouter(dependencies=[Depends(verify_api_key)])


class VoteInput(BaseModel):
    """A single community vote on story direction."""

    script_id: str = Field(..., min_length=8, max_length=64)
    client_id: str = Field(..., min_length=1, max_length=64)
    direction: str = Field(..., pattern="^(msisimko|furaha|wasiwasi|utulivu)$")


class VoteResponse(BaseModel):
    counted: bool
    direction: str
    total: int
    winner: str


class StatsResponse(BaseModel):
    script_id: str
    votes: dict[str, int]
    total: int
    winner: str


class InfluenceResponse(BaseModel):
    client_id: str
    scripts_influenced: int


@router.post("/vote", response_model=VoteResponse)
async def cast_vote(payload: VoteInput) -> VoteResponse:
    """Record a vote. A client's latest vote for a script always wins."""
    try:
        counted = vote_service.record_vote(payload.script_id, payload.client_id, payload.direction)
    except vote_service.InvalidDirectionError as exc:
        raise InvalidInputError(str(exc)) from exc

    # Best-effort mirror into Postgres (matching the global degrade-gracefully rule).
    try:
        async with SessionLocal() as session:
            session.add(
                Vote(
                    script_id=payload.script_id,
                    client_id=payload.client_id,
                    direction=payload.direction,
                )
            )
            await session.commit()
    except Exception as exc:  # noqa: BLE001
        _logger.warning("vote_db_persist_failed", error=str(exc))

    return VoteResponse(
        counted=counted,
        direction=payload.direction,
        total=vote_service.total_votes(payload.script_id),
        winner=vote_service.resolve_direction(payload.script_id),
    )


@router.get("/stats/{script_id}", response_model=StatsResponse)
async def vote_stats(script_id: str) -> StatsResponse:
    """Return the tally and winning direction for a script."""
    return StatsResponse(
        script_id=script_id,
        votes=vote_service.tally(script_id),
        total=vote_service.total_votes(script_id),
        winner=vote_service.resolve_direction(script_id),
    )


@router.get("/influence/{client_id}", response_model=InfluenceResponse)
async def client_influence(client_id: str) -> InfluenceResponse:
    """Engagement metric: how many distinct scripts a client has voted on."""
    return InfluenceResponse(
        client_id=client_id,
        scripts_influenced=vote_service.client_influence(client_id),
    )
