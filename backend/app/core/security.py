from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Header, HTTPException, status
from jwt import PyJWKClient

from app.core.config import get_settings


@dataclass
class AuthenticatedUser:
    user_id: str
    access_token: str


@lru_cache
def _jwks_client() -> PyJWKClient:
    settings = get_settings()
    jwks_url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
    return PyJWKClient(jwks_url)


def get_current_user(authorization: str | None = Header(default=None)) -> AuthenticatedUser:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação ausente ou mal formatado",
        )

    token = authorization.removeprefix("Bearer ").strip()

    try:
        signing_key = _jwks_client().get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        ) from exc

    return AuthenticatedUser(user_id=payload["sub"], access_token=token)
