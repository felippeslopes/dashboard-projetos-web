import json
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.config import get_settings

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


class SheetAccessError(Exception):
    pass


@lru_cache
def _sheets_service():
    settings = get_settings()
    info = json.loads(settings.google_sheets_credentials_json)
    credentials = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def validate_sheet_access(sheet_id: str) -> None:
    """Confirma que a service account consegue abrir a planilha.

    Validação de estrutura de abas/colunas é adicionada no passo de
    dashboard_service, quando o layout real da planilha for definido.
    """
    try:
        _sheets_service().spreadsheets().get(spreadsheetId=sheet_id).execute()
    except Exception as exc:
        raise SheetAccessError(
            "Não foi possível acessar a planilha. Verifique se o link está correto e se "
            "a planilha foi compartilhada com o e-mail de serviço do sistema."
        ) from exc
