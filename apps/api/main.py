from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from core.config import settings
from core.tenant import TenantIsolationMiddleware
from routers import auth, users, consent, assessments, profiles, copilot, plans, org, coach, governance

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ICF AI Copilot API starting", env=settings.ENVIRONMENT)
    yield
    logger.info("ICF AI Copilot API stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="ICF AI Copilot API",
        description="Decision Intelligence platform — powered by IBM watsonx.ai",
        version="0.1.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(TenantIsolationMiddleware)

    prefix = "/api/v1"
    app.include_router(auth.router, prefix=prefix, tags=["auth"])
    app.include_router(users.router, prefix=prefix, tags=["users"])
    app.include_router(consent.router, prefix=prefix, tags=["consent"])
    app.include_router(assessments.router, prefix=prefix, tags=["assessments"])
    app.include_router(profiles.router, prefix=prefix, tags=["profiles"])
    app.include_router(copilot.router, prefix=prefix, tags=["copilot"])
    app.include_router(plans.router, prefix=prefix, tags=["plans"])
    app.include_router(org.router, prefix=prefix, tags=["org"])
    app.include_router(coach.router, prefix=prefix, tags=["coach"])
    app.include_router(governance.router, prefix=prefix, tags=["governance"])

    @app.get("/health", tags=["system"])
    async def health():
        return {"status": "ok", "version": "0.1.0", "env": settings.ENVIRONMENT}

    return app


app = create_app()
