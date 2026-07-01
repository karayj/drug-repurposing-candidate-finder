import json
from typing import Optional, Any
from redis import asyncio as aioredis
from app.config import get_settings


class CacheService:
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[aioredis.Redis] = None

    async def connect(self):
        try:
            self.redis_client = await aioredis.from_url(
                self.settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        except Exception as e:
            print(f"Redis connection error: {e}")
            self.redis_client = None

    async def disconnect(self):
        if self.redis_client:
            await self.redis_client.close()

    async def get(self, key: str) -> Optional[Any]:
        if not self.redis_client:
            return None

        try:
            cached = await self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            print(f"Cache get error: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        if not self.redis_client:
            return

        try:
            ttl = ttl or self.settings.REDIS_CACHE_TTL
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
        except Exception as e:
            print(f"Cache set error: {e}")

    def generate_key(self, prefix: str, *args) -> str:
        return f"{prefix}:{':'.join(str(arg).lower().replace(' ', '_') for arg in args)}"
