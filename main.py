import sys
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from config import DATABASE_DIR
from routers.competitions import router as competitions_router
from routers.matches import router as matches_router
from routers.rate_limit import router as rate_limit_router
from rate_limit_store import rate_limit_store


app = FastAPI(
    title="Football Matches API",
    description=(
        "API REST para consultar y modificar archivos JSON de partidos "
        "almacenados por temporada y liga."
    ),
    version="1.0.0",
)

app.include_router(competitions_router)
app.include_router(matches_router)
app.include_router(rate_limit_router)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_host = request.client.host if request.client else "unknown"
    bucket_key = f"{client_host}:{request.url.path}"
    now = time.monotonic()
    bucket = rate_limit_store.buckets[bucket_key]

    while bucket and now - bucket[0] >= rate_limit_store.window_seconds:
        bucket.popleft()

    if len(bucket) >= rate_limit_store.requests:
        return JSONResponse(
            status_code=429,
            content={
                "detail": (
                    f"Límite excedido: máximo {rate_limit_store.requests} solicitudes cada "
                    f"{rate_limit_store.window_seconds:g} segundo(s)."
                )
            },
        )

    bucket.append(now)
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(rate_limit_store.requests)
    response.headers["X-RateLimit-Window-Seconds"] = f"{rate_limit_store.window_seconds:g}"
    response.headers["X-RateLimit-Remaining"] = str(max(rate_limit_store.requests - len(bucket), 0))
    return response


@app.get("/health", tags=["health"])
def healthcheck():
    return {
        "status": "ok",
        "database_dir": str(DATABASE_DIR),
        "rate_limit_requests": rate_limit_store.requests,
        "rate_limit_window_seconds": rate_limit_store.window_seconds,
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
