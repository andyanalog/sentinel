from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        extra="ignore",
    )

    # Core
    env: str = Field("local", alias="SENTINEL_ENV")  # "local" or "prod"
    api_secret: str = Field("change-me", alias="SENTINEL_API_SECRET")
    dummy_mode: bool = Field(False, alias="SENTINEL_DUMMY")
    eval_cost_usdc: float = Field(0.0001, alias="EVAL_COST_USDC")
    allowed_origins: str = Field("", alias="ALLOWED_ORIGINS")

    @property
    def is_prod(self) -> bool:
        return self.env.lower() == "prod"

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins:
            return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
        return ["*"] if not self.is_prod else []

    # Data stores
    database_url: str = Field(
        "sqlite+aiosqlite:///:memory:",
        alias="DATABASE_URL",
    )
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")

    # Arc L1
    arc_rpc_url: str = Field("", alias="ARC_RPC_URL")
    arc_chain_id: int = Field(0, alias="ARC_CHAIN_ID")
    reputation_ledger_address: str = Field("", alias="REPUTATION_LEDGER_ADDRESS")
    operator_pool_address: str = Field("", alias="OPERATOR_POOL_ADDRESS")
    arc_usdc_address: str = Field(
        "0x3600000000000000000000000000000000000000", alias="ARC_USDC_ADDRESS"
    )
    sentinel_wallet_private_key: str = Field("", alias="SENTINEL_WALLET_PRIVATE_KEY")
    ledger_batch_size: int = Field(100, alias="LEDGER_BATCH_SIZE")
    ledger_batch_interval: int = Field(60, alias="LEDGER_BATCH_INTERVAL")
    pool_debit_interval: int = Field(30, alias="POOL_DEBIT_INTERVAL")

    # Circle (Gateway Nanopayments / x402)
    circle_api_key: str = Field("", alias="CIRCLE_API_KEY")
    circle_seller_address: str = Field("", alias="CIRCLE_SELLER_ADDRESS")
    circle_wallet_set_id: str = Field("", alias="CIRCLE_WALLET_SET_ID")

    @field_validator("database_url", mode="after")
    @classmethod
    def _coerce_asyncpg(cls, v: str) -> str:
        # Railway/Heroku-style Postgres URLs come as `postgres://` or
        # `postgresql://`. SQLAlchemy's async engine needs the `+asyncpg` driver.
        # Rewrite here so both local `.env` and managed providers work unchanged.
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
