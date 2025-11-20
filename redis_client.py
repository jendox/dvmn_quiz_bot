import os

from redis import Redis


def connect_redis() -> Redis:
    return Redis(
        host=os.environ["REDIS_HOST"],
        port=int(os.environ["REDIS_PORT"]),
        username=os.environ["REDIS_USERNAME"],
        password=os.environ["REDIS_PASSWORD"],
        decode_responses=True,
    )
