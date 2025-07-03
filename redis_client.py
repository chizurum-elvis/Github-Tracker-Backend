import os
import redis
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# Load environment variables
REDIS_URL = os.getenv("REDIS_URL")
ENV = os.getenv("ENV", "development")  # 'development' or 'production'

if not REDIS_URL:
    raise ValueError("Missing REDIS_URL in environment variables")

# SSL settings
ssl_options = {}

# In development, allow self-signed certs (if needed)
if REDIS_URL.startswith("rediss://"):
    if ENV == "development":
        ssl_options["ssl_cert_reqs"] = None  # Don't verify SSL cert in dev
    else:
        ssl_options["ssl_cert_reqs"] = "required"  # Strict validation in prod

# Create Redis client
try:
    redis_client = redis.from_url(
        REDIS_URL,
        decode_responses=True,
        **ssl_options
    )
    # Optional: Test connection
    redis_client.ping()
    print(f"[✔] Connected to Redis ({ENV} mode)")
except redis.RedisError as e:
    raise ConnectionError(f"[✘] Failed to connect to Redis: {e}")