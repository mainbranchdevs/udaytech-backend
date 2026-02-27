import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import Address, User, UserProfile
from app.schemas.user import AddressCreate, AddressOut, AddressUpdate, UserOut, UserUpdate

router = APIRouter()


@router.patch("/me", response_model=UserOut)
async def update_profile(body: UserUpdate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if body.name is not None:
        user.name = body.name
    await db.commit()
    await db.refresh(user)
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_verified=user.is_verified,
        created_at=user.created_at,
        profile_image=user.profile.profile_image if user.profile else None,
    )


# --- Addresses ---

@router.get("/addresses", response_model=list[AddressOut])
async def list_addresses(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Address).where(Address.user_id == user.id))
    return result.scalars().all()


@router.post("/addresses", response_model=AddressOut, status_code=201)
async def create_address(body: AddressCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    addr = Address(user_id=user.id, **body.model_dump())
    db.add(addr)
    await db.commit()
    await db.refresh(addr)
    return addr


@router.patch("/addresses/{address_id}", response_model=AddressOut)
async def update_address(
    address_id: uuid.UUID,
    body: AddressUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Address).where(Address.id == address_id, Address.user_id == user.id))
    addr = result.scalar_one_or_none()
    if not addr:
        raise HTTPException(status_code=404, detail="Address not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(addr, field, value)
    await db.commit()
    await db.refresh(addr)
    return addr
