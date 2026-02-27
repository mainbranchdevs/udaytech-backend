import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.support import SupportMessage, SupportTicket
from app.models.user import User
from app.schemas.support import MessageCreate, MessageOut, TicketCreate, TicketOut, TicketStatusUpdate
from app.services.notification_service import create_notification

router = APIRouter()


@router.post("/tickets", response_model=TicketOut, status_code=201)
async def create_ticket(body: TicketCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    ticket = SupportTicket(user_id=user.id, order_id=body.order_id, status="pending")
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/tickets", response_model=list[TicketOut])
async def list_tickets(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(SupportTicket)
    if user.role != "admin":
        stmt = stmt.where(SupportTicket.user_id == user.id)
    stmt = stmt.order_by(SupportTicket.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.patch("/tickets/{ticket_id}/status", response_model=TicketOut)
async def update_ticket_status(
    ticket_id: uuid.UUID,
    body: TicketStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = body.status
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.post("/messages", response_model=MessageOut, status_code=201)
async def send_message(body: MessageCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SupportTicket).where(SupportTicket.id == body.ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if user.role != "admin" and ticket.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    msg = SupportMessage(
        ticket_id=body.ticket_id, sender_id=user.id,
        message=body.message, message_type=body.message_type,
    )
    db.add(msg)

    notify_user_id = ticket.user_id if user.role == "admin" else None
    if notify_user_id:
        await create_notification(
            db, user_id=notify_user_id,
            title="New support reply",
            message="You have a new reply on your support ticket.",
            type="support",
        )

    await db.commit()
    await db.refresh(msg)
    return msg
