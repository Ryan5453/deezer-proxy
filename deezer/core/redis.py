import redis.asyncio as redis

from deezer.core.config import redis_url

redis = redis.from_url(redis_url)
