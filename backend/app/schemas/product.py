from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str
    price: Decimal
    image_url: str | None
    category: str
    stock_quantity: int
    is_sample: bool
    created_at: datetime
    updated_at: datetime
