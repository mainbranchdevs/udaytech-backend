"""
Seed sample catalog content into the database.

Usage:
    python seed_catalog.py
    python seed_catalog.py seed_data/catalog_sample.json

The script is idempotent by entity name/title:
- Categories are matched by name
- Products are matched by name
- Services are matched by name
- Combos are matched by name
- Banners are matched by title
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import async_session
from app.models.notification import Banner
from app.models.product import (
    Category,
    Combo,
    ComboItem,
    Product,
    ProductAttribute,
    ProductImage,
    Service,
)


DEFAULT_DATA_FILE = Path("seed_data/catalog_sample.json")


def load_data(data_file: Path) -> dict[str, Any]:
    with data_file.open("r", encoding="utf-8") as f:
        return json.load(f)


async def seed_categories(db, rows: list[dict[str, Any]]) -> dict[str, int]:
    category_map: dict[str, int] = {}
    for row in rows:
        name = row["name"].strip()
        parent_id = row.get("parent_id")
        result = await db.execute(select(Category).where(Category.name == name))
        category = result.scalar_one_or_none()
        if category:
            category.parent_id = parent_id
        else:
            category = Category(name=name, parent_id=parent_id)
            db.add(category)
            await db.flush()
        category_map[name] = category.id
    return category_map


async def seed_products(db, rows: list[dict[str, Any]], category_map: dict[str, int]) -> dict[str, str]:
    product_map: dict[str, str] = {}
    for row in rows:
        name = row["name"].strip()
        result = await db.execute(select(Product).where(Product.name == name))
        product = result.scalar_one_or_none()

        category_name = row.get("category_name")
        category_id = category_map.get(category_name) if category_name else None

        base_fields = {
            "name": name,
            "description": row.get("description"),
            "category_id": category_id,
            "base_price": row["base_price"],
            "discount_price": row.get("discount_price"),
            "is_active": bool(row.get("is_active", True)),
            "is_published": bool(row.get("is_published", True)),
        }

        if product:
            for field, value in base_fields.items():
                setattr(product, field, value)
        else:
            product = Product(**base_fields)
            db.add(product)
            await db.flush()

        # Replace attributes to keep data aligned with the seed file.
        await db.execute(
            ProductAttribute.__table__.delete().where(ProductAttribute.product_id == product.id)
        )
        for attr in row.get("attributes", []):
            db.add(
                ProductAttribute(
                    product_id=product.id,
                    attribute_name=attr["attribute_name"],
                    attribute_value=attr["attribute_value"],
                )
            )

        # Replace images to keep display ordering deterministic.
        await db.execute(
            ProductImage.__table__.delete().where(ProductImage.product_id == product.id)
        )
        for idx, image_url in enumerate(row.get("image_urls", [])):
            db.add(
                ProductImage(
                    product_id=product.id,
                    image_url=image_url,
                    display_order=idx,
                    is_primary=(idx == 0),
                )
            )

        product_map[name] = str(product.id)
    return product_map


async def seed_services(db, rows: list[dict[str, Any]]) -> dict[str, str]:
    service_map: dict[str, str] = {}
    for row in rows:
        name = row["name"].strip()
        result = await db.execute(select(Service).where(Service.name == name))
        service = result.scalar_one_or_none()

        base_fields = {
            "name": name,
            "description": row.get("description"),
            "image_url": row.get("image_url"),
            "base_price": row["base_price"],
            "is_active": bool(row.get("is_active", True)),
            "is_published": bool(row.get("is_published", True)),
        }
        if service:
            for field, value in base_fields.items():
                setattr(service, field, value)
        else:
            service = Service(**base_fields)
            db.add(service)
            await db.flush()

        service_map[name] = str(service.id)
    return service_map


async def seed_combos(db, rows: list[dict[str, Any]], product_map: dict[str, str], service_map: dict[str, str]) -> int:
    seeded_count = 0
    for row in rows:
        name = row["name"].strip()
        result = await db.execute(select(Combo).where(Combo.name == name))
        combo = result.scalar_one_or_none()
        base_fields = {
            "name": name,
            "description": row.get("description"),
            "price": row["price"],
            "banner_image": row.get("banner_image"),
            "is_active": bool(row.get("is_active", True)),
            "is_published": bool(row.get("is_published", True)),
        }
        if combo:
            for field, value in base_fields.items():
                setattr(combo, field, value)
        else:
            combo = Combo(**base_fields)
            db.add(combo)
            await db.flush()

        await db.execute(ComboItem.__table__.delete().where(ComboItem.combo_id == combo.id))

        for item in row.get("items", []):
            item_type = item["item_type"]
            ref_name = item["name"]
            quantity = int(item.get("quantity", 1))

            if item_type == "product":
                item_id = product_map.get(ref_name)
            elif item_type == "service":
                item_id = service_map.get(ref_name)
            else:
                raise ValueError(f"Unsupported combo item_type: {item_type}")

            if not item_id:
                raise ValueError(
                    f"Combo '{name}' references missing {item_type} named '{ref_name}'."
                )

            db.add(
                ComboItem(
                    combo_id=combo.id,
                    item_type=item_type,
                    item_id=item_id,
                    quantity=quantity,
                )
            )

        seeded_count += 1
    return seeded_count


async def seed_banners(db, rows: list[dict[str, Any]]) -> int:
    seeded_count = 0
    for row in rows:
        title = row["title"].strip()
        result = await db.execute(select(Banner).where(Banner.title == title))
        banner = result.scalar_one_or_none()
        base_fields = {
            "title": title,
            "image_url": row["image_url"],
            "redirect_type": row.get("redirect_type"),
            "redirect_id": row.get("redirect_id"),
            "priority": int(row.get("priority", 0)),
            "start_date": row.get("start_date"),
            "end_date": row.get("end_date"),
            "is_active": bool(row.get("is_active", True)),
        }
        if banner:
            for field, value in base_fields.items():
                setattr(banner, field, value)
        else:
            banner = Banner(**base_fields)
            db.add(banner)
        seeded_count += 1
    return seeded_count


async def run(data_file: Path) -> None:
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")

    payload = load_data(data_file)

    async with async_session() as db:
        # Categories first so products can attach category IDs.
        category_map = await seed_categories(db, payload.get("categories", []))
        product_map = await seed_products(db, payload.get("products", []), category_map)
        service_map = await seed_services(db, payload.get("services", []))
        combo_count = await seed_combos(
            db,
            payload.get("combos", []),
            product_map,
            service_map,
        )
        banner_count = await seed_banners(db, payload.get("banners", []))
        await db.commit()

    print("Catalog seed complete.")
    print(f"- Categories: {len(category_map)}")
    print(f"- Products: {len(product_map)}")
    print(f"- Services: {len(service_map)}")
    print(f"- Combos: {combo_count}")
    print(f"- Banners: {banner_count}")
    print(f"- Source: {data_file}")


if __name__ == "__main__":
    input_file = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA_FILE
    asyncio.run(run(input_file))
