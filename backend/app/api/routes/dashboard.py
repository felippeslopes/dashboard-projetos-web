from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.rate_limit import limiter
from app.core.security import AuthenticatedUser, get_current_user
from app.repositories import user_config_repo
from app.schemas.project import DashboardResponse, UpdateStatusRequest
from app.services import dashboard_service, sheets_provider
from app.services.sheets_provider import SheetAccessError, SheetConflictError, SheetStructureError

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard(user: AuthenticatedUser = Depends(get_current_user)) -> DashboardResponse:
    config = user_config_repo.get_config(user.user_id, user.access_token)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma planilha conectada. Acesse a tela 'Conectar Planilha' para configurar sua fonte de dados.",
        )

    try:
        parsed = sheets_provider.fetch_tarefas(config.sheet_id)
    except (SheetAccessError, SheetStructureError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    cards, grafico = dashboard_service.build_dashboard(parsed.tarefas)

    return DashboardResponse(
        cards=cards,
        tarefas=parsed.tarefas,
        grafico_status=grafico,
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
        sheets_provider.update_status(
            config.sheet_id, linha_planilha, payload.status, payload.status_esperado
        )
    except SheetConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except (SheetAccessError, SheetStructureError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
