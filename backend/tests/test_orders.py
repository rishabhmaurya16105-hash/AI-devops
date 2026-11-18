from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Order, OrderItem, Product

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine, "connect")
def enable_sqlite_foreign_keys(connection: object, record: object) -> None:
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


def override_get_db() -> Generator[Session, None, None]:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=test_engine)


def add_product(
    product_id: int,
    name: str,
    price: Decimal,
    stock: int,
) -> None:
    with TestSessionLocal.begin() as db:
        db.add(
            Product(
                id=product_id,
                slug=f"product-{product_id}",
                name=name,
                description=f"{name} description",
                price=price,
                category="Test",
                stock_quantity=stock,
            )
        )


def product_stock(product_id: int) -> int:
    with TestSessionLocal() as db:
        product = db.get(Product, product_id)
        assert product is not None
        return product.stock_quantity


def test_create_order_persists_item_and_price_snapshot(client: TestClient) -> None:
    add_product(1, "Notebook", Decimal("18.25"), stock=7)

    response = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": 1, "quantity": 2}]},
    )

    assert response.status_code == 201
    order = response.json()
    assert order["order_number"].startswith("ORD-")
    assert order["status"] == "placed"
    assert Decimal(order["total_amount"]) == Decimal("36.50")
    assert len(order["items"]) == 1
    assert Decimal(order["items"][0]["unit_price"]) == Decimal("18.25")
    assert Decimal(order["items"][0]["subtotal"]) == Decimal("36.50")
    assert order["items"][0]["quantity"] == 2
    assert product_stock(1) == 5

    with TestSessionLocal() as db:
        persisted_order = db.scalar(
            select(Order).where(Order.order_number == order["order_number"])
        )
        assert persisted_order is not None
        persisted_items = db.scalars(
            select(OrderItem).where(OrderItem.order_id == persisted_order.id)
        ).all()
        assert len(persisted_items) == 1
        assert persisted_items[0].unit_price == Decimal("18.25")


def test_create_order_ignores_client_supplied_prices_and_totals(
    client: TestClient,
) -> None:
    add_product(1, "Notebook", Decimal("18.25"), stock=7)

    response = client.post(
        "/api/v1/orders",
        json={
            "items": [
                {
                    "product_id": 1,
                    "quantity": 2,
                    "unit_price": "0.01",
                    "subtotal": "0.02",
                }
            ],
            "total_amount": "0.02",
        },
    )

    assert response.status_code == 201
    order = response.json()
    assert Decimal(order["total_amount"]) == Decimal("36.50")
    assert Decimal(order["items"][0]["unit_price"]) == Decimal("18.25")
    assert Decimal(order["items"][0]["subtotal"]) == Decimal("36.50")
    assert product_stock(1) == 5


def test_create_order_with_multiple_products_and_duplicate_ids(
    client: TestClient,
) -> None:
    add_product(1, "Notebook", Decimal("18.25"), stock=7)
    add_product(2, "Bottle", Decimal("32.00"), stock=4)

    response = client.post(
        "/api/v1/orders",
        json={
            "items": [
                {"product_id": 1, "quantity": 1},
                {"product_id": 2, "quantity": 1},
                {"product_id": 1, "quantity": 1},
            ]
        },
    )

    assert response.status_code == 201
    order = response.json()
    assert Decimal(order["total_amount"]) == Decimal("68.50")
    assert len(order["items"]) == 2
    assert product_stock(1) == 5
    assert product_stock(2) == 3


def test_create_order_rejects_nonexistent_product(client: TestClient) -> None:
    response = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": 404, "quantity": 1}]},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product 404 was not found."
    with TestSessionLocal() as db:
        assert db.scalar(select(Order)) is None


@pytest.mark.parametrize("quantity", [0, -1])
def test_create_order_rejects_nonpositive_quantity(
    client: TestClient,
    quantity: int,
) -> None:
    response = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": 1, "quantity": quantity}]},
    )

    assert response.status_code == 422


def test_create_order_rejects_empty_items(client: TestClient) -> None:
    response = client.post("/api/v1/orders", json={"items": []})

    assert response.status_code == 422


def test_insufficient_stock_rolls_back_order_and_all_inventory_changes(
    client: TestClient,
) -> None:
    add_product(1, "Notebook", Decimal("18.25"), stock=7)
    add_product(2, "Bottle", Decimal("32.00"), stock=1)

    response = client.post(
        "/api/v1/orders",
        json={
            "items": [
                {"product_id": 1, "quantity": 2},
                {"product_id": 2, "quantity": 2},
            ]
        },
    )

    assert response.status_code == 409
    assert "only 1 item(s) available" in response.json()["detail"]
    assert product_stock(1) == 7
    assert product_stock(2) == 1
    with TestSessionLocal() as db:
        assert db.scalar(select(Order)) is None
        assert db.scalar(select(OrderItem)) is None


def test_database_failure_rolls_back_order_and_inventory(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    add_product(1, "Notebook", Decimal("18.25"), stock=7)

    def fail_order_reload(db: Session, order_id: int) -> Order:
        raise OperationalError(
            "SELECT orders",
            {},
            RuntimeError("internal database details"),
        )

    monkeypatch.setattr("app.services.order.load_order", fail_order_reload)
    response = client.post(
        "/api/v1/orders",
        json={"items": [{"product_id": 1, "quantity": 2}]},
    )

    assert response.status_code == 503
    assert "internal database details" not in response.text
    assert product_stock(1) == 7
    with TestSessionLocal() as db:
        assert db.scalar(select(Order)) is None
        assert db.scalar(select(OrderItem)) is None


def test_post_order_cors_allows_json_only_for_local_frontend(
    client: TestClient,
) -> None:
    response = client.options(
        "/api/v1/orders",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://127.0.0.1:5173"
    )
    assert "POST" in response.headers["access-control-allow-methods"]
