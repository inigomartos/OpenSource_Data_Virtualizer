"""Authentication service — single source of truth for JWT issuance."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.core.exceptions import AuthenticationError, DataMindException
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> UserResponse:
        """Register a new organization and admin user."""
        # Check if org slug already exists
        result = await self.db.execute(
            select(Organization).where(Organization.slug == data.org_slug)
        )
        if result.scalar_one_or_none():
            raise DataMindException("Organization slug already taken")

        # Check if email already exists in any org
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if result.scalar_one_or_none():
            raise DataMindException("Email already registered")

        # Create organization
        org = Organization(
            name=data.org_name,
            slug=data.org_slug,
        )
        self.db.add(org)
        await self.db.flush()

        # Create admin user
        user = User(
            org_id=org.id,
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role="admin",
        )
        self.db.add(user)
        await self.db.flush()

        return UserResponse.model_validate(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        """Authenticate user and return JWT tokens."""
        result = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password_hash):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is deactivated")

        token_data = {
            "sub": str(user.id),
            "org_id": str(user.org_id),
            "email": user.email,
            "role": user.role,
        }

        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
            user=UserResponse.model_validate(user),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        from app.core.security import decode_refresh_jwt
        from jose import JWTError

        try:
            payload = decode_refresh_jwt(refresh_token)
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid refresh token")

            user_id = payload.get("sub")
            result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")

            token_data = {
                "sub": str(user.id),
                "org_id": str(user.org_id),
                "email": user.email,
                "role": user.role,
            }

            return TokenResponse(
                access_token=create_access_token(token_data),
                refresh_token=create_refresh_token(token_data),
                user=UserResponse.model_validate(user),
            )
        except JWTError:
            raise AuthenticationError("Invalid refresh token")
