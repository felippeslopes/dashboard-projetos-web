import json
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.core.config import get_settings
from app.schemas.project import Tarefa

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

MAX_DATA_ROWS = 2000
DATA_RANGE = f"A1:Z{MAX_DATA_ROWS + 1}"

CANONICAL_HEADERS = {
    "projeto": "projeto",
    "nome": "tarefa",
    "status": "status",
    "responsavel": "responsavel",
    "prazo": "prazo",
}
DISPLAY_HEADERS = {
    "projeto": "Projeto",
    "nome": "Tarefa",
    "status": "Status",
    "responsavel": "Responsável",
    "prazo": "Prazo",
}
DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")


class SheetAccessError(Exception):
    pass


class SheetStructureError(Exception):
    pass


class SheetConflictError(Exception):
    """O valor na planilha mudou desde que o cliente carregou a tela."""

    pass


@dataclass
class SheetParseResult:
    tarefas: list[Tarefa]
    avisos: list[str] = field(default_factory=list)
    truncada: bool = False


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


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.strip().lower()


def _map_header(header_row: list[str]) -> dict[str, int]:
    normalized_row = [_normalize(cell) for cell in header_row]
    column_index: dict[str, int] = {}

    for field_name, expected_header in CANONICAL_HEADERS.items():
        try:
            column_index[field_name] = normalized_row.index(expected_header)
        except ValueError:
            continue

    missing = [DISPLAY_HEADERS[f] for f in CANONICAL_HEADERS if f not in column_index]
    if missing:
        expected = ", ".join(DISPLAY_HEADERS.values())
        raise SheetStructureError(
            f"A planilha não tem as colunas esperadas. Faltando: {', '.join(missing)}. "
            f"Cabeçalhos esperados na primeira linha: {expected}."
        )

    return column_index


def _parse_date(raw: str) -> date | None:
    raw = raw.strip()
    if not raw:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _cell(row: list[str], index: int) -> str:
    return row[index].strip() if index < len(row) else ""


def _parse_row(
    row: list[str], column_index: dict[str, int], linha: int
) -> tuple[Tarefa | None, str | None]:
    if not any(cell.strip() for cell in row):
        return None, None

    nome = _cell(row, column_index["nome"])
    if not nome:
        return None, f"Linha {linha}: ignorada, faltou 'Tarefa'"

    prazo_raw = _cell(row, column_index["prazo"])
    prazo = _parse_date(prazo_raw)
    aviso = None
    if prazo_raw and prazo is None:
        aviso = f"Linha {linha}: prazo inválido ('{prazo_raw}'), tarefa ficará sem data de entrega"

    tarefa = Tarefa(
        projeto=_cell(row, column_index["projeto"]),
        nome=nome,
        status=_cell(row, column_index["status"]),
        responsavel=_cell(row, column_index["responsavel"]),
        prazo=prazo,
        linha_planilha=linha,
    )
    return tarefa, aviso


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

    values = result.get("values", [])
    if not values:
        raise SheetStructureError(
            "A planilha está vazia. Adicione o cabeçalho e pelo menos uma tarefa."
        )

    header_row, *data_rows = values
    column_index = _map_header(header_row)

    truncada = len(data_rows) >= MAX_DATA_ROWS
    data_rows = data_rows[:MAX_DATA_ROWS]

    tarefas: list[Tarefa] = []
    avisos: list[str] = []
    for offset, row in enumerate(data_rows):
        linha = offset + 2  # +1 pelo header, +1 porque a planilha é 1-based
        tarefa, aviso = _parse_row(row, column_index, linha)
        if tarefa is not None:
            tarefas.append(tarefa)
        if aviso is not None:
            avisos.append(aviso)

    return SheetParseResult(tarefas=tarefas, avisos=avisos, truncada=truncada)


def _column_letter(index: int) -> str:
    """Converte um indice de coluna 0-based em letra (0 -> A, 25 -> Z).

    Suficiente porque DATA_RANGE limita a leitura as colunas A:Z.
    """
    return chr(ord("A") + index)


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
    column_index = _map_header(header_row)
    return _column_letter(column_index["status"])


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
