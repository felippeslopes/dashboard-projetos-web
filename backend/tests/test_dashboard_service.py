from datetime import date

from app.schemas.project import Tarefa
from app.services.dashboard_service import build_dashboard

TODAY = date(2025, 6, 15)
PAST = date(2025, 1, 1)
FUTURE = date(2025, 12, 31)


def make_tarefa(**overrides) -> Tarefa:
    defaults = dict(
        projeto="Projeto X",
        nome="Tarefa",
        status="Em andamento",
        responsavel="Ana",
        prazo=None,
        linha_planilha=2,
    )
    defaults.update(overrides)
    return Tarefa(**defaults)


def test_lista_vazia_zera_todos_os_cards_e_grafico():
    cards, grafico = build_dashboard([], today=TODAY)

    assert cards.total_tarefas == 0
    assert cards.em_andamento == 0
    assert cards.concluidas == 0
    assert cards.atrasadas == 0
    assert cards.taxa_conclusao == 0.0
    assert grafico == []


def test_conta_total_em_andamento_e_concluidas():
    tarefas = [
        make_tarefa(status="Em andamento"),
        make_tarefa(status="Em andamento"),
        make_tarefa(status="Concluído"),
        make_tarefa(status="Planejado"),
    ]

    cards, _ = build_dashboard(tarefas, today=TODAY)

    assert cards.total_tarefas == 4
    assert cards.em_andamento == 2
    assert cards.concluidas == 1


def test_taxa_conclusao_arredonda_uma_casa_decimal():
    tarefas = [make_tarefa(status="Concluído")] + [make_tarefa(status="Em andamento")] * 2

    cards, _ = build_dashboard(tarefas, today=TODAY)

    assert cards.taxa_conclusao == 33.3


def test_atrasada_e_calculada_pelo_prazo_nao_pelo_texto_do_status():
    tarefas = [
        make_tarefa(status="Em andamento", prazo=PAST),
        make_tarefa(status="Atrasado", prazo=FUTURE),
    ]

    cards, _ = build_dashboard(tarefas, today=TODAY)

    assert cards.atrasadas == 1


def test_concluida_ou_cancelada_nunca_conta_como_atrasada_mesmo_com_prazo_vencido():
    tarefas = [
        make_tarefa(status="Concluído", prazo=PAST),
        make_tarefa(status="Cancelado", prazo=PAST),
    ]

    cards, _ = build_dashboard(tarefas, today=TODAY)

    assert cards.atrasadas == 0


def test_tarefa_sem_prazo_nunca_conta_como_atrasada():
    tarefas = [make_tarefa(status="Em andamento", prazo=None)]

    cards, _ = build_dashboard(tarefas, today=TODAY)

    assert cards.atrasadas == 0


def test_grafico_agrupa_por_status_canonico_omitindo_zerados():
    tarefas = [
        make_tarefa(status="Planejado"),
        make_tarefa(status="Em andamento"),
        make_tarefa(status="Em andamento"),
    ]

    _, grafico = build_dashboard(tarefas, today=TODAY)

    breakdown = {item.status: item.quantidade for item in grafico}
    assert breakdown == {"Planejado": 1, "Em andamento": 2}


def test_grafico_e_case_e_acento_insensivel():
    tarefas = [make_tarefa(status="em ANDAMENTO"), make_tarefa(status="Concluido")]

    _, grafico = build_dashboard(tarefas, today=TODAY)

    breakdown = {item.status: item.quantidade for item in grafico}
    assert breakdown == {"Em andamento": 1, "Concluído": 1}


def test_status_desconhecido_cai_no_bucket_outros():
    tarefas = [make_tarefa(status="xyz-desconhecido")]

    cards, grafico = build_dashboard(tarefas, today=TODAY)

    breakdown = {item.status: item.quantidade for item in grafico}
    assert breakdown == {"Outros": 1}
    # nao deve contar em nenhum card especifico
    assert cards.em_andamento == 0
    assert cards.concluidas == 0
