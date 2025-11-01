import aioredis
from app.config import settings

redis = None

async def get_redis():
    global redis
    if redis is None:
        redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return redis

async def save_seen_message(message_id: str):
    r = await get_redis()
    await r.set(f"seen:{message_id}", "1", ex=60*60*24*7)  # 7 days TTL

async def has_seen_message(message_id: str) -> bool:
    r = await get_redis()
    v = await r.get(f"seen:{message_id}")
    return v is not None
