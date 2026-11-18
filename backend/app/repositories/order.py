from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Order, Product


def lock_products(db: Session, product_ids: Sequence[int]) -> list[Product]:
    statement = (
        select(Product)
        .where(Product.id.in_(product_ids))
        .order_by(Product.id)
        .with_for_update()
    )
    return list(db.scalars(statement).all())


def load_order(db: Session, order_id: int) -> Order:
    statement = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
    )
    order = db.scalar(statement)
    if order is None:
        raise RuntimeError("The newly created order could not be reloaded.")
    return order
