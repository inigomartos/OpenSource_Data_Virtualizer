"""Auth endpoints: login, register, refresh, logout."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, Cookie
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.core.database import get_db
from app.core.security import decode_jwt, decode_refresh_jwt, blacklist_token
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter()


def _set_auth_cookies(response: JSONResponse, access_token: str, refresh_token: str) -> None:
    """Set HttpOnly auth cookies on the response."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/v1/auth/refresh",
        domain=settings.COOKIE_DOMAIN,
    )


def _clear_auth_cookies(response: JSONResponse) -> None:
    """Remove auth cookies from the response."""
    response.delete_cookie("access_token", path="/", domain=settings.COOKIE_DOMAIN)
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh", domain=settings.COOKIE_DOMAIN)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    user = await service.register(data)
    try:
        await AuditService.log(
            db=db,
            org_id=getattr(user, "org_id", None),
            user_id=getattr(user, "id", None),
            action="auth.register",
            resource_type="user",
            resource_id=str(getattr(user, "id", None)),
            ip_address=request.client.host if request.client else None,
        )
    except Exception:
        pass
    return user


@router.post("/login")
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.login(data)

    try:
        await AuditService.log(
            db=db,
            org_id=getattr(result, "org_id", None) or (result.user.org_id if hasattr(result, "user") else None),
            user_id=getattr(result, "user_id", None) or (result.user.id if hasattr(result, "user") else None),
            action="auth.login",
            resource_type="user",
            resource_id=str(getattr(result, "user_id", None) or (result.user.id if hasattr(result, "user") else None)),
            ip_address=request.client.host if request.client else None,
        )
    except Exception:
        pass  # Don't block main operation if audit fails

    # Build JSON body — include tokens for backward compatibility + user info
    body = result.model_dump() if hasattr(result, "model_dump") else dict(result)

    response = JSONResponse(content=body)
    _set_auth_cookies(response, result.access_token, result.refresh_token)
    return response


@router.post("/refresh")
async def refresh_token(
    request: Request,
    refresh_token: Optional[str] = None,
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token. Reads refresh token from cookie or request body."""
    token = refresh_token or refresh_token_cookie
    if not token:
        return JSONResponse(status_code=401, content={"detail": "Refresh token required"})

    service = AuthService(db)
    result = await service.refresh(token)

    body = result.model_dump() if hasattr(result, "model_dump") else dict(result)

    response = JSONResponse(content=body)
    _set_auth_cookies(response, result.access_token, result.refresh_token)
    return response


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


@router.post("/logout")
async def logout(
    request: Request,
    body: LogoutRequest = LogoutRequest(),
    authorization: str = Header(default=""),
    user: User = Depends(get_current_user),
):
    """Revoke the current access token (and optionally the refresh token)."""
    # Blacklist the access token
    token = authorization.removeprefix("Bearer ") if authorization.startswith("Bearer ") else None
    if not token:
        token = request.cookies.get("access_token")

    if token:
        try:
            payload = decode_jwt(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti and exp:
                remaining = int(exp - datetime.now(timezone.utc).timestamp())
                if remaining > 0:
                    await blacklist_token(jti, remaining)
        except Exception:
            pass  # Token already validated by get_current_user

    # Blacklist the refresh token (from body or cookie)
    rt = body.refresh_token or request.cookies.get("refresh_token")
    if rt:
        try:
            refresh_payload = decode_refresh_jwt(rt)
            r_jti = refresh_payload.get("jti")
            r_exp = refresh_payload.get("exp")
            if r_jti and r_exp:
                remaining = int(r_exp - datetime.now(timezone.utc).timestamp())
                if remaining > 0:
                    await blacklist_token(r_jti, remaining)
        except Exception:
            pass  # Invalid refresh token — ignore

    response = JSONResponse(content={"message": "Logged out successfully"})
    _clear_auth_cookies(response)
    return response
