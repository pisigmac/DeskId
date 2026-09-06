"""Rate limiter supporting in-memory, database-backed, and Redis backends with enable/disable flag."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import Lock

from fastapi import HTTPException, Request, status
from sqlalchemy import func, select

from deskid.config import Settings, get_settings


def _client_ip(request: Request) -> str:
    """Return the client identifier for rate limiting.

    When behind a trusted reverse proxy, the first IP in the configured proxy
    header is used. Otherwise the direct transport client address is used.
    """
    settings = get_settings()
    if settings.rate_limit_trust_proxy:
        header_value = request.headers.get(settings.rate_limit_proxy_header.lower())
        if header_value:
            # X-Forwarded-For: client, proxy1, proxy2, ...
            return header_value.split(",")[0].strip() or "unknown"
    return request.client.host if request.client else "unknown"


class RateLimiter:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._store: dict[str, list[datetime]] = {}
        self._lock = Lock()

    def _limit(self, action: str) -> int:
        return getattr(self.settings, f"rate_limit_{action}", 10)

    def _window(self, action: str) -> int:
        return getattr(self.settings, f"rate_limit_{action}_window_seconds", 60)

    def _is_allowed_memory(self, key: str, limit: int, window_seconds: int, now: datetime) -> bool:
        cutoff = now - timedelta(seconds=window_seconds)
        with self._lock:
            timestamps = [t for t in self._store.get(key, []) if t > cutoff]
            if len(timestamps) >= limit:
                self._store[key] = timestamps
                return False
            timestamps.append(now)
            self._store[key] = timestamps
            return True

    def _is_allowed_db(self, key: str, limit: int, window_seconds: int, now: datetime) -> bool:
        try:
            from deskid.db import get_db_session
            from deskid.models import RateLimitEntry

            cutoff = now - timedelta(seconds=window_seconds)
            with get_db_session() as session:
                # Count records within active window
                count_stmt = select(func.count(RateLimitEntry.id)).where(
                    RateLimitEntry.key == key,
                    RateLimitEntry.timestamp > cutoff,
                )
                count = session.execute(count_stmt).scalar() or 0
                if count >= limit:
                    return False

                # Insert entry and optionally prune expired entries
                entry = RateLimitEntry(key=key, timestamp=now)
                session.add(entry)

                # Opportunistic cleanup for this key
                session.query(RateLimitEntry).filter(
                    RateLimitEntry.key == key,
                    RateLimitEntry.timestamp <= cutoff,
                ).delete(synchronize_session=False)

                session.commit()
                return True
        except Exception:
            if getattr(self.settings, "rate_limit_fail_closed", False):
                return False
            return self._is_allowed_memory(key, limit, window_seconds, now)

    def _get_redis_client(self):
        if not hasattr(self, "_redis_client") or self._redis_client is None:
            import redis

            self._redis_client = redis.Redis.from_url(
                self.settings.rate_limit_redis_url,
                decode_responses=False,
                socket_timeout=2.0,
            )
        return self._redis_client

    def _is_allowed_redis(self, key: str, limit: int, window_seconds: int, now: datetime) -> bool:
        redis_url = self.settings.rate_limit_redis_url
        if not redis_url:
            if getattr(self.settings, "rate_limit_fail_closed", False):
                return False
            return self._is_allowed_memory(key, limit, window_seconds, now)

        try:
            import uuid

            r = self._get_redis_client()
            now_ts = now.timestamp()
            cutoff_ts = now_ts - window_seconds
            redis_key = f"rl:{key}"
            member = f"{now_ts}:{uuid.uuid4().hex}"

            pipe = r.pipeline()
            pipe.zremrangebyscore(redis_key, 0, cutoff_ts)
            pipe.zcard(redis_key)
            pipe.zadd(redis_key, {member: now_ts})
            pipe.expire(redis_key, window_seconds + 10)
            results = pipe.execute()

            current_count = results[1]
            if current_count >= limit:
                # Remove newly inserted member so rejected attempts don't pollute window
                r.zrem(redis_key, member)
                return False
            return True
        except Exception:
            if getattr(self.settings, "rate_limit_fail_closed", False):
                return False
            # Fall back to memory on redis connection issue
            return self._is_allowed_memory(key, limit, window_seconds, now)

    def is_allowed(self, identifier: str, action: str) -> bool:
        # 1. Global Enable/Disable flag check
        if not getattr(self.settings, "rate_limit_enabled", True):
            return True

        key = f"{action}:{identifier}"
        limit = self._limit(action)
        window_seconds = self._window(action)
        now = datetime.now(timezone.utc)

        backend = getattr(self.settings, "rate_limit_backend", "memory").lower()
        if backend == "db":
            return self._is_allowed_db(key, limit, window_seconds, now)
        elif backend == "redis":
            return self._is_allowed_redis(key, limit, window_seconds, now)
        else:
            return self._is_allowed_memory(key, limit, window_seconds, now)


def rate_limit_dependency(action: str):
    """Returns a FastAPI dependency that enforces rate limits by client IP."""

    def _limit(request: Request) -> None:
        settings = get_settings()
        if not getattr(settings, "rate_limit_enabled", True):
            return

        identifier = _client_ip(request)
        limiter: RateLimiter = request.app.state.rate_limiter
        if not limiter.is_allowed(identifier, action):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )

    return _limit
