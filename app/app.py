# app.py
import os
import sys
import json
import signal
import logging

import tornado.ioloop
import tornado.autoreload
from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.httputil import HTTPServerRequest
from tornado.web import RequestHandler, Application, Finish

import mylog
from redis_connection_async import RedisConnectionAsync
from records_service import RecordsService


def is_dev_mode() -> bool:
    """Return True if running in development (enables autoreload)."""
    return os.environ.get("MODE_ENV", "").lower() not in {"prod", "production"}


def parse_json_body(request: HTTPServerRequest) -> dict:
    """Parse JSON body safely and return a dict. Raise ValueError on errors."""
    try:
        return json.loads(request.body)
    except Exception as exc:
        raise ValueError(f"Invalid JSON: {exc}")


def require_str(d: dict, key: str) -> str:
    """Require a non-empty string field from a dict payload."""
    v = d.get(key)
    if not isinstance(v, str) or not v:
        raise ValueError(f"Missing or invalid '{key}'.")
    return v


def optional_any(d: dict, key: str):
    """Return a value or None from dict without validation."""
    return d.get(key)


class SecureHandler(RequestHandler):
    def prepare(self):
        """Header-based API key auth; short-circuits request on failure."""
        expected_key = os.environ.get("API_SECRET_KEY")
        if not expected_key:
            logging.error("API_SECRET_KEY not set in environment variables.")
            self.set_status(500)
            self.write({"error": "Internal Server Error: API key not configured"})
            raise Finish()

        received_key = self.request.headers.get("X-API-KEY")
        if received_key != expected_key:
            self.set_status(401)
            self.write({"error": "Unauthorized"})
            raise Finish()


class HealthHandler(RequestHandler):
    def get(self):
        """Unauthenticated liveness endpoint."""
        global VERSION
        self.write({"status": "ok", "message": "pong", "version": VERSION})


class RecordHandler(SecureHandler):
    """POST /record  -> upsert (input + optional output)
       GET  /record  -> fetch one (user_id, match)
    """

    async def post(self):
        try:
            body = parse_json_body(self.request)

            user_id = require_str(body, "user_id")
            match_id = require_str(body, "match")
            input_data = optional_any(body, "input")
            output_data = optional_any(body, "output")
        except ValueError as e:
            self.set_status(400)
            self.write({"error": str(e)})
            return

        try:
            res = await RecordsService.upsert(user_id, match_id, input_data, output_data)
        except Exception:
            logging.exception("[upsert] failed")
            self.set_status(500)
            self.write({"error": "failed to upsert record"})
            return

        self.write({"status": "ok", **res})

    async def get(self):
        user_id = self.get_argument("user_id", default="")
        match_id = self.get_argument("match", default="")

        if not user_id or not match_id:
            self.set_status(400)
            self.write({"error": "user_id and match are required"})
            return

        try:
            rec = await RecordsService.get_one(user_id, match_id)
        except Exception:
            logging.exception("[get_one] failed")
            self.set_status(500)
            self.write({"error": "failed to fetch record"})
            return

        if rec:
            self.write(rec)
        else:
            self.set_status(404)
            self.write({"error": "not found"})


class RecordSetOutputHandler(SecureHandler):
    """PUT /record/output -> set/replace output only."""

    async def put(self):
        try:
            body = parse_json_body(self.request)
            user_id = require_str(body, "user_id")
            match_id = require_str(body, "match")
            if "output" not in body:
                raise ValueError("Missing 'output'.")
            output_data = body["output"]
        except ValueError as e:
            self.set_status(400)
            self.write({"error": str(e)})
            return

        try:
            res = await RecordsService.set_output(user_id, match_id, output_data)
        except Exception:
            logging.exception("[set_output] failed")
            self.set_status(500)
            self.write({"error": "failed to set output"})
            return

        self.write({"status": "ok", **res})


class RecordsGetRecentHandler(SecureHandler):
    """GET /records?user_id=...&limit=10&offset=0
       POST /records (JSON: {user_id, limit, offset})
       Returns most-recent N records with pagination.
    """
    async def _respond_recent(self, user_id: str, limit_value, offset_value) -> None:
        if not user_id:
            self.set_status(400)
            self.write({"error": "user_id is required"})
            return

        try:
            limit = int(limit_value if limit_value is not None else 10)
            offset = int(offset_value if offset_value is not None else 0)
            if limit <= 0 or offset < 0:
                raise ValueError("limit must be a positive integer and offset a non-negative integer.")
        except ValueError as e:
            self.set_status(400)
            self.write({"error": str(e)})
            return

        try:
            items = await RecordsService.get_recent(user_id, limit, offset)
        except Exception:
            logging.exception("[get_recent] failed")
            self.set_status(500)
            self.write({"error": "failed to fetch recent records"})
            return

        self.write({"user_id": user_id, "count": len(items), "items": items, "offset": offset, "limit": limit})

    async def get(self):
        user_id = self.get_argument("user_id", default="")
        limit_value = self.get_argument("limit", default="10")
        offset_value = self.get_argument("offset", default="0")

        await self._respond_recent(user_id, limit_value, offset_value)

    async def post(self):
        try:
            body = parse_json_body(self.request)
            user_id = require_str(body, "user_id")
            limit_value = body.get("limit", 10)
            offset_value = body.get("offset", 0)

        except ValueError as e:
            self.set_status(400)
            self.write({"error": str(e)})
            return

        await self._respond_recent(user_id, limit_value, offset_value)


def make_app() -> Application:
    return Application([
        (r"/ping", HealthHandler),
        (r"/record", RecordHandler),                 # GET + POST
        (r"/record/output", RecordSetOutputHandler), # PUT
        (r"/records", RecordsGetRecentHandler),      # GET + POST
    ])


def install_signal_handlers(ioloop: tornado.ioloop.IOLoop):
    """Graceful shutdown on SIGTERM/SIGINT."""
    def _signal(sig, frame):
        logging.info(f"Received signal {sig}, shutting down...")
        ioloop.add_callback_from_signal(ioloop.stop)

    signal.signal(signal.SIGTERM, _signal)
    signal.signal(signal.SIGINT, _signal)


async def start_async_redis():
    """Start async Redis and exit early on failure."""
    try:
        await RedisConnectionAsync.start(
            host=os.environ.get("REDIS_SERVER", "localhost"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            password=os.environ.get("REDIS_PASSWORD", "") or None,
        )
    except Exception:
        logging.exception("Failed to connect to Redis at startup.")
        sys.exit(1)


if __name__ == "__main__":
    VERSION = 3
    mylog.start()

    AsyncIOMainLoop().install()
    loop = tornado.ioloop.IOLoop.current()

    loop.run_sync(start_async_redis)

    app = make_app()
    app.listen(int(os.environ.get("PORT", "8890")))

    if is_dev_mode():
        tornado.autoreload.start()
        logging.info("Autoreload enabled (dev mode).")

    install_signal_handlers(loop)
    logging.info(f"Server started version {VERSION}")

    try:
        loop.start()
    finally:
        loop.run_sync(RedisConnectionAsync.close)
        logging.info("Server stopped")
