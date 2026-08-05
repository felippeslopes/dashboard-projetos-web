import re

from app.repositories import user_config_repo
from app.schemas.user_config import ConfigStatusResponse, UserConfigResponse
from app.services import sheets_provider

SHEET_URL_PATTERN = re.compile(r"^https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)")


class InvalidSheetUrlError(Exception):
    pass


def extract_sheet_id(sheet_url: str) -> str:
    match = SHEET_URL_PATTERN.match(sheet_url.strip())
    if not match:
        raise InvalidSheetUrlError(
            "Link inválido. Cole o link de compartilhamento de uma planilha do Google Sheets."
        )
    return match.group(1)


def get_current_config(user_id: str, access_token: str) -> UserConfigResponse | None:
    record = user_config_repo.get_config(user_id, access_token)
    if record is None:
        return None
    return UserConfigResponse(sheet_id=record.sheet_id, connected_at=record.connected_at)


def get_status(user_id: str, access_token: str) -> ConfigStatusResponse:
    return ConfigStatusResponse(
        service_account_email=sheets_provider.get_service_account_email(),
        config=get_current_config(user_id, access_token),
    )


def connect_sheet(sheet_url: str, user_id: str, access_token: str) -> UserConfigResponse:
    sheet_id = extract_sheet_id(sheet_url)
    sheets_provider.validate_sheet_access(sheet_id)
    record = user_config_repo.upsert_config(user_id, access_token, sheet_id)
    return UserConfigResponse(sheet_id=record.sheet_id, connected_at=record.connected_at)
