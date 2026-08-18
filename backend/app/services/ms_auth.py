from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx

from app.core.config import get_settings
from app.repositories import microsoft_token_repo

TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
GRAPH_SCOPES = "openid profile email offline_access Files.ReadWrite User.Read"

# Renova um pouco antes de expirar de verdade, pra nao correr risco de usar
# um token que expira no meio de uma chamada ao Graph.
EXPIRY_SAFETY_MARGIN = timedelta(minutes=2)


class MicrosoftAuthError(Exception):
    pass


@dataclass
class TokenSet:
    access_token: str
    refresh_token: str
    expires_at: datetime


def _exchange_refresh_token(refresh_token: str) -> TokenSet:
    settings = get_settings()
    if not settings.microsoft_client_id or not settings.microsoft_client_secret:
        raise MicrosoftAuthError(
            "Integração com Microsoft não configurada no servidor (faltam credenciais)."
        )

    try:
        response = httpx.post(
            TOKEN_URL,
            data={
                "client_id": settings.microsoft_client_id,
                "client_secret": settings.microsoft_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "scope": GRAPH_SCOPES,
            },
            timeout=10,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise MicrosoftAuthError(
            "Não foi possível renovar o acesso à sua conta Microsoft. Faça login novamente."
        ) from exc

    body = response.json()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=body["expires_in"])
    return TokenSet(
        access_token=body["access_token"],
        # a Microsoft normalmente rotaciona o refresh_token a cada troca
        refresh_token=body.get("refresh_token", refresh_token),
        expires_at=expires_at,
    )


def store_initial_token(
    user_id: str, access_token: str, ms_access_token: str, ms_refresh_token: str, expires_in: int
) -> None:
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    microsoft_token_repo.upsert_token(
        user_id, access_token, ms_access_token, ms_refresh_token, expires_at
    )


def get_valid_graph_token(user_id: str, access_token: str) -> str:
    """Retorna um access_token valido pra chamar o Microsoft Graph,
    renovando via refresh_token se o guardado estiver perto de expirar."""
    record = microsoft_token_repo.get_token(user_id, access_token)
    if record is None:
        raise MicrosoftAuthError(
            "Nenhuma conta Microsoft conectada. Faça login novamente com a Microsoft."
        )

    expires_at = record.expires_at
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))

    if datetime.now(timezone.utc) < expires_at - EXPIRY_SAFETY_MARGIN:
        return record.access_token

    fresh = _exchange_refresh_token(record.refresh_token)
    microsoft_token_repo.upsert_token(
        user_id, access_token, fresh.access_token, fresh.refresh_token, fresh.expires_at
    )
    return fresh.access_token
