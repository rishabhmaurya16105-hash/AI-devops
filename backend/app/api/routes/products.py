import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.product import ProductRead
from app.services.product import get_products

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_product_catalog(db: Session = Depends(get_db)) -> list[ProductRead]:
    try:
        return get_products(db)
    except SQLAlchemyError as exc:
        logger.warning("Product listing query failed.")
        raise HTTPException(
            status_code=503,
            detail="Product catalog is temporarily unavailable.",
        ) from exc
