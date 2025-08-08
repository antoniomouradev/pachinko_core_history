import os
import json
import logging
import tornado.web
import tornado.ioloop
import tornado.autoreload
from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

import mylog
from redis_connection import RedisConnection


class SecureHandler(tornado.web.RequestHandler):
    def prepare(self):
        expected_key = os.environ.get("API_SECRET_KEY")
        if not expected_key:
            logging.error("API_SECRET_KEY not set in environment variables.")
            self.set_status(500)
            self.finish({"error": "Internal Server Error: API key not configured"})
            return
        received_key = self.request.headers.get("X-API-KEY")
        if not expected_key or received_key != expected_key:
            self.set_status(401)
            self.finish({"error": "Unauthorized"})


class SaveInputHandler(SecureHandler):
    executor = ThreadPoolExecutor()

    @run_on_executor
    def _save(self, uuid, data):
        RedisConnection.save_input(uuid, data)

    async def post(self):
        uuid = self.get_argument("uuid")
        data = json.loads(self.request.body)
        await self._save(uuid, data)
        self.write({"status": "input saved", "uuid": uuid})


class SaveOutputHandler(SecureHandler):
    executor = ThreadPoolExecutor()

    @run_on_executor
    def _save(self, uuid, data):
        RedisConnection.save_output(uuid, data)

    async def post(self):
        uuid = self.get_argument("uuid")
        data = json.loads(self.request.body)
        await self._save(uuid, data)
        self.write({"status": "output saved", "uuid": uuid})


class GetPayloadHandler(SecureHandler):
    executor = ThreadPoolExecutor()

    @run_on_executor
    def _get(self, uuid):
        return RedisConnection.get_payload(uuid)

    async def get(self):
        uuid = self.get_argument("uuid")
        data = await self._get(uuid)
        if data:
            self.write(data)
        else:
            self.set_status(404)
            self.write({"error": "not found"})


def make_app():
    return tornado.web.Application([
        (r"/save_input", SaveInputHandler),
        (r"/save_output", SaveOutputHandler),
        (r"/get_payload", GetPayloadHandler),
    ])


if __name__ == "__main__":
    mylog.start()

    RedisConnection.start(
        host=os.environ.get("REDIS_SERVER", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        password=os.environ.get("REDIS_PASSWORD", "")
    )

    AsyncIOMainLoop().install()
    app = make_app()
    app.listen(8890)

    tornado.autoreload.start()

    logging.info("Server started")
    tornado.ioloop.IOLoop.current().start()
