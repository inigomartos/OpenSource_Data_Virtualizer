"""Dependency injection: DB sessions, current user, current org."""

from fastapi import Depends, Header, Cookie, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
from typing import Optional

from app.core.database import get_db
from app.core.security import decode_jwt, is_token_blacklisted
from app.core.exceptions import raise_unauthorized, raise_forbidden
from app.models.user import User


async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    access_token_cookie: Optional[str] = Cookie(None, alias="access_token"),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT from Authorization header or cookie, return User."""
    token = None

    # Try Authorization header first
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
    # Fallback to HttpOnly cookie
    elif access_token_cookie:
        token = access_token_cookie

    if not token:
        raise_unauthorized("Missing authentication credentials")

    try:
        payload = decode_jwt(token)
        if payload.get("type") != "access":
            raise_unauthorized("Invalid token type")
        jti = payload.get("jti")
        if jti and await is_token_blacklisted(jti):
            raise_unauthorized("Token has been revoked")
        user_id = payload.get("sub")
        if not user_id:
            raise_unauthorized("Invalid token payload")
    except JWTError:
        raise_unauthorized()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise_unauthorized("User not found or inactive")

    return user


def require_role(*roles: str):
    """Dependency factory: restrict endpoint to specific roles."""
    async def _check(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise_forbidden(f"Required role: {', '.join(roles)}")
        return user
    return _check
