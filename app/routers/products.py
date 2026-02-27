import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductListOut, ProductOut

router = APIRouter()


@router.get("", response_model=list[ProductListOut])
async def list_products(
    search: str | None = Query(None),
    category_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Product).where(Product.is_active == True, Product.is_published == True)  # noqa: E712
    if search:
        stmt = stmt.where(Product.name.ilike(f"%{search}%"))
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    stmt = stmt.order_by(Product.created_at.desc())
    result = await db.execute(stmt)
    products = result.scalars().all()
    out = []
    for p in products:
        primary = next((img.image_url for img in p.images if img.is_primary), None)
        if not primary and p.images:
            primary = p.images[0].image_url
        out.append(ProductListOut(
            id=p.id, name=p.name, base_price=float(p.base_price),
            discount_price=float(p.discount_price) if p.discount_price else None,
            primary_image=primary, category_id=p.category_id,
        ))
    return out


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id, Product.is_active == True))  # noqa: E712
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
