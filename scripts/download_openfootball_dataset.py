from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


ARCHIVE_URLS = (
    "https://codeload.github.com/openfootball/football.json/zip/refs/heads/master",
    "https://codeload.github.com/openfootball/football.json/zip/refs/heads/main",
)

PROJECT_DIR = Path(__file__).resolve().parents[1]
TARGET_DIR = PROJECT_DIR / "database" / "matches"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Descarga el repositorio openfootball/football.json e instala el "
            "dataset dentro de database/matches."
        )
    )
    parser.add_argument(
        "--keep-archive",
        action="store_true",
        help="Conserva el archivo ZIP descargado dentro del directorio temporal para depuración.",
    )
    return parser.parse_args()


def download_archive(destination: Path) -> Path:
    last_error: Exception | None = None
    archive_path = destination / "openfootball-football-json.zip"

    for url in ARCHIVE_URLS:
        try:
            with urlopen(url, timeout=60) as response:
                archive_path.write_bytes(response.read())
            print(f"Archivo descargado desde: {url}")
            return archive_path
        except (HTTPError, URLError) as exc:
            last_error = exc
            print(f"No se pudo descargar desde {url}: {exc}", file=sys.stderr)

    raise RuntimeError(
        "No fue posible descargar el dataset de openfootball/football.json."
    ) from last_error


def extract_archive(archive_path: Path, destination: Path) -> Path:
    with zipfile.ZipFile(archive_path, "r") as zip_file:
        zip_file.extractall(destination)

    extracted_roots = [path for path in destination.iterdir() if path.is_dir()]
    if not extracted_roots:
        raise RuntimeError("No se encontró contenido extraído en el archivo ZIP.")

    repository_root = extracted_roots[0]
    source_matches_dir = resolve_dataset_dir(repository_root)

    return source_matches_dir


def resolve_dataset_dir(repository_root: Path) -> Path:
    nested_matches_dir = repository_root / "matches"
    if nested_matches_dir.is_dir():
        return nested_matches_dir

    json_files = list(repository_root.glob("*/*.json"))
    if json_files:
        return repository_root

    raise RuntimeError(
        "El repositorio descargado no contiene una estructura de dataset reconocible."
    )


def replace_dataset(source_matches_dir: Path, target_dir: Path) -> None:
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(source_matches_dir, target_dir)


def main() -> int:
    args = parse_args()

    with tempfile.TemporaryDirectory(prefix="openfootball-download-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)

        try:
            archive_path = download_archive(temp_dir)
            source_matches_dir = extract_archive(archive_path, temp_dir)
            replace_dataset(source_matches_dir, TARGET_DIR)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1

        if args.keep_archive:
            kept_archive_path = PROJECT_DIR / archive_path.name
            shutil.copy2(archive_path, kept_archive_path)
            print(f"Se conservó una copia del ZIP en: {kept_archive_path}")

    print(f"Dataset instalado correctamente en: {TARGET_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
