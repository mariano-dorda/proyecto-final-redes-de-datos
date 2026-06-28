import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from ..data_access import get_competition_path, materialize_matches, read_competition, write_competition
from ..dependencies import require_basic_auth
from ..schemas import Match, MatchCreate, MatchUpdate


router = APIRouter(prefix="/competitions/{season}/{league}/matches", tags=["matches"])


def normalize_round(value: str) -> str:
    normalized = value.strip().lower()
    match = re.search(r"(\d+)$", normalized)
    return match.group(1) if match else normalized


def validate_score_progression(score: dict) -> None:
    ht_score = score.get("ht", [])
    ft_score = score.get("ft", [])

    if len(ht_score) < 2 or len(ft_score) < 2:
        return

    if ht_score[0] > ft_score[0] or ht_score[1] > ft_score[1]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "El marcador del primer tiempo no puede superar al marcador final "
                "para ninguno de los dos equipos."
            ),
        )


@router.get("", response_model=list[Match])
def list_matches(
    response: Response,
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
        normalized_round = normalize_round(round_name)
        matches = [
            match
            for match in matches
            if normalize_round(match.round) == normalized_round
        ]
    if date:
        matches = [match for match in matches if match.date == date]

    total_count = len(matches)
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Offset"] = str(offset)
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
    validate_score_progression(match.score.model_dump())
    path = get_competition_path(season, league)
    payload = read_competition(path)
    raw_matches = payload.setdefault("matches", [])
    raw_matches.append(match.model_dump())
    write_competition(path, payload)
    return Match(match_id=len(raw_matches) - 1, **match.model_dump())


@router.put("/{match_id}", response_model=Match)
def update_match(
    season: str,
    league: str,
    match_id: int,
    match: MatchUpdate,
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

    current_match = raw_matches[match_id]
    changes = match.model_dump(exclude_none=True)

    if "score" in changes:
        current_score = dict(current_match.get("score", {}))
        current_score.update(changes["score"])
        validate_score_progression(current_score)
        changes["score"] = current_score

    updated_match = dict(current_match)
    updated_match.update(changes)

    raw_matches[match_id] = updated_match
    payload["matches"] = raw_matches
    write_competition(path, payload)
    return Match(match_id=match_id, **updated_match)


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
