# records_service.py
# Business logic for (user_id, match_id) records on Redis
from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from redis_connection_async import RedisConnectionAsync

# ---- NOVO: TTL padrão de 7 dias (em segundos)
TTL_SECONDS = 42 * 24 * 60 * 60  # 42 days

def _now_unix() -> float:
    """Epoch seconds (UTC). Used as sorted-set score for ordering."""
    return time.time()


def _now_iso_gmt_minus3() -> str:
    """Human-readable timestamp already converted to GMT-3 (no offset, no microseconds)."""
    t = time.gmtime(time.time() - 3 * 3600)  # shift -3 hours from UTC
    return time.strftime("%Y-%m-%d %H:%M:%S", t)


def key_record(user_id: str, match_id: str) -> str:
    return f"record:{user_id}:{match_id}"


def key_user_index(user_id: str) -> str:
    return f"user:{user_id}:records"


def _maybe_json_dump(v: Any) -> str:
    """Serialize dicts/lists as JSON; keep primitives/strings as-is."""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def _maybe_json_load(s: Optional[str]) -> Any:
    if s is None:
        return None
    try:
        return json.loads(s)
    except Exception:
        return s


class RecordsService:
    """High-level API for record storage and queries."""

    @staticmethod
    async def upsert(
        user_id: str,
        match_id: str,
        input_data: Optional[Any] = None,
        output_data: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Create or update a record. Sets created_at on first write; always updates updated_at.
        Also updates the per-user sorted index (ZSET) by the current epoch time.
        """
        r = RedisConnectionAsync.client()
        rec_key = key_record(user_id, match_id)
        idx_key = key_user_index(user_id)

        updated_at = _now_iso_gmt_minus3()
        score = _now_unix()

        mapping: Dict[str, str] = {
            "user_id": user_id,
            "match_id": match_id,
            "updated_at": updated_at,
        }
        if input_data is not None:
            mapping["input"] = _maybe_json_dump(input_data)
        if output_data is not None:
            mapping["output"] = _maybe_json_dump(output_data)

        pipe = r.pipeline()
        # enqueue commands (await each to satisfy asyncio pipeline)
        await pipe.hsetnx(rec_key, "created_at", updated_at)   # only on first write
        await pipe.hset(rec_key, mapping=mapping)
        await pipe.zadd(idx_key, {match_id: score})            # index by updated_at (epoch)

        await pipe.expire(rec_key, TTL_SECONDS)                # record expira em 7 dias (rolling TTL)
        await pipe.expire(idx_key, TTL_SECONDS)                # índice também expira se ficar inativo

        res = await pipe.execute()

        return {
            "ok": True,
            "user_id": user_id,
            "match_id": match_id,
            "updated_at": updated_at,
            "created_at_set": bool(res[0]),
        }

    @staticmethod
    async def set_output(user_id: str, match_id: str, output_data: Any) -> Dict[str, Any]:
        """Update only output; refresh updated_at and index."""
        return await RecordsService.upsert(user_id, match_id, input_data=None, output_data=output_data)

    @staticmethod
    async def get_one(user_id: str, match_id: str) -> Optional[Dict[str, Any]]:
        r = RedisConnectionAsync.client()
        rec_key = key_record(user_id, match_id)
        data = await r.hgetall(rec_key)
        if not data:
            return None

        return {
            "user_id": data.get("user_id") or user_id,
            "match_id": data.get("match_id") or match_id,
            "input": _maybe_json_load(data.get("input")),
            "output": _maybe_json_load(data.get("output")),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
        }

    @staticmethod
    async def get_recent(user_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Return most-recent N records for a user, ordered by updated_at desc, with offset and limit."""
        r = RedisConnectionAsync.client()
        idx_key = key_user_index(user_id)

        # Sanitize inputs
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        # Calculate start and stop index for ZREVRANGE
        start_index = offset
        stop_index = offset + limit - 1

        # Latest match_ids by score (descending)
        match_ids = await r.zrevrange(idx_key, start_index, stop_index)
        if not match_ids:
            return []

        # Batch fetch via pipeline
        pipe = r.pipeline()
        for mid in match_ids:
            await pipe.hgetall(key_record(user_id, mid))
        raw_list = await pipe.execute()

        out: List[Dict[str, Any]] = []
        stale_mids: List[str] = []

        for mid, raw in zip(match_ids, raw_list):
            if not raw:
                stale_mids.append(mid)
                continue
            out.append({
                "user_id": raw.get("user_id") or user_id,
                "match_id": raw.get("match_id") or mid,
                "input": _maybe_json_load(raw.get("input")),
                "output": _maybe_json_load(raw.get("output")),
                "created_at": raw.get("created_at"),
                "updated_at": raw.get("updated_at"),
            })

        if stale_mids:
            await r.zrem(idx_key, *stale_mids)

        return out
