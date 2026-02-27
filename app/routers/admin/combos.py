import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.product import Combo, ComboItem
from app.models.user import User
from app.schemas.product import ComboCreate, ComboOut, ComboUpdate
from app.services.cloudinary_service import upload_image

router = APIRouter()


@router.get("", response_model=list[ComboOut])
async def admin_list_combos(_: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Combo).order_by(Combo.name))
    return result.scalars().all()


@router.post("", response_model=ComboOut, status_code=201)
async def create_combo(body: ComboCreate, _: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    combo = Combo(
        name=body.name, description=body.description,
        price=body.price, is_published=body.is_published,
    )
    db.add(combo)
    await db.flush()

    for item in body.items:
        db.add(ComboItem(
            combo_id=combo.id, item_type=item.item_type,
            item_id=item.item_id, quantity=item.quantity,
        ))

    await db.commit()
    await db.refresh(combo)
    return combo


@router.patch("/{combo_id}", response_model=ComboOut)
async def update_combo(
    combo_id: uuid.UUID, body: ComboUpdate,
    _: User = Depends(require_admin), db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Combo).where(Combo.id == combo_id))
    combo = result.scalar_one_or_none()
    if not combo:
        raise HTTPException(status_code=404, detail="Combo not found")
    payload = body.model_dump(exclude_unset=True)
    items_payload = payload.pop("items", None)

    for field, value in payload.items():
        setattr(combo, field, value)

    if items_payload is not None:
        await db.execute(
            ComboItem.__table__.delete().where(ComboItem.combo_id == combo_id)
        )
        for item in items_payload:
            db.add(ComboItem(
                combo_id=combo.id,
                item_type=item["item_type"],
                item_id=item["item_id"],
                quantity=item["quantity"],
            ))
    await db.commit()
    await db.refresh(combo)
    return combo


@router.post("/{combo_id}/banner", response_model=ComboOut)
async def upload_combo_banner(
    combo_id: uuid.UUID,
    file: UploadFile = File(...),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Combo).where(Combo.id == combo_id))
    combo = result.scalar_one_or_none()
    if not combo:
        raise HTTPException(status_code=404, detail="Combo not found")
    url = await upload_image(file, folder="udayatech/combos")
    combo.banner_image = url
    await db.commit()
    await db.refresh(combo)
    return combo
