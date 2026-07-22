from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """
    All application settings sourced from environment variables.
    See infrastructure/.env.example for documentation.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # ─── Application ────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # ─── Database ───────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://icf:icf@localhost:5432/icf"
    REDIS_URL: str = "redis://localhost:6379/0"

    # ─── Clerk Auth ─────────────────────────────────────────────────
    CLERK_SECRET_KEY: str = ""
    CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_WEBHOOK_SECRET: str = ""
    CLERK_JWKS_URL: str = "https://api.clerk.dev/v1/jwks"

    # ─── IBM watsonx.ai ─────────────────────────────────────────────
    WATSONX_API_KEY: str = ""
    WATSONX_PROJECT_ID: str = ""
    WATSONX_URL: str = "https://us-south.ml.cloud.ibm.com"
    WATSONX_LLM_MODEL_ID: str = "ibm/granite-13b-chat-v2"
    WATSONX_EMBEDDING_MODEL_ID: str = "ibm/slate-125m-english-rtrvr"

    # ─── Watson Discovery ───────────────────────────────────────────
    WATSON_DISCOVERY_API_KEY: str = ""
    WATSON_DISCOVERY_URL: str = ""
    WATSON_DISCOVERY_PROJECT_ID: str = ""

    # ─── watsonx.governance ─────────────────────────────────────────
    WATSONX_GOVERNANCE_URL: str = ""
    WATSONX_GOVERNANCE_API_KEY: str = ""

    # ─── Safety & Compliance ────────────────────────────────────────
    # Minimum cohort size for aggregated org/coach insights (re-identification guard)
    MIN_ANONYMIZATION_COHORT: int = 5
    # Active consent document version
    CONSENT_DOCUMENT_VERSION: str = "1.0"


settings = Settings()
