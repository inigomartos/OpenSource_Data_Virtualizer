"""Auth endpoints: login, register, refresh."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.core.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.audit_service import AuditService
from app.services.auth_service import AuthService

router = APIRouter()


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


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    result = await service.login(data)
    try:
        await AuditService.log(
            db=db, org_id=result.get("org_id") if isinstance(result, dict) else getattr(result, "org_id", None),
            user_id=result.get("user_id") if isinstance(result, dict) else getattr(result, "user_id", None),
            action="auth.login",
            resource_type="user",
            resource_id=str(result.get("user_id") if isinstance(result, dict) else getattr(result, "user_id", None)),
            ip_address=request.client.host if request.client else None,
        )
    except Exception:
        pass  # Don't block main operation if audit fails
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    service = AuthService(db)
    return await service.refresh(refresh_token)
