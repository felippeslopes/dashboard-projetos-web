from dataclasses import dataclass
from datetime import datetime

from supabase import create_client

from app.core.config import get_settings

TABLE_NAME = "user_config"

GOOGLE_SHEETS = "google_sheets"
EXCEL_ONLINE = "excel_online"


@dataclass
class UserConfigRecord:
    sheet_id: str
    connected_at: datetime
    provider: str = GOOGLE_SHEETS
    drive_id: str | None = None


def _client(access_token: str):
    settings = get_settings()
    client = create_client(settings.supabase_url, settings.supabase_anon_key)
    client.postgrest.auth(access_token)
    return client


def get_config(user_id: str, access_token: str) -> UserConfigRecord | None:
    response = (
        _client(access_token)
        .table(TABLE_NAME)
        .select("sheet_id, created_at, provider, drive_id")
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )
    if response is None or response.data is None:
        return None
    return UserConfigRecord(
        sheet_id=response.data["sheet_id"],
        connected_at=response.data["created_at"],
        provider=response.data.get("provider") or GOOGLE_SHEETS,
        drive_id=response.data.get("drive_id"),
    )


def upsert_config(
    user_id: str,
    access_token: str,
    sheet_id: str,
    provider: str = GOOGLE_SHEETS,
    drive_id: str | None = None,
) -> UserConfigRecord:
    response = (
        _client(access_token)
        .table(TABLE_NAME)
        .upsert(
            {
                "user_id": user_id,
                "sheet_id": sheet_id,
                "provider": provider,
                "drive_id": drive_id,
            },
            on_conflict="user_id",
        )
        .execute()
    )
    row = response.data[0]
    return UserConfigRecord(
        sheet_id=row["sheet_id"],
        connected_at=row["created_at"],
        provider=row.get("provider") or GOOGLE_SHEETS,
        drive_id=row.get("drive_id"),
    )
