import redis
from config import settings

redis_pool = redis.ConnectionPool.from_url(settings.CELERY_BROKER_URL, decode_responses=True)

def get_redis_connection():
    """Provides a connection from the pool."""
    return redis.Redis(connection_pool=redis_pool)