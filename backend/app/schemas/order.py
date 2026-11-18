from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

PositiveInteger = Annotated[int, Field(strict=True, gt=0)]


class OrderItemCreate(BaseModel):
    product_id: PositiveInteger
    quantity: PositiveInteger


class OrderCreate(BaseModel):
    items: Annotated[list[OrderItemCreate], Field(min_length=1)]


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    subtotal: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    total_amount: Decimal
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]
