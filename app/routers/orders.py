import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.product import Product, Service
from app.models.user import User
from app.schemas.order import OrderCreate, OrderOut

router = APIRouter()


async def _resolve_price(db: AsyncSession, item_type: str, item_id: uuid.UUID) -> float:
    if item_type == "product":
        result = await db.execute(select(Product).where(Product.id == item_id))
        entity = result.scalar_one_or_none()
        if not entity:
            raise HTTPException(status_code=400, detail=f"Product {item_id} not found")
        return float(entity.discount_price or entity.base_price)
    elif item_type == "service":
        result = await db.execute(select(Service).where(Service.id == item_id))
        entity = result.scalar_one_or_none()
        if not entity:
            raise HTTPException(status_code=400, detail=f"Service {item_id} not found")
        return float(entity.base_price)
    raise HTTPException(status_code=400, detail=f"Invalid item_type: {item_type}")


@router.post("", response_model=OrderOut, status_code=201)
async def create_order(body: OrderCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not body.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    total = 0.0
    order_items = []
    for item in body.items:
        price = await _resolve_price(db, item.item_type, item.item_id)
        line_total = price * item.quantity
        total += line_total
        order_items.append(OrderItem(
            item_type=item.item_type, item_id=item.item_id,
            quantity=item.quantity, price_snapshot=price,
        ))

    order = Order(
        user_id=user.id, status="pending", total_price=total,
        address_id=body.address_id, notes=body.notes,
    )
    order.items = order_items
    db.add(order)
    await db.flush()

    db.add(OrderStatusHistory(order_id=order.id, status="pending", updated_by=user.id, notes="Order placed"))
    await db.commit()
    await db.refresh(order)
    return order


@router.get("", response_model=list[OrderOut])
async def list_orders(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: uuid.UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == user.id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
