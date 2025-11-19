from redis import Redis

from config import Config

redis = Redis(
    host=Config.REDIS_HOST,
    port=Config.REDIS_PORT,
    username=Config.REDIS_USERNAME,
    password=Config.REDIS_PASSWORD,
    decode_responses=True,
)
