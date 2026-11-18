from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Product


def list_products(db: Session) -> list[Product]:
    statement = select(Product).order_by(Product.id)
    return list(db.scalars(statement).all())
