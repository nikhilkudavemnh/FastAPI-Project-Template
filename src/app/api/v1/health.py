from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SettingsDep
from app.db.session import SessionDep

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live(settings: SettingsDep) -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@router.get("/ready")
async def ready(session: SessionDep, settings: SettingsDep) -> dict[str, Any]:
    checks: dict[str, str] = {}
    try:
        await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:  # pragma: no cover
        checks["database"] = f"error: {e}"
    if settings.redis_url:
        try:
            import redis.asyncio as aioredis

            r = aioredis.from_url(settings.redis_url)
            await r.ping()
            await r.aclose()
            checks["redis"] = "ok"
        except Exception as e:  # pragma: no cover
            checks["redis"] = f"error: {e}"
    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "service": settings.service_name, "checks": checks}
