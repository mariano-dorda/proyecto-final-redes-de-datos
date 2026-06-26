from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import require_basic_auth
from rate_limit_store import rate_limit_store
from schemas import RateLimitConfig


router = APIRouter(prefix="/rate-limit", tags=["rate-limit"])


@router.get("", response_model=RateLimitConfig)
def get_rate_limit(
    _: Annotated[str, Depends(require_basic_auth)],
):
    return RateLimitConfig(
        requests=rate_limit_store.requests,
        window_seconds=rate_limit_store.window_seconds,
    )


@router.put("", response_model=RateLimitConfig)
def update_rate_limit(
    config: RateLimitConfig,
    _: Annotated[str, Depends(require_basic_auth)],
):
    rate_limit_store.update(
        requests=config.requests,
        window_seconds=config.window_seconds,
    )
    return config
