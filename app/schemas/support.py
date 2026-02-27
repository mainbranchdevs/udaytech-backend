import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SupportTicketStatus = Literal["pending", "not_resolved", "completed"]
SupportTicketOutStatus = Literal["pending", "not_resolved", "completed", "open"]


class TicketCreate(BaseModel):
    order_id: uuid.UUID | None = None


class TicketStatusUpdate(BaseModel):
    status: SupportTicketStatus


class MessageCreate(BaseModel):
    ticket_id: uuid.UUID
    message: str
    message_type: str = "text"


class MessageOut(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    message: str
    message_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TicketOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    order_id: uuid.UUID | None
    status: SupportTicketOutStatus
    created_at: datetime
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}
