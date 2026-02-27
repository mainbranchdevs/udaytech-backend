from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.user import User
from app.schemas.user import UserOut

router = APIRouter()


@router.get("", response_model=list[UserOut])
async def admin_list_users(
    search: str | None = Query(default=None, min_length=1),
    role: str | None = Query(default=None),
    is_verified: bool | None = Query(default=None),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User)

    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                User.email.ilike(term),
                User.name.ilike(term),
            )
        )
    if role in {"admin", "customer"}:
        stmt = stmt.where(User.role == role)
    if is_verified is not None:
        stmt = stmt.where(User.is_verified == is_verified)

    result = await db.execute(stmt.order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            is_verified=user.is_verified,
            created_at=user.created_at,
            profile_image=user.profile.profile_image if user.profile else None,
        )
        for user in users
    ]
