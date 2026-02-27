import uuid
from datetime import datetime

from pydantic import BaseModel

from app.schemas.product import ProductListOut


class WishlistCreate(BaseModel):
    product_id: uuid.UUID


class WishlistItemOut(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    created_at: datetime
    product: ProductListOut

    model_config = {"from_attributes": True}
