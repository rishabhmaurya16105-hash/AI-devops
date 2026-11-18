from collections import Counter
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models import Order, OrderItem, Product
from app.repositories.order import load_order, lock_products
from app.schemas.order import OrderCreate, OrderRead


class ProductNotFoundError(Exception):
    def __init__(self, product_id: int) -> None:
        self.product_id = product_id


class InsufficientStockError(Exception):
    def __init__(self, product_id: int, available: int) -> None:
        self.product_id = product_id
        self.available = available


def place_order(db: Session, request: OrderCreate) -> OrderRead:
    quantities: Counter[int] = Counter()
    for item in request.items:
        quantities[item.product_id] += item.quantity

    with db.begin():
        products = lock_products(db, sorted(quantities))
        products_by_id = {product.id: product for product in products}

        for product_id, quantity in quantities.items():
            if product_id not in products_by_id:
                raise ProductNotFoundError(product_id)
            product = products_by_id[product_id]
            if product.stock_quantity < quantity:
                raise InsufficientStockError(
                    product_id,
                    product.stock_quantity,
                )

        order = Order(
            order_number=f"ORD-{uuid4().hex.upper()}",
            total_amount=Decimal("0.00"),
            status="placed",
        )
        total_amount = Decimal("0.00")

        for product_id, quantity in quantities.items():
            product: Product = products_by_id[product_id]
            unit_price = product.price
            subtotal = unit_price * quantity
            total_amount += subtotal
            order.items.append(
                OrderItem(
                    product_id=product.id,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal,
                )
            )
            product.stock_quantity -= quantity

        order.total_amount = total_amount
        db.add(order)
        db.flush()
        response = OrderRead.model_validate(load_order(db, order.id))

    return response
