"""Security helpers for password hashing and JWT auth."""

from datetime import datetime, timedelta, timezone
import hashlib
from uuid import UUID

import bcrypt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions import UnauthorizedException
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _normalize_password_secret(password: str) -> bytes:
    """Pre-hash password to a fixed-length secret to bypass bcrypt's 72-byte input limit."""
    # SHA-256 digest is deterministic and keeps compatibility with direct bcrypt verification.
    return hashlib.sha256(password.encode("utf-8")).digest()


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Verify a plain-text password against the hash."""
    if not hashed_password:
        return False
    try:
        secret = _normalize_password_secret(plain_password)
        return bcrypt.checkpw(secret, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """Generate a secure hash for a password."""
    secret = _normalize_password_secret(password)
    return bcrypt.hashpw(secret, bcrypt.gensalt()).decode("utf-8")


def create_access_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    """Create JWT access token for a user."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve authenticated user from Bearer token."""
    credentials_exception = UnauthorizedException("Invalid or expired authentication token")

    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise credentials_exception
        user_uuid = UUID(user_id)
    except (JWTError, ValueError):
        raise credentials_exception

    repository = UserRepository(db)
    user = await repository.get_by_id(user_uuid)
    if not user:
        raise credentials_exception
    return user
