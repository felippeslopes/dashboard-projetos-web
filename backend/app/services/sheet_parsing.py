"""Parsing compartilhado entre provedores de planilha (Google Sheets, Excel
Online). Opera sobre `list[list[str]]` generico -- nao sabe nada sobre a API
de nenhum dos dois, so sobre o formato de linhas/colunas esperado."""

import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime

from app.schemas.project import Tarefa

MAX_DATA_ROWS = 2000

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
# DD/MM/AAAA primeiro (convencao BR, mesma do Google Sheets) -- "%m/%d/%Y"
# so entra como fallback pra datas que so fazem sentido no formato dos EUA
# (dia > 12), caso do Excel Online formatando pelo locale dele.
DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y")


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


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.strip().lower()


def map_header(header_row: list[str]) -> dict[str, int]:
    normalized_row = [normalize(cell) for cell in header_row]
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


def parse_date(raw: str) -> date | None:
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
    prazo = parse_date(prazo_raw)
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


def parse_values(values: list[list[str]]) -> SheetParseResult:
    """Recebe a grade bruta (linha 1 = cabecalho) de qualquer provedor e
    devolve as tarefas parseadas, com a mesma tolerancia a erro linha a
    linha (linha em branco ignorada, falta de Tarefa vira aviso, prazo
    invalido vira aviso sem derrubar a linha)."""
    if not values:
        raise SheetStructureError(
            "A planilha está vazia. Adicione o cabeçalho e pelo menos uma tarefa."
        )

    header_row, *data_rows = values
    column_index = map_header(header_row)

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


def column_letter(index: int) -> str:
    """Converte um indice de coluna 0-based em letra (0 -> A, 25 -> Z).

    Suficiente porque a leitura se limita as colunas A:Z.
    """
    return chr(ord("A") + index)
