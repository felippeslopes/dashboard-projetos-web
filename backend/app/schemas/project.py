from datetime import date

from pydantic import BaseModel


class Tarefa(BaseModel):
    projeto: str
    nome: str
    status: str
    responsavel: str
    prazo: date | None
    linha_planilha: int


class DashboardCards(BaseModel):
    total_tarefas: int
    em_andamento: int
    concluidas: int
    atrasadas: int
    taxa_conclusao: float


class StatusBreakdown(BaseModel):
    status: str
    quantidade: int


class DashboardResponse(BaseModel):
    cards: DashboardCards
    tarefas: list[Tarefa]
    grafico_status: list[StatusBreakdown]
    avisos: list[str] = []
    planilha_truncada: bool = False


class UpdateStatusRequest(BaseModel):
    status: str
    status_esperado: str
