from datetime import date

from app.services.sheet_parsing import parse_date


def test_parse_date_aceita_formato_br_dd_mm_aaaa():
    assert parse_date("27/05/2026") == date(2026, 5, 27)


def test_parse_date_aceita_iso():
    assert parse_date("2026-05-27") == date(2026, 5, 27)


def test_parse_date_aceita_formato_americano_quando_dia_maior_que_12():
    # Excel Online as vezes formata pelo locale dele (M/D/AAAA, sem zero a
    # esquerda) mesmo pra planilhas em portugues -- "5/27/2026" so faz
    # sentido como 27 de maio, ja que nao existe mes 27.
    assert parse_date("5/27/2026") == date(2026, 5, 27)


def test_parse_date_prioriza_dd_mm_em_caso_ambiguo():
    # "5/6/2026" e ambiguo (5 de junho vs 6 de maio) -- o formato BR
    # (dd/mm) ganha por ser o publico principal do produto.
    assert parse_date("5/6/2026") == date(2026, 6, 5)


def test_parse_date_vazio_retorna_none():
    assert parse_date("") is None
    assert parse_date("   ") is None


def test_parse_date_invalida_retorna_none():
    assert parse_date("não é uma data") is None
