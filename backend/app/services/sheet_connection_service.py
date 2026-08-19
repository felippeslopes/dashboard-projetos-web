import re

from app.repositories import user_config_repo
from app.repositories.user_config_repo import EXCEL_ONLINE, GOOGLE_SHEETS
from app.schemas.user_config import ConfigStatusResponse, UserConfigResponse
from app.services import excel_provider, ms_auth, sheets_provider

SHEET_URL_PATTERN = re.compile(r"^https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)")
EXCEL_URL_HOSTS = ("1drv.ms", "onedrive.live.com", ".sharepoint.com")


class InvalidSheetUrlError(Exception):
    pass


def extract_sheet_id(sheet_url: str) -> str:
    match = SHEET_URL_PATTERN.match(sheet_url.strip())
    if not match:
        raise InvalidSheetUrlError(
            "Link inválido. Cole o link de compartilhamento de uma planilha do Google Sheets."
        )
    return match.group(1)


def _detect_provider(sheet_url: str) -> str:
    url = sheet_url.strip()
    if SHEET_URL_PATTERN.match(url):
        return GOOGLE_SHEETS
    if any(host in url for host in EXCEL_URL_HOSTS):
        return EXCEL_ONLINE
    raise InvalidSheetUrlError(
        "Link não reconhecido. Cole o link de compartilhamento de uma planilha do "
        "Google Sheets ou de um arquivo do Excel Online (OneDrive/SharePoint)."
    )


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
    provider = _detect_provider(sheet_url)

    if provider == GOOGLE_SHEETS:
        sheet_id = extract_sheet_id(sheet_url)
        sheets_provider.validate_sheet_access(sheet_id)
        record = user_config_repo.upsert_config(user_id, access_token, sheet_id, provider=GOOGLE_SHEETS)
        return UserConfigResponse(sheet_id=record.sheet_id, connected_at=record.connected_at)

    graph_token = ms_auth.get_valid_graph_token(user_id, access_token)
    drive_id, item_id = excel_provider.resolve_share_url(sheet_url, graph_token)
    record = user_config_repo.upsert_config(
        user_id, access_token, item_id, provider=EXCEL_ONLINE, drive_id=drive_id
    )
    return UserConfigResponse(sheet_id=record.sheet_id, connected_at=record.connected_at)
