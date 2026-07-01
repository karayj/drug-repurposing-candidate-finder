from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.dependencies import get_cache
from app.services.cache_service import CacheService

router = APIRouter()


@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
    cache: CacheService = Depends(get_cache)
):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        print(f"Database health check error: {e}")
        db_status = "unhealthy"

    cache_status = "healthy"
    try:
        if cache.redis_client:
            await cache.redis_client.ping()
    except Exception:
        cache_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" and cache_status == "healthy" else "degraded",
        "database": db_status,
        "cache": cache_status
    }
