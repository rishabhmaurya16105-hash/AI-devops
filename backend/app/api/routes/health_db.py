import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health/db", tags=["health"])
def database_health_check(db: Session = Depends(get_db)) -> JSONResponse:
    try:
        db.execute(text("SELECT 1")).scalar_one()
    except SQLAlchemyError:
        logger.warning("Database health check failed.")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy"},
        )

    return JSONResponse(content={"status": "healthy"})
