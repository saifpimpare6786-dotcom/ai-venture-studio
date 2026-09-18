"""
Authentication & Authorization middleware for AI Venture Studio.

Supports two modes:
1. **Development Mode** (default): Uses a simple API key header (X-User-ID) for local dev.
2. **Supabase Mode**: Validates JWT tokens from Supabase Auth when SUPABASE_URL is configured.

Usage in route handlers:
    from app.core.auth import get_current_user

    @router.get("/projects")
    async def list_projects(user_id: str = Depends(get_current_user)):
        return await db.list_projects(user_id=user_id)
"""

import os
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

try:
    from app.core.config import settings
except ImportError:
    from ..core.config import settings

# Optional JWT security scheme (won't enforce on dev mode)
_bearer_scheme = HTTPBearer(auto_error=False)

# Cache for decoded JWT user IDs (simple in-memory, resets on restart)
_jwt_cache: dict[str, str] = {}


def _is_supabase_auth_enabled() -> bool:
    """Check if Supabase Auth is configured for JWT validation."""
    return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)


async def _validate_supabase_jwt(token: str) -> str:
    """
    Validates a Supabase JWT and returns the user ID (sub claim).
    Uses the Supabase service role client to verify the token.
    """
    if token in _jwt_cache:
        return _jwt_cache[token]

    try:
        from supabase import create_client
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        user_response = client.auth.get_user(token)
        
        if user_response and user_response.user:
            user_id = user_response.user.id
            _jwt_cache[token] = user_id
            return user_id
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired token.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI dependency that extracts the authenticated user ID.

    Resolution order:
    1. If Bearer JWT token is supplied -> validate with Supabase JWT
    2. If X-User-ID header is present -> use it directly
    3. If query param 'token' or 'user_id' is present (e.g. for SSE) -> use it
    4. Fall back to 'default_founder' during development/debug mode
    """
    # 1. Check Bearer credentials or Authorization header
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    else:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif request.query_params.get("token"):
            token = request.query_params.get("token")

    if token:
        if _is_supabase_auth_enabled():
            try:
                return await _validate_supabase_jwt(token)
            except Exception as e:
                # If token was supplied but invalid, reject or log
                print(f"[Auth] Warning: JWT validation failed ({e}), checking fallback headers.")
        else:
            return token

    # 2. Check X-User-ID header
    dev_user_id = request.headers.get("X-User-ID", "").strip()
    if dev_user_id:
        return dev_user_id

    # 3. Check query param for SSE / links
    query_user_id = request.query_params.get("user_id", "").strip()
    if query_user_id:
        return query_user_id

    # 4. Fallback in DEBUG mode or local operation
    if settings.DEBUG or not _is_supabase_auth_enabled():
        return "default_founder"

    raise HTTPException(
        status_code=401, 
        detail="Authentication required. Provide a valid Bearer token or X-User-ID header.",
        headers={"WWW-Authenticate": "Bearer"}
    )

