import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.product import Service
from app.models.user import User
from app.schemas.product import ServiceCreate, ServiceOut, ServiceUpdate
from app.services.cloudinary_service import upload_image

router = APIRouter()


@router.get("", response_model=list[ServiceOut])
async def admin_list_services(_: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).order_by(Service.name))
    return result.scalars().all()


@router.post("", response_model=ServiceOut, status_code=201)
async def create_service(body: ServiceCreate, _: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    svc = Service(**body.model_dump())
    db.add(svc)
    await db.commit()
    await db.refresh(svc)
    return svc


@router.patch("/{service_id}", response_model=ServiceOut)
async def update_service(
    service_id: uuid.UUID, body: ServiceUpdate,
    _: User = Depends(require_admin), db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Service).where(Service.id == service_id))
    svc = result.scalar_one_or_none()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(svc, field, value)
    await db.commit()
    await db.refresh(svc)
    return svc


@router.post("/{service_id}/image", response_model=ServiceOut)
async def upload_service_image(
    service_id: uuid.UUID,
    file: UploadFile = File(...),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Service).where(Service.id == service_id))
    svc = result.scalar_one_or_none()
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    svc.image_url = await upload_image(file, folder="udayatech/services")
    await db.commit()
    await db.refresh(svc)
    return svc
