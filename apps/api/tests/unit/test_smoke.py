"""
Smoke tests for the FastAPI application.

These tests verify the basic structure — they do NOT require a real DB or
real IBM credentials. External integrations are mocked.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """The /health endpoint should return 200 with status:ok."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


@pytest.mark.asyncio
async def test_protected_endpoint_without_token():
    """A protected endpoint should return 403 when no auth header is provided."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/users/me")

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_webhook_without_signature():
    """The Clerk webhook should reject requests with no svix headers."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/webhook",
            json={"type": "user.created", "data": {}},
        )
    # Should fail signature check — 400
    assert response.status_code == 400
