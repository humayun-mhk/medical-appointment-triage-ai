from collections import defaultdict, deque
from time import monotonic

from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models import User


_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


def check_rate_limit(request: Request, key: str, max_requests: int, window_seconds: int) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        return
    now = monotonic()
    bucket_key = f"{request.url.path}:{key}"
    bucket = _BUCKETS[bucket_key]
    while bucket and now - bucket[0] > window_seconds:
        bucket.popleft()
    if len(bucket) >= max_requests:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")
    bucket.append(now)


def ip_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def admin_rate_limit(request: Request, current_user: User = Depends(get_current_user)) -> None:
    check_rate_limit(request, f"admin:{current_user.id}", 60, 60)
