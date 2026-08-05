import unicodedata
from datetime import date

from app.schemas.project import DashboardCards, StatusBreakdown, Tarefa

CANONICAL_STATUSES = ["Planejado", "Em andamento", "Concluído", "Atrasado", "Cancelado"]
_OVERDUE_EXCLUDED = {"concluido", "cancelado"}


def _normalize_status(status: str) -> str:
    text = unicodedata.normalize("NFKD", status).encode("ascii", "ignore").decode("ascii")
    return text.strip().lower()


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


def build_dashboard(
    tarefas: list[Tarefa], today: date | None = None
) -> tuple[DashboardCards, list[StatusBreakdown]]:
    today = today or date.today()

    total = len(tarefas)
    em_andamento = sum(1 for t in tarefas if _normalize_status(t.status) == "em andamento")
    concluidas = sum(1 for t in tarefas if _normalize_status(t.status) == "concluido")
    atrasadas = sum(
        1
        for t in tarefas
        if t.prazo is not None
        and t.prazo < today
        and _normalize_status(t.status) not in _OVERDUE_EXCLUDED
    )
    taxa_conclusao = round(concluidas / total * 100, 1) if total else 0.0

    cards = DashboardCards(
        total_tarefas=total,
        em_andamento=em_andamento,
        concluidas=concluidas,
        atrasadas=atrasadas,
        taxa_conclusao=taxa_conclusao,
    )

    return cards, _status_breakdown(tarefas)
