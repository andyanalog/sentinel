from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from sentinel.api.dependencies import get_container
from sentinel.container import Container

router = APIRouter(prefix="/v1/dashboard", tags=["dashboard"])


@router.get("/events")
async def events(
    limit: int = Query(100, ge=1, le=500),
    since: int | None = Query(None),
    container: Container = Depends(get_container),
) -> dict:
    items = [asdict(e) for e in container.feed.recent(limit=limit, since_seq=since)]
    return {
        "cursor": container.feed.total,
        "counts": container.feed.counts_by_action(),
        "events": items,
    }


@router.get("/timeseries")
async def timeseries(
    window: int = Query(300, ge=30, le=3600),
    bucket: int = Query(5, ge=1, le=300),
    container: Container = Depends(get_container),
) -> dict:
    return container.feed.timeseries(window_seconds=window, bucket_seconds=bucket)


@router.get("/fingerprints")
async def fingerprints(
    limit: int = Query(10, ge=1, le=50),
    container: Container = Depends(get_container),
) -> dict:
    return {"items": container.feed.top_fingerprints(limit=limit)}


@router.get("/operators")
async def operators(
    container: Container = Depends(get_container),
) -> dict:
    reg = container.operators
    ops = list(getattr(reg, "_by_id", {}).values())

    out = []
    for op in ops:
        balance = await container.pool.balance(op.id)
        out.append(
            {
                "id": op.id,
                "name": op.name,
                "balance_usdc": round(balance, 6),
            }
        )
    return {
        "items": out,
        "eval_cost_usdc": container.settings.eval_cost_usdc,
    }
