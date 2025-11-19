import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    REDIS_HOST = os.environ["REDIS_HOST"]
    REDIS_PORT = int(os.environ["REDIS_PORT"])
    REDIS_USERNAME = os.environ["REDIS_USERNAME"]
    REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
    TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
    VK_TOKEN = os.environ["VK_TOKEN"]
