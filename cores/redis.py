from cores.config import settings
from ghkit.database import redis_client

REDIS = redis_client.RedisClient(
    host=settings.redis.host,
    port=settings.redis.port,
    password=settings.redis.password,
    db=settings.redis.default_db
)
