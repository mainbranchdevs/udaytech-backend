import uuid
from datetime import datetime

from pydantic import BaseModel


class OrderItemIn(BaseModel):
    item_type: str  # 'product' | 'service'
    item_id: uuid.UUID
    quantity: int = 1


class OrderCreate(BaseModel):
    address_id: uuid.UUID | None = None
    notes: str | None = None
    items: list[OrderItemIn]


class OrderItemOut(BaseModel):
    id: uuid.UUID
    item_type: str
    item_id: uuid.UUID
    quantity: int
    price_snapshot: float

    model_config = {"from_attributes": True}


class StatusHistoryOut(BaseModel):
    id: uuid.UUID
    status: str
    timestamp: datetime
    notes: str | None

    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    total_price: float
    address_id: uuid.UUID | None
    notes: str | None
    created_at: datetime
    items: list[OrderItemOut] = []
    status_history: list[StatusHistoryOut] = []

    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status: str
    notes: str | None = None
