from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Product

SAMPLE_PRODUCTS = (
    {
        "slug": "daily-notebook",
        "name": "The Daily Notebook",
        "description": "A little space for your big thoughts.",
        "price": Decimal("18.00"),
        "category": "Workspace",
        "stock_quantity": 20,
        "is_sample": True,
    },
    {
        "slug": "good-form-bottle",
        "name": "Good Form Bottle",
        "description": "Your new favorite reason to hydrate.",
        "price": Decimal("32.00"),
        "category": "Everyday",
        "stock_quantity": 15,
        "is_sample": True,
    },
    {
        "slug": "slow-morning-cup",
        "name": "Slow Morning Cup",
        "description": "For that first, uninterrupted sip.",
        "price": Decimal("24.00"),
        "category": "Everyday",
        "stock_quantity": 18,
        "is_sample": True,
    },
    {
        "slug": "little-catchall",
        "name": "The Little Catchall",
        "description": "A happy home for pocket-sized things.",
        "price": Decimal("16.00"),
        "category": "Accessories",
        "stock_quantity": 12,
        "is_sample": True,
    },
    {
        "slug": "focus-friend-timer",
        "name": "Focus Friend Timer",
        "description": "A gentler way to find your focus.",
        "price": Decimal("28.00"),
        "category": "Workspace",
        "stock_quantity": 10,
        "is_sample": True,
    },
    {
        "slug": "weekend-tote",
        "name": "The Weekend Tote",
        "description": "Room for plans, and the lack of them.",
        "price": Decimal("36.00"),
        "category": "Accessories",
        "stock_quantity": 14,
        "is_sample": True,
    },
)


def seed_products(db: Session) -> int:
    slugs = [product["slug"] for product in SAMPLE_PRODUCTS]
    existing_slugs = set(
        db.scalars(select(Product.slug).where(Product.slug.in_(slugs))).all()
    )
    new_products = [
        Product(**product)
        for product in SAMPLE_PRODUCTS
        if product["slug"] not in existing_slugs
    ]
    db.add_all(new_products)
    if new_products:
        db.flush()
    return len(new_products)


def main() -> None:
    with SessionLocal.begin() as db:
        inserted_count = seed_products(db)

    existing_count = len(SAMPLE_PRODUCTS) - inserted_count
    print(
        f"Sample products: {inserted_count} inserted, "
        f"{existing_count} already present."
    )


if __name__ == "__main__":
    main()
