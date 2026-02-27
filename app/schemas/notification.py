import uuid
from datetime import datetime, date

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: uuid.UUID
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class BannerCreate(BaseModel):
    title: str
    image_url: str
    redirect_type: str | None = None
    redirect_id: str | None = None
    priority: int = 0
    start_date: date | None = None
    end_date: date | None = None


class BannerUpdate(BaseModel):
    title: str | None = None
    image_url: str | None = None
    redirect_type: str | None = None
    redirect_id: str | None = None
    priority: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None


class BannerOut(BaseModel):
    id: uuid.UUID
    title: str
    image_url: str
    redirect_type: str | None
    redirect_id: str | None
    priority: int
    start_date: date | None
    end_date: date | None
    is_active: bool

    model_config = {"from_attributes": True}
