from pydantic import BaseModel, Field


class Score(BaseModel):
    ht: list[int] = Field(default_factory=list, description="Goles al entretiempo [local, visitante].")
    ft: list[int] = Field(default_factory=list, description="Goles al final [local, visitante].")


class MatchCreate(BaseModel):
    round: str
    date: str
    time: str
    team1: str
    team2: str
    score: Score


class Match(MatchCreate):
    match_id: int


class ScoreUpdate(BaseModel):
    ht: list[int] | None = None
    ft: list[int] | None = None


class MatchUpdate(BaseModel):
    round: str | None = None
    date: str | None = None
    time: str | None = None
    team1: str | None = None
    team2: str | None = None
    score: ScoreUpdate | None = None


class CompetitionSummary(BaseModel):
    season: str
    league: str
    name: str
    matches_count: int


class CompetitionDetail(BaseModel):
    season: str
    league: str
    name: str
    matches_count: int
    matches: list[Match]


class RateLimitConfig(BaseModel):
    requests: int = Field(ge=1, description="Cantidad máxima de solicitudes permitidas.")
    window_seconds: float = Field(gt=0, description="Ventana de tiempo del límite en segundos.")


Score.model_rebuild()
MatchCreate.model_rebuild()
Match.model_rebuild()
ScoreUpdate.model_rebuild()
MatchUpdate.model_rebuild()
CompetitionSummary.model_rebuild()
CompetitionDetail.model_rebuild()
RateLimitConfig.model_rebuild()
