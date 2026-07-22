"""
Clerk JWT verification using JWKS (RS256).
The JWKS client is cached; keys are refreshed automatically on rotation.
"""

import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, status
from functools import lru_cache

from core.config import settings


@lru_cache(maxsize=1)
def _get_jwks_client() -> PyJWKClient:
    return PyJWKClient(settings.CLERK_JWKS_URL)


def verify_clerk_token(token: str) -> dict:
    """
    Verify a Clerk-issued JWT and return the decoded payload.
    Raises HTTP 401 on any failure.
    """
    try:
        client = _get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )
