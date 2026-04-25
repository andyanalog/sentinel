from fastapi import APIRouter, Depends

from sentinel.api.dependencies import get_container
from sentinel.container import Container

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(container: Container = Depends(get_container)) -> dict:
    return {
        "status": "ok",
        "dummy_mode": container.settings.dummy_mode,
    }
