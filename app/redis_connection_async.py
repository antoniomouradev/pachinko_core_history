# redis_connection_async.py
# Async Redis connection wrapper using redis.asyncio

from __future__ import annotations

import logging
from typing import Optional
import redis.asyncio as aioredis  # pip install "redis>=4.2"


class RedisConnectionAsync:
    """Async Redis wrapper with a single shared connection pool."""

    _client: Optional[aioredis.Redis] = None

    @classmethod
    async def start(
        cls,
        host: str,
        port: int,
        password: Optional[str] = None,
        db: int = 0,
    ):
        """Initialize a global async Redis client."""
        cls._client = aioredis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            encoding="utf-8",
            decode_responses=True,
        )

        pong = await cls._client.ping()
        if pong is not True:
            raise RuntimeError("Redis PING failed")

        logging.info(f"[Redis] Connected to {host}:{port}, db={db}")

    @classmethod
    def client(cls) -> aioredis.Redis:
        """Return the shared async Redis client."""
        if cls._client is None:
            raise RuntimeError("Redis not started. Call RedisConnectionAsync.start(...) first.")
        return cls._client

    @classmethod
    async def close(cls):
        """Gracefully close the client/pool."""
        if cls._client is not None:
            await cls._client.close()
            cls._client = None
            logging.info("[Redis] Connection closed")
