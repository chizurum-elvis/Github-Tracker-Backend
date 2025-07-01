import redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

if not REDIS_URL:
    raise ValueError("Missing REDIS_URL environment variable")

# Use redis.from_url and disable SSL cert check
redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    ssl_cert_reqs=None  # This disables strict SSL cert validation
)
