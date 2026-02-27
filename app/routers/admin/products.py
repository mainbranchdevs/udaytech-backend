import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import require_admin
from app.models.product import Product, ProductAttribute, ProductImage
from app.models.user import User
from app.schemas.product import ProductCreate, ProductOut, ProductUpdate
from app.services.cloudinary_service import upload_image

router = APIRouter()


@router.get("", response_model=list[ProductOut])
async def admin_list_products(_: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).order_by(Product.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=ProductOut, status_code=201)
async def create_product(body: ProductCreate, _: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    product = Product(
        name=body.name, description=body.description,
        category_id=body.category_id, base_price=body.base_price,
        discount_price=body.discount_price, is_published=body.is_published,
    )
    db.add(product)
    await db.flush()

    for attr in body.attributes:
        db.add(ProductAttribute(
            product_id=product.id,
            attribute_name=attr.attribute_name,
            attribute_value=attr.attribute_value,
        ))

    await db.commit()
    await db.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: uuid.UUID,
    body: ProductUpdate,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    payload = body.model_dump(exclude_unset=True)
    attributes_payload = payload.pop("attributes", None)

    for field, value in payload.items():
        setattr(product, field, value)

    if attributes_payload is not None:
        await db.execute(
            ProductAttribute.__table__.delete().where(ProductAttribute.product_id == product_id)
        )
        for attr in attributes_payload:
            db.add(ProductAttribute(
                product_id=product.id,
                attribute_name=attr["attribute_name"],
                attribute_value=attr["attribute_value"],
            ))
    await db.commit()
    await db.refresh(product)
    return product


@router.post("/{product_id}/images", response_model=ProductOut)
async def upload_product_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    is_primary: bool = False,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    url = await upload_image(file, folder="udayatech/products")
    order = len(product.images)
    db.add(ProductImage(
        product_id=product_id, image_url=url,
        display_order=order, is_primary=is_primary,
    ))
    await db.commit()
    await db.refresh(product)
    return product
