from datetime import date

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.notification import Banner
from app.models.product import Category
from app.routers import auth, products, services, combos, orders, support, notifications, users, wishlist
from app.routers.admin import (
    products as admin_products,
    services as admin_services,
    combos as admin_combos,
    orders as admin_orders,
    banners as admin_banners,
    categories as admin_categories,
    users as admin_users,
)
from app.schemas.notification import BannerOut
from app.schemas.product import CategoryOut

app = FastAPI(title="Udaya Tech API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        settings.FRONTEND_URL.rstrip("/"),
        "http://localhost:5173",
        "http://localhost:5174",
        "https://udayatech.in",
        "https://www.udayatech.in",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Public routes ---
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(services.router, prefix="/services", tags=["Services"])
app.include_router(combos.router, prefix="/combos", tags=["Combos"])

# --- Authenticated customer routes ---
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(wishlist.router, prefix="/wishlist", tags=["Wishlist"])
app.include_router(support.router, prefix="/support", tags=["Support"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])
app.include_router(users.router, prefix="/users", tags=["Users"])

# --- Admin routes ---
app.include_router(admin_products.router, prefix="/admin/products", tags=["Admin Products"])
app.include_router(admin_services.router, prefix="/admin/services", tags=["Admin Services"])
app.include_router(admin_combos.router, prefix="/admin/combos", tags=["Admin Combos"])
app.include_router(admin_orders.router, prefix="/admin/orders", tags=["Admin Orders"])
app.include_router(admin_banners.router, prefix="/admin/banners", tags=["Admin Banners"])
app.include_router(admin_categories.router, prefix="/admin/categories", tags=["Admin Categories"])
app.include_router(admin_users.router, prefix="/admin/users", tags=["Admin Users"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/categories", response_model=list[CategoryOut], tags=["Categories"])
async def public_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).order_by(Category.id))
    return result.scalars().all()


@app.get("/banners", response_model=list[BannerOut], tags=["Banners"])
async def public_banners(db: AsyncSession = Depends(get_db)):
    today = date.today()
    stmt = (
        select(Banner)
        .where(
            Banner.is_active == True,  # noqa: E712
            (Banner.start_date == None) | (Banner.start_date <= today),  # noqa: E711
            (Banner.end_date == None) | (Banner.end_date >= today),  # noqa: E711
        )
        .order_by(Banner.priority.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
