from app.database import get_db
from app.services.cache_service import CacheService
from functools import lru_cache

_cache_service_instance = None


async def get_cache() -> CacheService:
    global _cache_service_instance
    if _cache_service_instance is None:
        _cache_service_instance = CacheService()
        await _cache_service_instance.connect()
    return _cache_service_instance
