import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Combo
from app.schemas.product import ComboOut

router = APIRouter()


@router.get("", response_model=list[ComboOut])
async def list_combos(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Combo).where(Combo.is_active == True, Combo.is_published == True)  # noqa: E712
    )
    return result.scalars().all()


@router.get("/{combo_id}", response_model=ComboOut)
async def get_combo(combo_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Combo).where(Combo.id == combo_id, Combo.is_active == True))  # noqa: E712
    combo = result.scalar_one_or_none()
    if not combo:
        raise HTTPException(status_code=404, detail="Combo not found")
    return combo
