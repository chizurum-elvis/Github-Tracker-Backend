import os
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
ENV = os.getenv("ENV", "development")  

if not REDIS_URL:
    raise ValueError("Missing REDIS_URL in environment variables")

ssl_options = {}
if REDIS_URL.startswith("rediss://"):
    if ENV == "development":
        ssl_options["ssl_cert_reqs"] = None 
    else:
        ssl_options["ssl_cert_reqs"] = "required"  

try:
    redis_client = redis.from_url(
        REDIS_URL,
        decode_responses=True,
        **ssl_options  
    )
    redis_client.ping()
    print(f"[✔] Connected to Redis ({ENV} mode)")
except redis.RedisError as e:
    raise ConnectionError(f"[✘] Failed to connect to Redis: {e}")