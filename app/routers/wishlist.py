import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.order import Wishlist
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductListOut
from app.schemas.wishlist import WishlistCreate, WishlistItemOut

router = APIRouter()


def _to_product_list_item(product: Product) -> ProductListOut:
    return ProductListOut(
        id=product.id,
        name=product.name,
        base_price=float(product.base_price),
        discount_price=float(product.discount_price) if product.discount_price else None,
        primary_image=None,
        category_id=product.category_id,
    )


@router.get("", response_model=list[WishlistItemOut])
async def list_wishlist(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Wishlist, Product)
        .join(Product, Product.id == Wishlist.product_id)
        .where(Wishlist.user_id == user.id)
        .order_by(Wishlist.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        WishlistItemOut(
            id=wishlist.id,
            product_id=wishlist.product_id,
            created_at=wishlist.created_at,
            product=_to_product_list_item(product),
        )
        for wishlist, product in rows
    ]


@router.post("", response_model=WishlistItemOut, status_code=201)
async def add_wishlist_item(
    body: WishlistCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    product_result = await db.execute(select(Product).where(Product.id == body.product_id))
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_result = await db.execute(
        select(Wishlist).where(Wishlist.user_id == user.id, Wishlist.product_id == body.product_id)
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        return WishlistItemOut(
            id=existing.id,
            product_id=existing.product_id,
            created_at=existing.created_at,
            product=_to_product_list_item(product),
        )

    item = Wishlist(user_id=user.id, product_id=body.product_id)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return WishlistItemOut(
        id=item.id,
        product_id=item.product_id,
        created_at=item.created_at,
        product=_to_product_list_item(product),
    )


@router.delete("/{wishlist_id}", status_code=204)
async def remove_wishlist_item(
    wishlist_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Wishlist).where(Wishlist.id == wishlist_id, Wishlist.user_id == user.id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")

    await db.delete(item)
    await db.commit()
