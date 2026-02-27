import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.order import Order, OrderStatusHistory
from app.models.user import User
from app.schemas.order import OrderOut, OrderStatusUpdate
from app.services.notification_service import create_notification

router = APIRouter()


@router.get("", response_model=list[OrderOut])
async def admin_list_orders(_: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).order_by(Order.created_at.desc()))
    return result.scalars().all()


@router.patch("/{order_id}/status", response_model=OrderOut)
async def update_order_status(
    order_id: uuid.UUID,
    body: OrderStatusUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = body.status
    db.add(OrderStatusHistory(
        order_id=order.id, status=body.status,
        updated_by=admin.id, notes=body.notes,
    ))

    await create_notification(
        db, user_id=order.user_id,
        title="Order status updated",
        message=f"Your order status has been changed to: {body.status}",
        type="order",
    )

    await db.commit()
    await db.refresh(order)
    return order
