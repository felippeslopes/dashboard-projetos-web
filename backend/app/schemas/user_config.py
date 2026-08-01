from datetime import datetime

from pydantic import BaseModel, Field


class ConnectSheetRequest(BaseModel):
    sheet_url: str = Field(..., min_length=1)


class UserConfigResponse(BaseModel):
    sheet_id: str
    connected_at: datetime
