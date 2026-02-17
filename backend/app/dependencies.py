"""Dependency injection: DB sessions, current user, current org."""

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError

from app.core.database import get_db
from app.core.security import decode_jwt
from app.core.exceptions import raise_unauthorized, raise_forbidden
from app.models.user import User


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT from Authorization header, return User."""
    if not authorization.startswith("Bearer "):
        raise_unauthorized("Invalid authorization header")

    token = authorization.removeprefix("Bearer ")

    try:
        payload = decode_jwt(token)
        if payload.get("type") != "access":
            raise_unauthorized("Invalid token type")
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
