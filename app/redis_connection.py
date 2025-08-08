from datetime import timedelta
import pickle
import redis
import logging


class RedisConnection:
    _instance = None
    host = None
    port = None
    password = None
    TTL_SECONDS = int(timedelta(days=30).total_seconds())

    @staticmethod
    def start(host, port, password):
        RedisConnection.r = RedisConnection(host, port, password)

    def __init__(self, host, port, password) -> None:
        RedisConnection.host = host
        RedisConnection.port = port
        RedisConnection.password = password
        RedisConnection.connect()

    @staticmethod
    def connect():
        RedisConnection._instance = redis.StrictRedis(
            host=RedisConnection.host,
            port=RedisConnection.port,
            db=0,
            password=RedisConnection.password
        )
        try:
            if RedisConnection._instance.ping():
                logging.info(f"Redis connected on port: {RedisConnection.port}")
        except redis.ConnectionError as e:
            logging.error(f"[Redis] ConnectionError: {e}")

    @staticmethod
    def save_raw(name, obj, ttl=TTL_SECONDS):
        try:
            serialized = pickle.dumps(obj)
            RedisConnection._instance.set(name, serialized, ex=ttl)
        except Exception as e:
            logging.error(f"[Redis Save] {e}")
            RedisConnection.connect()

    @staticmethod
    def load_raw(name):
        try:
            data = RedisConnection._instance.get(name)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logging.error(f"[Redis Load] {e}")
            RedisConnection.connect()

    @staticmethod
    def delete(name):
        try:
            return RedisConnection._instance.delete(name)
        except Exception as e:
            logging.error(f"[Redis Delete] {e}")
            RedisConnection.connect()

    @staticmethod
    def save_input(uuid, payload):
        key = f"payload:{uuid}"
        current = RedisConnection.load_raw(key) or {}
        current["input"] = payload
        RedisConnection.save_raw(key, current)

    @staticmethod
    def save_output(uuid, payload):
        key = f"payload:{uuid}"
        current = RedisConnection.load_raw(key) or {}
        current["output"] = payload
        RedisConnection.save_raw(key, current)

    @staticmethod
    def get_payload(uuid):
        return RedisConnection.load_raw(f"payload:{uuid}")

