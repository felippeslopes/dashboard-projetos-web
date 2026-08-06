from dataclasses import dataclass
from datetime import datetime

from supabase import create_client

from app.core.config import get_settings

TABLE_NAME = "user_config"


@dataclass
class UserConfigRecord:
    sheet_id: str
    connected_at: datetime


def _client(access_token: str):
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client


def get_config(user_id: str, access_token: str) -> UserConfigRecord | None:
    response = (
        _client(access_token)
        .table(TABLE_NAME)
        .select("sheet_id, created_at")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if response is None or response.data is None:
        return None
    return UserConfigRecord(
        sheet_id=response.data["sheet_id"],
        connected_at=response.data["created_at"],
    )


def upsert_config(user_id: str, access_token: str, sheet_id: str) -> UserConfigRecord:
    response = (
        _client(access_token)
        .table(TABLE_NAME)
        .upsert({"user_id": user_id, "sheet_id": sheet_id}, on_conflict="user_id")
        .execute()
    )
    row = response.data[0]
    return UserConfigRecord(sheet_id=row["sheet_id"], connected_at=row["created_at"])
