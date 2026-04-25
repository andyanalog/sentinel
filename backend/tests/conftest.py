import pytest
from httpx import ASGITransport, AsyncClient

from sentinel.config import Settings
from sentinel.main import create_app


@pytest.fixture
def dummy_settings() -> Settings:
    return Settings(SENTINEL_DUMMY=True, SENTINEL_API_SECRET="test-secret")


@pytest.fixture
async def app(dummy_settings):
    return create_app(dummy_settings)


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        async with app.router.lifespan_context(app):
            yield c
