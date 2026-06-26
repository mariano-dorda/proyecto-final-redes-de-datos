from fastapi import APIRouter, Query, Response

from ..data_access import (
    build_competition_descriptor,
    get_competition_path,
    get_json_files,
    materialize_matches,
    read_competition,
)
from ..schemas import CompetitionDetail, CompetitionSummary


router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("", response_model=list[CompetitionSummary])
def list_competitions(
    response: Response,
    season: str | None = Query(default=None),
    league: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    competitions = [
        CompetitionSummary(**build_competition_descriptor(path))
        for path in get_json_files()
    ]

    if season:
        competitions = [item for item in competitions if item.season == season]
    if league:
        competitions = [item for item in competitions if league.lower() in item.league.lower()]

    total_count = len(competitions)
    response.headers["X-Total-Count"] = str(total_count)
    response.headers["X-Limit"] = str(limit)
    response.headers["X-Offset"] = str(offset)
    return competitions[offset : offset + limit]


@router.get("/{season}/{league}", response_model=CompetitionDetail)
def get_competition(season: str, league: str):
    path = get_competition_path(season, league)
    payload = read_competition(path)
    matches = materialize_matches(payload.get("matches", []))
    return CompetitionDetail(
        season=season,
        league=league,
        name=payload.get("name", league),
        matches_count=len(matches),
        matches=matches,
    )
