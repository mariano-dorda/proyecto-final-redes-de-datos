from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from data_access import get_competition_path, materialize_matches, read_competition, write_competition
from dependencies import require_basic_auth
from schemas import Match, MatchCreate


router = APIRouter(prefix="/competitions/{season}/{league}/matches", tags=["matches"])


@router.get("", response_model=list[Match])
def list_matches(
    season: str,
    league: str,
    team: str | None = Query(default=None),
    round_name: str | None = Query(default=None, alias="round"),
    date: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    path = get_competition_path(season, league)
    payload = read_competition(path)
    matches = materialize_matches(payload.get("matches", []))

    if team:
        team_lower = team.lower()
        matches = [
            match
            for match in matches
            if team_lower in match.team1.lower() or team_lower in match.team2.lower()
        ]
    if round_name:
        round_lower = round_name.lower()
        matches = [match for match in matches if round_lower in match.round.lower()]
    if date:
        matches = [match for match in matches if match.date == date]

    return matches[offset : offset + limit]


@router.get("/{match_id}", response_model=Match)
def get_match(season: str, league: str, match_id: int):
    path = get_competition_path(season, league)
    payload = read_competition(path)
    raw_matches = payload.get("matches", [])

    if match_id < 0 or match_id >= len(raw_matches):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el partido con match_id={match_id}.",
        )

    return Match(match_id=match_id, **raw_matches[match_id])


@router.post("", response_model=Match, status_code=status.HTTP_201_CREATED)
def create_match(
    season: str,
    league: str,
    match: MatchCreate,
    _: Annotated[str, Depends(require_basic_auth)],
):
    path = get_competition_path(season, league)
    payload = read_competition(path)
    raw_matches = payload.setdefault("matches", [])
    raw_matches.append(match.model_dump())
    write_competition(path, payload)
    return Match(match_id=len(raw_matches) - 1, **match.model_dump())


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(
    season: str,
    league: str,
    match_id: int,
    _: Annotated[str, Depends(require_basic_auth)],
):
    path = get_competition_path(season, league)
    payload = read_competition(path)
    raw_matches = payload.get("matches", [])

    if match_id < 0 or match_id >= len(raw_matches):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el partido con match_id={match_id}.",
        )

    raw_matches.pop(match_id)
    payload["matches"] = raw_matches
    write_competition(path, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
