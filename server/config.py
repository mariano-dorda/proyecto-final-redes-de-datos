import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
DATABASE_DIR = PROJECT_DIR / "database" / "matches"
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "5"))
RATE_LIMIT_WINDOW_SECONDS = float(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "1"))
API_BASIC_USER = os.getenv("API_BASIC_USER", "admin")
API_BASIC_PASSWORD = os.getenv("API_BASIC_PASSWORD", "admin123")
