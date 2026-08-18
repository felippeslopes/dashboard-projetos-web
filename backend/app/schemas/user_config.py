from datetime import datetime

from pydantic import BaseModel, Field


class ConnectSheetRequest(BaseModel):
    sheet_url: str = Field(..., min_length=1)


class UserConfigResponse(BaseModel):
    sheet_id: str
    connected_at: datetime


class ConfigStatusResponse(BaseModel):
    service_account_email: str
    config: UserConfigResponse | None


class MicrosoftTokenRequest(BaseModel):
    access_token: str = Field(..., min_length=1)
    refresh_token: str = Field(..., min_length=1)
    expires_in: int = Field(..., gt=0)
