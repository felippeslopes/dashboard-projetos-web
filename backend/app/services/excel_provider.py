"""Provedor de dados via Excel Online (Microsoft Graph). Mesma forma de API
que `sheets_provider.py`, mas usa o token OAuth delegado do proprio usuario
(via `ms_auth`) em vez de uma service account -- nao existe equivalente
simples de service account para arquivos pessoais do OneDrive."""

import base64

import httpx

from app.services.sheet_parsing import (
    SheetAccessError,
    SheetConflictError,
    SheetParseResult,
    SheetStructureError,
    column_letter,
    map_header,
    parse_values,
)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

ACCESS_ERROR_MESSAGE = (
    "Não foi possível acessar o arquivo do Excel Online. Verifique se o link de "
    "compartilhamento está correto e se você tem acesso a ele com a conta Microsoft logada."
)


def _auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _encode_share_url(url: str) -> str:
    """Formato exigido pelo Microsoft Graph pra resolver um link de
    compartilhamento em um driveItem: base64url sem padding, prefixado
    com "u!". https://learn.microsoft.com/graph/api/shares-get"""
    encoded = base64.urlsafe_b64encode(url.strip().encode("utf-8")).decode("ascii")
    return f"u!{encoded.rstrip('=')}"


def resolve_share_url(url: str, access_token: str) -> tuple[str, str]:
    """Resolve um link de compartilhamento do OneDrive/Excel Online em
    (drive_id, item_id). Chamada unica que ja serve de validacao de acesso."""
    share_id = _encode_share_url(url)
    try:
        response = httpx.get(
            f"{GRAPH_BASE}/shares/{share_id}/driveItem",
            headers=_auth_header(access_token),
            params={"$select": "id,parentReference"},
            timeout=10,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SheetAccessError(ACCESS_ERROR_MESSAGE) from exc

    body = response.json()
    try:
        drive_id = body["parentReference"]["driveId"]
        item_id = body["id"]
    except KeyError as exc:
        raise SheetAccessError(ACCESS_ERROR_MESSAGE) from exc

    return drive_id, item_id


def _first_worksheet_id(drive_id: str, item_id: str, access_token: str) -> str:
    try:
        response = httpx.get(
            f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/workbook/worksheets",
            headers=_auth_header(access_token),
            timeout=10,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SheetAccessError(ACCESS_ERROR_MESSAGE) from exc

    worksheets = response.json().get("value", [])
    if not worksheets:
        raise SheetStructureError("A planilha do Excel não tem nenhuma aba.")
    return worksheets[0]["id"]


def _range_text(
    drive_id: str, item_id: str, worksheet_id: str, address: str, access_token: str
) -> list[list[str]]:
    try:
        response = httpx.get(
            f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/workbook/worksheets/"
            f"{worksheet_id}/range(address='{address}')",
            headers=_auth_header(access_token),
            params={"$select": "text"},
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SheetAccessError(ACCESS_ERROR_MESSAGE) from exc

    return response.json().get("text", [])


def _used_range_text(
    drive_id: str, item_id: str, worksheet_id: str, access_token: str
) -> list[list[str]]:
    try:
        response = httpx.get(
            f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/workbook/worksheets/"
            f"{worksheet_id}/usedRange(valuesOnly=true)",
            headers=_auth_header(access_token),
            params={"$select": "text"},
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SheetAccessError(ACCESS_ERROR_MESSAGE) from exc

    return response.json().get("text", [])


def fetch_tarefas(drive_id: str, item_id: str, access_token: str) -> SheetParseResult:
    """Le, valida e parseia as tarefas da primeira aba da planilha do Excel.

    Usa a propriedade `text` do range (representacao ja formatada como
    exibida na planilha), nunca `values` -- evita ter que lidar com numeros
    de serie de data ou tipos nativos do Excel, mesmo espirito do
    FORMATTED_VALUE usado no Google Sheets."""
    worksheet_id = _first_worksheet_id(drive_id, item_id, access_token)
    values = _used_range_text(drive_id, item_id, worksheet_id, access_token)
    return parse_values(values)


def update_status(
    drive_id: str,
    item_id: str,
    linha_planilha: int,
    novo_status: str,
    status_esperado: str,
    access_token: str,
) -> None:
    """Mesma estrategia de conflito do Google: le o valor atual antes de
    escrever e recusa (SheetConflictError) se divergir do esperado."""
    worksheet_id = _first_worksheet_id(drive_id, item_id, access_token)

    header_row = _range_text(drive_id, item_id, worksheet_id, "1:1", access_token)
    if not header_row:
        raise SheetStructureError("A planilha do Excel está vazia.")
    column_index = map_header(header_row[0])
    cell_address = f"{column_letter(column_index['status'])}{linha_planilha}"

    current_text = _range_text(drive_id, item_id, worksheet_id, cell_address, access_token)
    current_value = current_text[0][0].strip() if current_text and current_text[0] else ""

    if current_value != status_esperado.strip():
        raise SheetConflictError(
            "Esse dado foi alterado por outra pessoa enquanto você editava. "
            "Recarregue a página para ver o valor atual."
        )

    try:
        response = httpx.patch(
            f"{GRAPH_BASE}/drives/{drive_id}/items/{item_id}/workbook/worksheets/"
            f"{worksheet_id}/range(address='{cell_address}')",
            headers=_auth_header(access_token),
            json={"values": [[novo_status]]},
            timeout=10,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise SheetAccessError(
            "Não foi possível salvar a alteração no Excel Online."
        ) from exc
