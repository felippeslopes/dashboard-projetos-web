import httpx
import pytest

from app.services import excel_provider
from app.services.excel_provider import _encode_share_url
from app.services.sheet_parsing import SheetConflictError

HEADER_ROW = ["Projeto", "Tarefa", "Status", "Responsável", "Prazo"]


class _FakeResponse:
    def __init__(self, json_body, status_code=200):
        self._json = json_body
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("erro", request=None, response=self)

    def json(self):
        return self._json


def test_encode_share_url_tem_prefixo_e_sem_padding():
    encoded = _encode_share_url("https://1drv.ms/x/s!AbCdEf")
    assert encoded.startswith("u!")
    assert "=" not in encoded


def test_fetch_tarefas_usa_texto_formatado(monkeypatch):
    def fake_get(url, headers, params=None, timeout=None):
        if url.endswith("/workbook/worksheets"):
            return _FakeResponse({"value": [{"id": "sheet1"}]})
        if "usedRange" in url:
            return _FakeResponse(
                {
                    "text": [
                        HEADER_ROW,
                        ["Projeto X", "Tarefa 1", "Em andamento", "Ana", "20/08/2026"],
                    ]
                }
            )
        raise AssertionError(f"chamada inesperada: {url}")

    monkeypatch.setattr(httpx, "get", fake_get)

    resultado = excel_provider.fetch_tarefas("drive-1", "item-1", "token")

    assert len(resultado.tarefas) == 1
    assert resultado.tarefas[0].nome == "Tarefa 1"
    assert resultado.tarefas[0].status == "Em andamento"


def test_update_status_recusa_quando_valor_diverge(monkeypatch):
    patch_calls = []

    def fake_get(url, headers, params=None, timeout=None):
        if url.endswith("/workbook/worksheets"):
            return _FakeResponse({"value": [{"id": "sheet1"}]})
        if "range(address='1:1')" in url:
            return _FakeResponse({"text": [HEADER_ROW]})
        if "range(address='C5')" in url:
            return _FakeResponse({"text": [["Cancelado"]]})
        raise AssertionError(f"chamada inesperada: {url}")

    def fake_patch(*args, **kwargs):
        patch_calls.append((args, kwargs))
        return _FakeResponse({})

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(httpx, "patch", fake_patch)

    with pytest.raises(SheetConflictError):
        excel_provider.update_status(
            "drive-1", "item-1", 5, "Concluído", "Em andamento", "token"
        )

    assert patch_calls == []


def test_update_status_escreve_quando_valor_bate(monkeypatch):
    patch_calls = []

    def fake_get(url, headers, params=None, timeout=None):
        if url.endswith("/workbook/worksheets"):
            return _FakeResponse({"value": [{"id": "sheet1"}]})
        if "range(address='1:1')" in url:
            return _FakeResponse({"text": [HEADER_ROW]})
        if "range(address='C5')" in url:
            return _FakeResponse({"text": [["Em andamento"]]})
        raise AssertionError(f"chamada inesperada: {url}")

    def fake_patch(url, headers=None, json=None, timeout=None):
        patch_calls.append((url, json))
        return _FakeResponse({})

    monkeypatch.setattr(httpx, "get", fake_get)
    monkeypatch.setattr(httpx, "patch", fake_patch)

    excel_provider.update_status("drive-1", "item-1", 5, "Concluído", "Em andamento", "token")

    assert len(patch_calls) == 1
    url, body = patch_calls[0]
    assert "range(address='C5')" in url
    assert body == {"values": [["Concluído"]]}
