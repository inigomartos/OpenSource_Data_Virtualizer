"""Password hashing, JWT encode/decode, AES encryption, token blacklist."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import hashlib

from app.config import settings
from loguru import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_jwt(token: str) -> dict[str, Any]:
    """Decode and validate an access JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])


def decode_refresh_jwt(token: str) -> dict[str, Any]:
    """Decode and validate a refresh JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.JWT_REFRESH_SECRET, algorithms=[settings.JWT_ALGORITHM])


def _get_fernet() -> Fernet:
    """Derive a Fernet key from the ENCRYPTION_KEY setting."""
    key = hashlib.sha256(settings.ENCRYPTION_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_value(plaintext: str) -> str:
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    return _get_fernet().decrypt(ciphertext.encode()).decode()


# ── Token Blacklist (Redis) ─────────────────────────────────────────────────

async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JTI to the Redis blacklist with the given TTL."""
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        await r.setex(f"blacklist:{jti}", ttl_seconds, "1")
        await r.aclose()
    except Exception as e:
        logger.warning(f"Failed to blacklist token {jti}: {e}")


async def is_token_blacklisted(jti: str) -> bool:
    """Check if a JTI has been blacklisted."""
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        result = await r.exists(f"blacklist:{jti}")
        await r.aclose()
        return bool(result)
    except Exception as e:
        # Fail-open: if Redis is down, allow the request but log warning
        logger.warning(f"Redis blacklist check failed for {jti}: {e}")
        return False
