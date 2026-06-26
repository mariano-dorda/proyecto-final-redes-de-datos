import json
from pathlib import Path

from fastapi import HTTPException, status

from .config import DATABASE_DIR
from .schemas import Match


def get_json_files() -> list[Path]:
    return sorted(DATABASE_DIR.rglob("*.json"))


def build_competition_descriptor(path: Path) -> dict[str, str | int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    matches = payload.get("matches", [])
    return {
        "season": path.parent.name,
        "league": path.stem,
        "name": payload.get("name", path.stem),
        "matches_count": len(matches),
    }


def get_competition_path(season: str, league: str) -> Path:
    path = DATABASE_DIR / season / f"{league}.json"
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe el recurso para season='{season}' y league='{league}'.",
        )
    return path


def read_competition(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_competition(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def materialize_matches(raw_matches: list[dict]) -> list[Match]:
    return [Match(match_id=index, **match) for index, match in enumerate(raw_matches)]
