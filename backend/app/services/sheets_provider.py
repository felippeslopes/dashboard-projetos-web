import json
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.config import get_settings
from app.services.sheet_parsing import (
    SheetAccessError,
    SheetConflictError,
    SheetParseResult,
    SheetStructureError,
    column_letter,
    map_header,
    parse_values,
)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

MAX_DATA_ROWS = 2000
DATA_RANGE = f"A1:Z{MAX_DATA_ROWS + 1}"

__all__ = [
    "SheetAccessError",
    "SheetStructureError",
    "SheetConflictError",
    "SheetParseResult",
    "get_service_account_email",
    "validate_sheet_access",
    "fetch_tarefas",
    "update_status",
]


@lru_cache
def _credentials_info() -> dict:
    settings = get_settings()
    return json.loads(settings.google_sheets_credentials_json)


@lru_cache
def _sheets_service():
    credentials = service_account.Credentials.from_service_account_info(_credentials_info(), scopes=SCOPES)
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def get_service_account_email() -> str:
    return _credentials_info()["client_email"]


def validate_sheet_access(sheet_id: str) -> None:
    """Confirma que a service account consegue abrir a planilha."""
    try:
        _sheets_service().spreadsheets().get(spreadsheetId=sheet_id).execute()
    except Exception as exc:
        raise SheetAccessError(
            "Não foi possível acessar a planilha. Verifique se o link está correto e se "
            "a planilha foi compartilhada com o e-mail de serviço do sistema."
        ) from exc


def fetch_tarefas(sheet_id: str) -> SheetParseResult:
    """Lê, valida e parseia as tarefas da planilha.

    Nunca interpreta o conteúdo da célula como fórmula/código: usa
    valueRenderOption="FORMATTED_VALUE" (o padrão da API), ou seja, sempre
    lemos o valor já calculado pelo Google Sheets, nunca a fórmula bruta.
    """
    try:
        result = (
            _sheets_service()
            .spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range=DATA_RANGE, valueRenderOption="FORMATTED_VALUE")
            .execute()
        )
    except Exception as exc:
        raise SheetAccessError(
            "Não foi possível acessar a planilha. Verifique se o link está correto e se "
            "a planilha foi compartilhada com o e-mail de serviço do sistema."
        ) from exc

    return parse_values(result.get("values", []))


def _status_column_letter(sheet_id: str) -> str:
    try:
        result = (
            _sheets_service()
            .spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range="A1:Z1", valueRenderOption="FORMATTED_VALUE")
            .execute()
        )
    except Exception as exc:
        raise SheetAccessError(
            "Não foi possível acessar a planilha. Verifique se o link está correto e se "
            "a planilha foi compartilhada com o e-mail de serviço do sistema."
        ) from exc

    header_row = result.get("values", [[]])[0] if result.get("values") else []
    column_index = map_header(header_row)
    return column_letter(column_index["status"])


def update_status(
    sheet_id: str, linha_planilha: int, novo_status: str, status_esperado: str
) -> None:
    """Atualiza apenas a celula de status de uma linha, com checagem de conflito.

    Le o valor atual da celula antes de escrever e compara com
    `status_esperado` (o status que o cliente tinha quando iniciou a edicao).
    Se for diferente, alguem alterou esse dado nesse meio tempo -- levanta
    SheetConflictError em vez de sobrescrever (estrategia "last-write-wins
    com aviso", nao silenciosa).
    """
    column = _status_column_letter(sheet_id)
    cell_range = f"{column}{linha_planilha}"

    try:
        current = (
            _sheets_service()
            .spreadsheets()
            .values()
            .get(spreadsheetId=sheet_id, range=cell_range, valueRenderOption="FORMATTED_VALUE")
            .execute()
        )
    except Exception as exc:
        raise SheetAccessError(
            "Não foi possível acessar a planilha. Verifique se o link está correto e se "
            "a planilha foi compartilhada com o e-mail de serviço do sistema."
        ) from exc

    values = current.get("values", [])
    current_value = values[0][0].strip() if values and values[0] else ""

    if current_value != status_esperado.strip():
        raise SheetConflictError(
            "Esse dado foi alterado por outra pessoa enquanto você editava. "
            "Recarregue a página para ver o valor atual."
        )

    try:
        _sheets_service().spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=cell_range,
            valueInputOption="USER_ENTERED",
            body={"values": [[novo_status]]},
        ).execute()
    except Exception as exc:
        raise SheetAccessError(
            "Não foi possível salvar a alteração. Verifique se a planilha foi "
            "compartilhada com permissão de Editor para o e-mail de serviço do sistema."
        ) from exc
