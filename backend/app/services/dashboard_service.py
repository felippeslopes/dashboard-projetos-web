import unicodedata
from dataclasses import dataclass
from datetime import date

from app.schemas.project import (
    DashboardCards,
    GroupBreakdown,
    PeriodoBreakdown,
    StatusBreakdown,
    Tarefa,
)

CANONICAL_STATUSES = ["Planejado", "Em andamento", "Concluído", "Atrasado", "Cancelado"]
_OVERDUE_EXCLUDED = {"concluido", "cancelado"}
_MESES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
]


@dataclass
class DashboardBuildResult:
    cards: DashboardCards
    grafico_status: list[StatusBreakdown]
    grafico_projeto: list[GroupBreakdown]
    grafico_responsavel: list[GroupBreakdown]
    grafico_prazo: list[PeriodoBreakdown]


def _normalize_status(status: str) -> str:
    text = unicodedata.normalize("NFKD", status).encode("ascii", "ignore").decode("ascii")
    return text.strip().lower()


def _is_atrasada(tarefa: Tarefa, today: date) -> bool:
    return (
        tarefa.prazo is not None
        and tarefa.prazo < today
        and _normalize_status(tarefa.status) not in _OVERDUE_EXCLUDED
    )


def _status_breakdown(tarefas: list[Tarefa]) -> list[StatusBreakdown]:
    canonical_by_normalized = {_normalize_status(s): s for s in CANONICAL_STATUSES}
    counts: dict[str, int] = {}

    for tarefa in tarefas:
        normalized = _normalize_status(tarefa.status)
        label = canonical_by_normalized.get(normalized, "Outros")
        counts[label] = counts.get(label, 0) + 1

    ordered_labels = CANONICAL_STATUSES + ["Outros"]
    return [
        StatusBreakdown(status=label, quantidade=counts[label])
        for label in ordered_labels
        if counts.get(label)
    ]


def _group_breakdown(
    tarefas: list[Tarefa], key_fn, today: date
) -> list[GroupBreakdown]:
    grupos: dict[str, list[Tarefa]] = {}
    for tarefa in tarefas:
        chave = key_fn(tarefa).strip() or "Sem informação"
        grupos.setdefault(chave, []).append(tarefa)

    resultado = []
    for chave, itens in grupos.items():
        total = len(itens)
        concluidas = sum(1 for t in itens if _normalize_status(t.status) == "concluido")
        atrasadas = sum(1 for t in itens if _is_atrasada(t, today))
        taxa = round(concluidas / total * 100, 1) if total else 0.0
        resultado.append(
            GroupBreakdown(
                chave=chave,
                total=total,
                concluidas=concluidas,
                atrasadas=atrasadas,
                taxa_conclusao=taxa,
            )
        )

    return sorted(resultado, key=lambda g: g.total, reverse=True)


def _periodo_breakdown(tarefas: list[Tarefa]) -> list[PeriodoBreakdown]:
    contagem: dict[tuple[int, int], int] = {}
    for tarefa in tarefas:
        if tarefa.prazo is None:
            continue
        chave = (tarefa.prazo.year, tarefa.prazo.month)
        contagem[chave] = contagem.get(chave, 0) + 1

    ordenado = sorted(contagem.items())
    return [
        PeriodoBreakdown(periodo=f"{_MESES[mes - 1]}/{ano}", total=total)
        for (ano, mes), total in ordenado
    ]


def build_dashboard(tarefas: list[Tarefa], today: date | None = None) -> DashboardBuildResult:
    today = today or date.today()

    total = len(tarefas)
    em_andamento = sum(1 for t in tarefas if _normalize_status(t.status) == "em andamento")
    concluidas = sum(1 for t in tarefas if _normalize_status(t.status) == "concluido")
    atrasadas = sum(1 for t in tarefas if _is_atrasada(t, today))
    taxa_conclusao = round(concluidas / total * 100, 1) if total else 0.0

    cards = DashboardCards(
        total_tarefas=total,
        em_andamento=em_andamento,
        concluidas=concluidas,
        atrasadas=atrasadas,
        taxa_conclusao=taxa_conclusao,
    )

    return DashboardBuildResult(
        cards=cards,
        grafico_status=_status_breakdown(tarefas),
        grafico_projeto=_group_breakdown(tarefas, lambda t: t.projeto, today),
        grafico_responsavel=_group_breakdown(tarefas, lambda t: t.responsavel, today),
        grafico_prazo=_periodo_breakdown(tarefas),
    )
