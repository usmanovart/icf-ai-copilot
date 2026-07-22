"""
Tenant isolation middleware.

Every request from an authenticated user is stamped with:
  - request.state.user_id
  - request.state.org_id  (may be None for individual users)

This middleware only reads the JWT sub/org claims for stamping.
Actual DB-level isolation is enforced in each service method
by always filtering queries with these values.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from core.security import verify_clerk_token


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request.state.user_id = None
        request.state.org_id = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):]
            try:
                payload = verify_clerk_token(token)
                request.state.user_id = payload.get("sub")
                # Clerk puts the active org in the 'org_id' claim
                request.state.org_id = payload.get("org_id")
            except Exception:
                # Middleware must not block unauthenticated routes
                pass

        response = await call_next(request)
        return response
