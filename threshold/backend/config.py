from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = "THRESHOLD API"
    version: str = "1.0.0"
    api_v1_str: str = "/api/v1"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    database_url: str = f"sqlite:///{(BACKEND_DIR / 'threshold.db').as_posix()}"
    demo_mode: bool = True

    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    solana_rpc_url: str = "https://api.devnet.solana.com"
    solana_program_id: str = "threshold-demo-program"
    solana_usdc_mint: str = "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU"

    orthogonal_api_key: str = ""
    google_maps_api_key: str = ""
    gemini_api_key: str = "AIzaSyAQgrVLtCKbu8nJCUIU3gh-apFD16Rr77A"
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_database: str = "THRESHOLD_DB"
    snowflake_schema: str = "PUBLIC"

settings = Settings()
