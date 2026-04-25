from fastapi import Depends, Header, HTTPException, Request, status

from sentinel.container import Container
from sentinel.models.operator import Operator


def get_container(request: Request) -> Container:
    container: Container = request.app.state.container
    return container


async def authenticate(
    authorization: str | None = Header(default=None),
    container: Container = Depends(get_container),
) -> Operator:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "missing bearer token"
        )
    api_key = authorization.split(" ", 1)[1].strip()

    if container.settings.dummy_mode:
        # In dummy mode, any key is accepted and mapped to a stable synthetic
        # operator so the demo can register zero operators and still work.
        op = await container.operators.by_api_key(api_key)
        if op is None:
            op = await container.operators.create(f"demo:{api_key[:8]}")
            # Rebind the key so the caller's key is the one of record.
            op.api_key = api_key
            container.operators._by_key[api_key] = op  # type: ignore[attr-defined]
            container.operators._by_id[op.id] = op  # type: ignore[attr-defined]
        return op

    op = await container.operators.by_api_key(api_key)
    if op is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid api key")
    return op
