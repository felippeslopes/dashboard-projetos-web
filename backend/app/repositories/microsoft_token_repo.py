from dataclasses import dataclass
from datetime import datetime

from supabase import create_client

from app.core.config import get_settings

TABLE_NAME = "microsoft_tokens"


@dataclass
class MicrosoftTokenRecord:
    access_token: str
    refresh_token: str
    expires_at: datetime


def _client(access_token: str):
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client


def upsert_token(
    user_id: str,
    access_token: str,
    ms_access_token: str,
    ms_refresh_token: str,
    expires_at: datetime,
) -> None:
    _client(access_token).table(TABLE_NAME).upsert(
        {
            "user_id": user_id,
            "access_token": ms_access_token,
            "refresh_token": ms_refresh_token,
            "expires_at": expires_at.isoformat(),
        },
        on_conflict="user_id",
    ).execute()


def get_token(user_id: str, access_token: str) -> MicrosoftTokenRecord | None:
    response = (
        _client(access_token)
        .table(TABLE_NAME)
        .select("access_token, refresh_token, expires_at")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if response is None or response.data is None:
        return None
    return MicrosoftTokenRecord(
        access_token=response.data["access_token"],
        refresh_token=response.data["refresh_token"],
        expires_at=response.data["expires_at"],
    )
