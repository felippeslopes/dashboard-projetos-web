from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.rate_limit import limiter
from app.core.security import AuthenticatedUser, get_current_user
from app.repositories import snapshot_repo, user_config_repo
from app.repositories.user_config_repo import EXCEL_ONLINE, UserConfigRecord
from app.schemas.project import DashboardResponse, HistoricoPonto, UpdateStatusRequest
from app.services import dashboard_service, excel_provider, ms_auth, sheets_provider
from app.services.ms_auth import MicrosoftAuthError
from app.services.sheet_parsing import SheetAccessError, SheetConflictError, SheetStructureError

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _fetch_tarefas(config: UserConfigRecord, user: AuthenticatedUser):
    if config.provider == EXCEL_ONLINE:
        graph_token = ms_auth.get_valid_graph_token(user.user_id, user.access_token)
        return excel_provider.fetch_tarefas(config.drive_id, config.sheet_id, graph_token)
    return sheets_provider.fetch_tarefas(config.sheet_id)


def _update_status(
    config: UserConfigRecord, user: AuthenticatedUser, linha_planilha: int, novo_status: str, status_esperado: str
) -> None:
    if config.provider == EXCEL_ONLINE:
        graph_token = ms_auth.get_valid_graph_token(user.user_id, user.access_token)
        excel_provider.update_status(
            config.drive_id, config.sheet_id, linha_planilha, novo_status, status_esperado, graph_token
        )
        return
    sheets_provider.update_status(config.sheet_id, linha_planilha, novo_status, status_esperado)


@router.get("", response_model=DashboardResponse)
def get_dashboard(user: AuthenticatedUser = Depends(get_current_user)) -> DashboardResponse:
    config = user_config_repo.get_config(user.user_id, user.access_token)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma planilha conectada. Acesse a tela 'Conectar Planilha' para configurar sua fonte de dados.",
        )

    try:
        parsed = _fetch_tarefas(config, user)
    except (SheetAccessError, SheetStructureError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except MicrosoftAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    resultado = dashboard_service.build_dashboard(parsed.tarefas)

    historico: list[HistoricoPonto] = []
    try:
        snapshot_repo.upsert_snapshot(user.user_id, user.access_token, resultado.cards)
        historico = [
            HistoricoPonto(
                data=registro.snapshot_date,
                total_tarefas=registro.total_tarefas,
                concluidas=registro.concluidas,
                atrasadas=registro.atrasadas,
                taxa_conclusao=registro.taxa_conclusao,
            )
            for registro in snapshot_repo.list_snapshots(user.user_id, user.access_token)
        ]
    except Exception:
        # Historico e um complemento opcional -- se a tabela ainda nao existe
        # no Supabase (ou qualquer outra falha de infraestrutura), o
        # dashboard principal nao deve quebrar por causa disso.
        historico = []

    return DashboardResponse(
        cards=resultado.cards,
        tarefas=parsed.tarefas,
        grafico_status=resultado.grafico_status,
        grafico_projeto=resultado.grafico_projeto,
        grafico_responsavel=resultado.grafico_responsavel,
        grafico_prazo=resultado.grafico_prazo,
        historico=historico,
        avisos=parsed.avisos,
        planilha_truncada=parsed.truncada,
    )


@router.patch("/tarefas/{linha_planilha}/status", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("30/minute")
def update_tarefa_status(
    request: Request,
    linha_planilha: int,
    payload: UpdateStatusRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> None:
    config = user_config_repo.get_config(user.user_id, user.access_token)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma planilha conectada. Acesse a tela 'Conectar Planilha' para configurar sua fonte de dados.",
        )

    try:
        _update_status(config, user, linha_planilha, payload.status, payload.status_esperado)
    except SheetConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (SheetAccessError, SheetStructureError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except MicrosoftAuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
