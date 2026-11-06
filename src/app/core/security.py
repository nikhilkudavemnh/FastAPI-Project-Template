"""Password hashing (argon2 via pwdlib) and JWT issuing/verification (PyJWT).
Tokens carry: sub (user id), typ (access|refresh), jti, iat, exp, iss (service name)."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings
from app.core.exceptions import UnauthorizedError

type TokenType = Literal["access", "refresh"]

_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _hasher.verify(password, hashed)


def create_token(
    settings: Settings,
    *,
    subject: str,
    token_type: TokenType,
    extra: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    ttl = (
        timedelta(minutes=settings.access_token_expire_minutes)
        if token_type == "access"
        else timedelta(days=settings.refresh_token_expire_days)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "typ": token_type,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + ttl,
        "iss": settings.service_name,
        **(extra or {}),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(settings: Settings, token: str, *, expected_type: TokenType) -> dict[str, Any]:
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "typ"]},
        )
    except jwt.ExpiredSignatureError as e:
        raise UnauthorizedError("Token expired") from e
    except jwt.PyJWTError as e:
        raise UnauthorizedError("Invalid token") from e
    if payload.get("typ") != expected_type:
        raise UnauthorizedError(f"Expected {expected_type} token")
    return payload
