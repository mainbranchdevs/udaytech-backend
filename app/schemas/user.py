import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    name: str | None
    role: str
    is_verified: bool
    created_at: datetime
    profile_image: str | None = None

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    name: str | None = None


class AddressCreate(BaseModel):
    full_address: str
    city: str
    state: str
    pincode: str
    landmark: str | None = None


class AddressUpdate(BaseModel):
    full_address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    landmark: str | None = None


class AddressOut(BaseModel):
    id: uuid.UUID
    full_address: str
    city: str
    state: str
    pincode: str
    landmark: str | None

    model_config = {"from_attributes": True}
