import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.order import OrderCreate, OrderRead
from app.services.order import (
    InsufficientStockError,
    ProductNotFoundError,
    place_order,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    request: OrderCreate,
    db: Session = Depends(get_db),
) -> OrderRead:
    try:
        return place_order(db, request)
    except ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {exc.product_id} was not found.",
        ) from exc
    except InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Product {exc.product_id} has only "
                f"{exc.available} item(s) available."
            ),
        ) from exc
    except SQLAlchemyError as exc:
        logger.warning("Order creation failed due to a database error.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The order could not be completed. Please try again.",
        ) from exc
