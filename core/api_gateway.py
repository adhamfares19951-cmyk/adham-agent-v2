"""Central API Gateway & Resilience Shield for Adham Agent Enterprise OS.
Provides:
1. SQLite Caching: Persistent response caching with TTL to minimize redundant calls and conserve API quotas.
2. Token-Bucket Rate Limiter: Asynchronous domain-aware rate limiting preventing HTTP 429 bans and IP throttling.
3. Retry & Timeout Handler: Smart exponential backoff with transient error recovery and connection pooling.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

import config
import memory

log = logging.getLogger("core.api_gateway")

DB_PATH = getattr(config, "BASE_DIR", Path(__file__).resolve().parent.parent) / "agent_memory.db"


# ==============================================================================
# Response Wrapper
# ==============================================================================

@dataclass
class GatewayResponse:
    """Standardized normalized response object for all gateway requests."""
    status_code: int
    text: str
    headers: dict[str, str] = field(default_factory=dict)
    cache_hit: bool = False
    latency_ms: int = 0
    url: str = ""
    method: str = "GET"

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        """Parses response text into JSON dict or list."""
        try:
            return json.loads(self.text)
        except Exception as e:
            log.warning("GatewayResponse JSON parse failed for %s: %s", self.url, e)
            return None


# ==============================================================================
# Token-Bucket Rate Limiter
# ==============================================================================

class TokenBucket:
    """Thread/Asyncio-safe token bucket for rate-limiting domain requests."""

    def __init__(self, capacity: float, refill_rate: float) -> None:
        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)  # tokens per second
        self.tokens = float(capacity)
        self.last_updated = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self, tokens_needed: float = 1.0) -> float:
        """Waits until enough tokens are available and consumes them. Returns wait time in seconds."""
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_updated
            self.last_updated = now

            # Refill tokens according to elapsed time
            self.tokens = min(self.capacity, self.tokens + (elapsed * self.refill_rate))

            if self.tokens >= tokens_needed:
                self.tokens -= tokens_needed
                return 0.0

            # Compute wait time needed
            needed = tokens_needed - self.tokens
            wait_seconds = needed / self.refill_rate if self.refill_rate > 0 else 1.0
            await asyncio.sleep(wait_seconds)
            self.last_updated = time.monotonic()
            self.tokens = 0.0
            return wait_seconds


# Domain-specific presets (requests/sec and burst capacities)
DEFAULT_RATE_LIMITS: dict[str, tuple[float, float]] = {
    # domain substring: (capacity, refill_rate_per_sec)
    "binance.com": (20.0, 10.0),
    "coingecko.com": (5.0, 0.5),
    "gold-api.com": (10.0, 2.0),
    "er-api.com": (10.0, 2.0),
    "ip-api.com": (5.0, 0.75),            # max 45 requests / min
    "openstreetmap.org": (2.0, 1.0),       # strict Nominatim 1 req/sec policy
    "default": (10.0, 5.0),
}


# ==============================================================================
# Core API Gateway
# ==============================================================================

class APIGateway:
    """Central resilience gateway for all external HTTP requests."""

    def __init__(self, db_path: Path | str = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self._rate_limiters: dict[str, TokenBucket] = {}
        self._limiter_lock = asyncio.Lock()
        self._client: httpx.AsyncClient | None = None
        self._ensure_cache_table()

    def _ensure_cache_table(self) -> None:
        """Ensures the api_cache table and indexes exist in SQLite."""
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS api_cache (
                        cache_key TEXT PRIMARY KEY,
                        url TEXT NOT NULL,
                        method TEXT NOT NULL DEFAULT 'GET',
                        status_code INTEGER NOT NULL,
                        response_body TEXT NOT NULL,
                        headers_json TEXT NOT NULL DEFAULT '{}',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at INTEGER NOT NULL
                    );
                    CREATE INDEX IF NOT EXISTS idx_api_cache_expires ON api_cache (expires_at);
                """)
        except Exception as e:
            log.warning("Could not verify api_cache table in %s: %s", self.db_path, e)

    def _get_cache(self, cache_key: str) -> GatewayResponse | None:
        """Retrieves cached response if not expired."""
        now = int(time.time())
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT url, method, status_code, response_body, headers_json, expires_at "
                    "FROM api_cache WHERE cache_key = ? AND expires_at > ?",
                    (cache_key, now),
                ).fetchone()

                if row:
                    try:
                        headers = json.loads(row["headers_json"])
                    except Exception:
                        headers = {}
                    return GatewayResponse(
                        status_code=row["status_code"],
                        text=row["response_body"],
                        headers=headers,
                        cache_hit=True,
                        latency_ms=1,
                        url=row["url"],
                        method=row["method"],
                    )
        except Exception as e:
            log.debug("Cache lookup failed for %s: %s", cache_key, e)
        return None

    def _set_cache(
        self,
        cache_key: str,
        url: str,
        method: str,
        status_code: int,
        response_body: str,
        headers: dict,
        ttl_seconds: int,
    ) -> None:
        """Stores a response in SQLite with calculated expiration time."""
        if ttl_seconds <= 0:
            return
        expires_at = int(time.time()) + ttl_seconds
        headers_str = json.dumps(dict(headers or {}), ensure_ascii=False)
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO api_cache "
                    "(cache_key, url, method, status_code, response_body, headers_json, expires_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (cache_key, url, method, status_code, response_body, headers_str, expires_at),
                )
                conn.commit()
        except Exception as e:
            log.debug("Cache save failed for %s: %s", url, e)

    def clear_expired_cache(self) -> int:
        """Removes expired entries from api_cache. Returns number of purged rows."""
        now = int(time.time())
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                cur = conn.execute("DELETE FROM api_cache WHERE expires_at <= ?", (now,))
                conn.commit()
                return cur.rowcount
        except Exception as e:
            log.warning("Clear expired cache failed: %s", e)
            return 0

    def get_cache_stats(self) -> dict[str, Any]:
        """Returns statistics about current cache utilization."""
        now = int(time.time())
        try:
            with sqlite3.connect(self.db_path, timeout=30.0) as conn:
                total = conn.execute("SELECT COUNT(*) FROM api_cache").fetchone()[0]
                active = conn.execute("SELECT COUNT(*) FROM api_cache WHERE expires_at > ?", (now,)).fetchone()[0]
                expired = total - active
                return {"total_entries": total, "active_entries": active, "expired_entries": expired}
        except Exception:
            return {"total_entries": 0, "active_entries": 0, "expired_entries": 0}

    def _generate_cache_key(self, method: str, url: str, params: dict | None, json_data: Any) -> str:
        """Produces a deterministic SHA256 cache key from request signature."""
        param_str = json.dumps(params or {}, sort_keys=True, ensure_ascii=False)
        body_str = json.dumps(json_data, sort_keys=True, ensure_ascii=False) if json_data else ""
        raw = f"{method.upper()}:{url}:{param_str}:{body_str}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def _get_rate_limiter_for_url(self, url: str) -> TokenBucket:
        """Matches URL domain against rate limit presets."""
        hostname = urlparse(url).netloc.lower()
        async with self._limiter_lock:
            if hostname in self._rate_limiters:
                return self._rate_limiters[hostname]

            # Find matching preset or default
            capacity, refill = DEFAULT_RATE_LIMITS["default"]
            for dom_pat, (cap, ref) in DEFAULT_RATE_LIMITS.items():
                if dom_pat != "default" and dom_pat in hostname:
                    capacity, refill = cap, ref
                    break

            bucket = TokenBucket(capacity=capacity, refill_rate=refill)
            self._rate_limiters[hostname] = bucket
            return bucket

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0),
                follow_redirects=True,
                headers={"User-Agent": "AdhamAgent-EnterpriseOS/2.0 (+https://github.com/adham-agent)"},
            )
        return self._client

    async def close(self) -> None:
        """Closes the underlying HTTP client session."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        json_data: Any = None,
        data: Any = None,
        headers: dict | None = None,
        ttl_seconds: int = 300,
        max_retries: int = 3,
        timeout_seconds: float = 10.0,
        force_refresh: bool = False,
    ) -> GatewayResponse:
        """Executes an HTTP request governed by rate limiting, caching, and retry policies."""
        method_upper = method.upper()
        cache_key = self._generate_cache_key(method_upper, url, params, json_data)

        # 1. Cache Check (for idempotent GET requests)
        if method_upper == "GET" and not force_refresh:
            cached = self._get_cache(cache_key)
            if cached is not None:
                log.debug("Cache HIT for %s (Key: %s...)", url, cache_key[:8])
                return cached

        # 2. Rate Limiting enforcement
        bucket = await self._get_rate_limiter_for_url(url)
        waited = await bucket.acquire(1.0)
        if waited > 0:
            log.debug("Rate-limiter waited %.2fs for %s", waited, url)

        # 3. Connection and Retry Execution Loop
        client = await self._get_client()
        req_headers = dict(headers or {})
        last_error: Exception | None = None
        delays = [0.5, 1.5, 3.0]

        for attempt in range(max_retries):
            t0 = time.monotonic()
            try:
                resp = await client.request(
                    method=method_upper,
                    url=url,
                    params=params,
                    json=json_data,
                    data=data,
                    headers=req_headers,
                    timeout=timeout_seconds,
                )
                latency = int((time.monotonic() - t0) * 1000)

                # Transient rate-limit or server error retry (429, 502, 503, 504)
                if resp.status_code in (429, 502, 503, 504) and attempt < max_retries - 1:
                    sleep_time = delays[min(attempt, len(delays) - 1)]
                    log.warning("HTTP %s from %s, retrying in %.1fs (attempt %d/%d)",
                                resp.status_code, url, sleep_time, attempt + 1, max_retries)
                    await asyncio.sleep(sleep_time)
                    continue

                resp_obj = GatewayResponse(
                    status_code=resp.status_code,
                    text=resp.text,
                    headers=dict(resp.headers),
                    cache_hit=False,
                    latency_ms=latency,
                    url=url,
                    method=method_upper,
                )

                # 4. Cache only successful GET responses
                if method_upper == "GET" and resp_obj.is_success and ttl_seconds > 0:
                    self._set_cache(
                        cache_key=cache_key,
                        url=url,
                        method=method_upper,
                        status_code=resp.status_code,
                        response_body=resp.text,
                        headers=dict(resp.headers),
                        ttl_seconds=ttl_seconds,
                    )

                return resp_obj

            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError, httpx.NetworkError) as e:
                last_error = e
                latency = int((time.monotonic() - t0) * 1000)
                if attempt < max_retries - 1:
                    sleep_time = delays[min(attempt, len(delays) - 1)]
                    log.warning("Network error '%s' on %s, retrying in %.1fs (attempt %d/%d)",
                                e, url, sleep_time, attempt + 1, max_retries)
                    await asyncio.sleep(sleep_time)
                else:
                    log.error("Network request failed after %d retries for %s: %s", max_retries, url, e)

        # Fallback error response
        return GatewayResponse(
            status_code=504 if isinstance(last_error, httpx.TimeoutException) else 503,
            text=json.dumps({"error": str(last_error or "Network connection failed")}),
            headers={},
            cache_hit=False,
            latency_ms=0,
            url=url,
            method=method_upper,
        )

    async def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        ttl_seconds: int = 300,
        max_retries: int = 3,
        force_refresh: bool = False,
    ) -> GatewayResponse:
        """Shortcut helper for GET requests."""
        return await self.request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            ttl_seconds=ttl_seconds,
            max_retries=max_retries,
            force_refresh=force_refresh,
        )

    async def post(
        self,
        url: str,
        params: dict | None = None,
        json_data: Any = None,
        headers: dict | None = None,
        ttl_seconds: int = 0,
        max_retries: int = 3,
    ) -> GatewayResponse:
        """Shortcut helper for POST requests."""
        return await self.request(
            method="POST",
            url=url,
            params=params,
            json_data=json_data,
            headers=headers,
            ttl_seconds=ttl_seconds,
            max_retries=max_retries,
        )


# ==============================================================================
# Global Singleton
# ==============================================================================

_GATEWAY_INSTANCE: APIGateway | None = None


def get_api_gateway() -> APIGateway:
    """Returns the shared APIGateway singleton."""
    global _GATEWAY_INSTANCE
    if _GATEWAY_INSTANCE is None:
        _GATEWAY_INSTANCE = APIGateway()
    return _GATEWAY_INSTANCE
