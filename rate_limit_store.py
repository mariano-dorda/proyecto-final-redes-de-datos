from collections import defaultdict, deque

from config import RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS


class RateLimitStore:
    def __init__(self, requests: int, window_seconds: float):
        self.requests = requests
        self.window_seconds = window_seconds
        self.buckets: dict[str, deque[float]] = defaultdict(deque)

    def update(self, requests: int, window_seconds: float) -> None:
        self.requests = requests
        self.window_seconds = window_seconds
        self.buckets.clear()


rate_limit_store = RateLimitStore(
    requests=RATE_LIMIT_REQUESTS,
    window_seconds=RATE_LIMIT_WINDOW_SECONDS,
)
