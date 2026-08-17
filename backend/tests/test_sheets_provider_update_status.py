import pytest
from unittest.mock import MagicMock

from app.services import sheets_provider
from app.services.sheets_provider import SheetConflictError

HEADER_ROW = ["Projeto", "Tarefa", "Status", "Responsável", "Prazo"]


class _FakeRequest:
    def __init__(self, result):
        self._result = result

    def execute(self):
        return self._result


def _make_fake_service(cell_value: str, update_calls: list):
    service = MagicMock()
    values = service.spreadsheets.return_value.values.return_value

    def get(spreadsheetId, range, valueRenderOption):
        if range == "A1:Z1":
            return _FakeRequest({"values": [HEADER_ROW]})
        return _FakeRequest({"values": [[cell_value]]})

    def update(spreadsheetId, range, valueInputOption, body):
        update_calls.append((range, body))
        return _FakeRequest({})

    values.get.side_effect = get
    values.update.side_effect = update
    return service


def test_update_status_escreve_quando_valor_atual_bate_com_esperado(monkeypatch):
    update_calls: list = []
    fake_service = _make_fake_service(cell_value="Em andamento", update_calls=update_calls)
    monkeypatch.setattr(sheets_provider, "_sheets_service", lambda: fake_service)

    sheets_provider.update_status(
        sheet_id="sheet-1",
        linha_planilha=5,
        novo_status="Concluído",
        status_esperado="Em andamento",
    )

    assert update_calls == [("C5", {"values": [["Concluído"]]})]


def test_update_status_levanta_conflito_quando_valor_atual_diverge(monkeypatch):
    update_calls: list = []
    fake_service = _make_fake_service(cell_value="Cancelado", update_calls=update_calls)
    monkeypatch.setattr(sheets_provider, "_sheets_service", lambda: fake_service)

    with pytest.raises(SheetConflictError):
        sheets_provider.update_status(
            sheet_id="sheet-1",
            linha_planilha=5,
            novo_status="Concluído",
            status_esperado="Em andamento",
        )

    assert update_calls == []
