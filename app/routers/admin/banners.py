import uuid
from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin, get_current_user
from app.models.notification import Banner
from app.models.user import User
from app.schemas.notification import BannerCreate, BannerOut, BannerUpdate
from app.services.cloudinary_service import upload_image

router = APIRouter()


# Public endpoint (mounted separately for customers in main.py isn't needed — we put a public route on this router too)
# Admin list shows all banners including inactive
@router.get("", response_model=list[BannerOut])
async def admin_list_banners(_: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Banner).order_by(Banner.priority.desc()))
    return result.scalars().all()


@router.post("", response_model=BannerOut, status_code=201)
async def create_banner(body: BannerCreate, _: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    banner = Banner(**body.model_dump())
    db.add(banner)
    await db.commit()
    await db.refresh(banner)
    return banner


@router.patch("/{banner_id}", response_model=BannerOut)
async def update_banner(
    banner_id: uuid.UUID, body: BannerUpdate,
    _: User = Depends(require_admin), db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Banner).where(Banner.id == banner_id))
    banner = result.scalar_one_or_none()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(banner, field, value)
    await db.commit()
    await db.refresh(banner)
    return banner


@router.post("/upload-image")
async def upload_banner_image(
    file: UploadFile = File(...),
    _: User = Depends(require_admin),
):
    image_url = await upload_image(file, folder="udayatech/banners")
    return {"image_url": image_url}
