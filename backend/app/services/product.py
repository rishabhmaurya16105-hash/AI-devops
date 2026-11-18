from sqlalchemy.orm import Session

from app.repositories.product import list_products
from app.schemas.product import ProductRead


def get_products(db: Session) -> list[ProductRead]:
    return list_products(db)
