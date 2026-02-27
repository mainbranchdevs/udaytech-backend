import uuid
from datetime import datetime

from pydantic import BaseModel, Field
from typing import Literal


# --- Categories ---

class CategoryCreate(BaseModel):
    name: str
    parent_id: int | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    parent_id: int | None

    model_config = {"from_attributes": True}


# --- Products ---

class ProductImageOut(BaseModel):
    id: uuid.UUID
    image_url: str
    display_order: int
    is_primary: bool

    model_config = {"from_attributes": True}


class ProductAttributeOut(BaseModel):
    id: uuid.UUID
    attribute_name: str
    attribute_value: str

    model_config = {"from_attributes": True}


class ProductAttributeIn(BaseModel):
    attribute_name: str
    attribute_value: str


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    category_id: int | None = None
    base_price: float
    discount_price: float | None = None
    is_published: bool = False
    attributes: list[ProductAttributeIn] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category_id: int | None = None
    base_price: float | None = None
    discount_price: float | None = None
    is_active: bool | None = None
    is_published: bool | None = None
    attributes: list[ProductAttributeIn] | None = None


class ProductOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    category_id: int | None
    base_price: float
    discount_price: float | None
    is_active: bool
    is_published: bool
    created_at: datetime
    images: list[ProductImageOut] = []
    attributes: list[ProductAttributeOut] = []

    model_config = {"from_attributes": True}


class ProductListOut(BaseModel):
    id: uuid.UUID
    name: str
    base_price: float
    discount_price: float | None
    primary_image: str | None = None
    category_id: int | None

    model_config = {"from_attributes": True}


# --- Services ---

class ServiceCreate(BaseModel):
    name: str
    description: str | None = None
    image_url: str | None = None
    base_price: float
    is_published: bool = False


class ServiceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    image_url: str | None = None
    base_price: float | None = None
    is_active: bool | None = None
    is_published: bool | None = None


class ServiceOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    image_url: str | None
    base_price: float
    is_active: bool
    is_published: bool

    model_config = {"from_attributes": True}


# --- Combos ---

class ComboItemIn(BaseModel):
    item_type: Literal["product", "service"]
    item_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)


class ComboItemOut(BaseModel):
    id: uuid.UUID
    item_type: str
    item_id: uuid.UUID
    quantity: int

    model_config = {"from_attributes": True}


class ComboCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    is_published: bool = False
    items: list[ComboItemIn] = Field(default_factory=list)


class ComboUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    is_active: bool | None = None
    is_published: bool | None = None
    items: list[ComboItemIn] | None = None


class ComboOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    price: float
    banner_image: str | None
    is_active: bool
    is_published: bool
    items: list[ComboItemOut] = []

    model_config = {"from_attributes": True}
