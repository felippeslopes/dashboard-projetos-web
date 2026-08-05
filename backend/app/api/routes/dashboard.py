from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import AuthenticatedUser, get_current_user
from app.repositories import user_config_repo
from app.schemas.project import DashboardResponse
from app.services import dashboard_service, sheets_provider
from app.services.sheets_provider import SheetAccessError, SheetStructureError

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
