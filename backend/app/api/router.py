from fastapi import APIRouter

from app.api.routes import health, health_db, orders, products

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(health_db.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
