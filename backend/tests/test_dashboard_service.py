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
    resultado = build_dashboard([], today=TODAY)

    assert resultado.cards.total_tarefas == 0
    assert resultado.cards.em_andamento == 0
    assert resultado.cards.concluidas == 0
    assert resultado.cards.atrasadas == 0
    assert resultado.cards.taxa_conclusao == 0.0
    assert resultado.grafico_status == []
    assert resultado.grafico_projeto == []
    assert resultado.grafico_responsavel == []
    assert resultado.grafico_prazo == []


def test_conta_total_em_andamento_e_concluidas():
    tarefas = [
        make_tarefa(status="Em andamento"),
        make_tarefa(status="Em andamento"),
        make_tarefa(status="Concluído"),
        make_tarefa(status="Planejado"),
    ]

    resultado = build_dashboard(tarefas, today=TODAY)

    assert resultado.cards.total_tarefas == 4
    assert resultado.cards.em_andamento == 2
    assert resultado.cards.concluidas == 1


def test_taxa_conclusao_arredonda_uma_casa_decimal():
    tarefas = [make_tarefa(status="Concluído")] + [make_tarefa(status="Em andamento")] * 2

    resultado = build_dashboard(tarefas, today=TODAY)

    assert resultado.cards.taxa_conclusao == 33.3


def test_atrasada_e_calculada_pelo_prazo_nao_pelo_texto_do_status():
    tarefas = [
        make_tarefa(status="Em andamento", prazo=PAST),
        make_tarefa(status="Atrasado", prazo=FUTURE),
    ]

    resultado = build_dashboard(tarefas, today=TODAY)

    assert resultado.cards.atrasadas == 1


def test_concluida_ou_cancelada_nunca_conta_como_atrasada_mesmo_com_prazo_vencido():
    tarefas = [
        make_tarefa(status="Concluído", prazo=PAST),
        make_tarefa(status="Cancelado", prazo=PAST),
    ]

    resultado = build_dashboard(tarefas, today=TODAY)

    assert resultado.cards.atrasadas == 0


def test_tarefa_sem_prazo_nunca_conta_como_atrasada():
    tarefas = [make_tarefa(status="Em andamento", prazo=None)]

    resultado = build_dashboard(tarefas, today=TODAY)

    assert resultado.cards.atrasadas == 0


def test_grafico_agrupa_por_status_canonico_omitindo_zerados():
    tarefas = [
        make_tarefa(status="Planejado"),
        make_tarefa(status="Em andamento"),
        make_tarefa(status="Em andamento"),
    ]

    resultado = build_dashboard(tarefas, today=TODAY)

    breakdown = {item.status: item.quantidade for item in resultado.grafico_status}
    assert breakdown == {"Planejado": 1, "Em andamento": 2}


def test_grafico_e_case_e_acento_insensivel():
    tarefas = [make_tarefa(status="em ANDAMENTO"), make_tarefa(status="Concluido")]

    resultado = build_dashboard(tarefas, today=TODAY)

    breakdown = {item.status: item.quantidade for item in resultado.grafico_status}
    assert breakdown == {"Em andamento": 1, "Concluído": 1}


def test_status_desconhecido_cai_no_bucket_outros():
    tarefas = [make_tarefa(status="xyz-desconhecido")]

    resultado = build_dashboard(tarefas, today=TODAY)

    breakdown = {item.status: item.quantidade for item in resultado.grafico_status}
    assert breakdown == {"Outros": 1}
    # nao deve contar em nenhum card especifico
    assert resultado.cards.em_andamento == 0
    assert resultado.cards.concluidas == 0


def test_grafico_projeto_agrupa_total_concluidas_atrasadas_e_taxa():
    tarefas = [
        make_tarefa(projeto="Alpha", status="Concluído"),
        make_tarefa(projeto="Alpha", status="Em andamento", prazo=PAST),
        make_tarefa(projeto="Beta", status="Planejado"),
    ]

    resultado = build_dashboard(tarefas, today=TODAY)

    por_projeto = {g.chave: g for g in resultado.grafico_projeto}
    assert por_projeto["Alpha"].total == 2
    assert por_projeto["Alpha"].concluidas == 1
    assert por_projeto["Alpha"].atrasadas == 1
    assert por_projeto["Alpha"].taxa_conclusao == 50.0
    assert por_projeto["Beta"].total == 1


def test_grafico_projeto_ordena_por_total_decrescente():
    tarefas = [
        make_tarefa(projeto="Pequeno"),
        make_tarefa(projeto="Grande"),
        make_tarefa(projeto="Grande"),
        make_tarefa(projeto="Grande"),
    ]

    resultado = build_dashboard(tarefas, today=TODAY)

    assert [g.chave for g in resultado.grafico_projeto] == ["Grande", "Pequeno"]


def test_grafico_responsavel_trata_vazio_como_sem_informacao():
    tarefas = [make_tarefa(responsavel="")]

    resultado = build_dashboard(tarefas, today=TODAY)

    assert resultado.grafico_responsavel[0].chave == "Sem informação"


def test_grafico_prazo_agrupa_por_mes_e_ignora_sem_prazo():
    tarefas = [
        make_tarefa(prazo=date(2025, 6, 1)),
        make_tarefa(prazo=date(2025, 6, 20)),
        make_tarefa(prazo=date(2025, 7, 1)),
        make_tarefa(prazo=None),
    ]

    resultado = build_dashboard(tarefas, today=TODAY)

    assert [(p.periodo, p.total) for p in resultado.grafico_prazo] == [
        ("jun/2025", 2),
        ("jul/2025", 1),
    ]


def test_grafico_prazo_ordena_cronologicamente_entre_anos():
    tarefas = [
        make_tarefa(prazo=date(2026, 1, 5)),
        make_tarefa(prazo=date(2025, 12, 5)),
    ]

    resultado = build_dashboard(tarefas, today=TODAY)

    assert [p.periodo for p in resultado.grafico_prazo] == ["dez/2025", "jan/2026"]
