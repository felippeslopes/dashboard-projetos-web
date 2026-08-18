from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.repositories.microsoft_token_repo import MicrosoftTokenRecord
from app.services import ms_auth
from app.services.ms_auth import MicrosoftAuthError


@dataclass
class _FakeSettings:
    microsoft_client_id: str = "client-id"
    microsoft_client_secret: str = "client-secret"


def test_get_valid_graph_token_retorna_token_guardado_quando_nao_esta_perto_de_expirar(
    monkeypatch,
):
    record = MicrosoftTokenRecord(
        access_token="token-atual",
        refresh_token="refresh-atual",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    monkeypatch.setattr(
        "app.services.ms_auth.microsoft_token_repo.get_token", lambda *a, **k: record
    )

    def _falha_se_chamado(*args, **kwargs):
        raise AssertionError("nao deveria chamar a Microsoft se o token ainda e valido")

    monkeypatch.setattr(httpx, "post", _falha_se_chamado)

    resultado = ms_auth.get_valid_graph_token("user-1", "supabase-token")

    assert resultado == "token-atual"


def test_get_valid_graph_token_renova_quando_perto_de_expirar(monkeypatch):
    record = MicrosoftTokenRecord(
        access_token="token-velho",
        refresh_token="refresh-velho",
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=30),
    )
    monkeypatch.setattr(
        "app.services.ms_auth.microsoft_token_repo.get_token", lambda *a, **k: record
    )
    monkeypatch.setattr("app.services.ms_auth.get_settings", lambda: _FakeSettings())

    upsert_calls = []
    monkeypatch.setattr(
        "app.services.ms_auth.microsoft_token_repo.upsert_token",
        lambda *args: upsert_calls.append(args),
    )

    class _FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "access_token": "token-novo",
                "refresh_token": "refresh-novo",
                "expires_in": 3600,
            }

    monkeypatch.setattr(httpx, "post", lambda *a, **k: _FakeResponse())

    resultado = ms_auth.get_valid_graph_token("user-1", "supabase-token")

    assert resultado == "token-novo"
    assert len(upsert_calls) == 1
    assert upsert_calls[0][2] == "token-novo"
    assert upsert_calls[0][3] == "refresh-novo"


def test_get_valid_graph_token_levanta_erro_quando_nao_ha_conta_conectada(monkeypatch):
    monkeypatch.setattr(
        "app.services.ms_auth.microsoft_token_repo.get_token", lambda *a, **k: None
    )

    with pytest.raises(MicrosoftAuthError):
        ms_auth.get_valid_graph_token("user-1", "supabase-token")
