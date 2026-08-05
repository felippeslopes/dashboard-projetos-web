from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.rate_limit import limiter
from app.core.security import AuthenticatedUser, get_current_user
from app.schemas.user_config import ConfigStatusResponse, ConnectSheetRequest, UserConfigResponse
from app.services import sheet_connection_service
from app.services.sheet_connection_service import InvalidSheetUrlError
from app.services.sheets_provider import SheetAccessError

router = APIRouter(prefix="/config", tags=["config"])


@router.get("", response_model=ConfigStatusResponse)
def get_config(user: AuthenticatedUser = Depends(get_current_user)) -> ConfigStatusResponse:
    return sheet_connection_service.get_status(user.user_id, user.access_token)


@router.post("", response_model=UserConfigResponse)
@limiter.limit("10/minute")
def connect_sheet(
    request: Request,
    payload: ConnectSheetRequest,
    user: AuthenticatedUser = Depends(get_current_user),
) -> UserConfigResponse:
    try:
        return sheet_connection_service.connect_sheet(payload.sheet_url, user.user_id, user.access_token)
    except InvalidSheetUrlError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except SheetAccessError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
