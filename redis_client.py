import redis
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise ValueError("Missing REDIS_URL environment variable")

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)