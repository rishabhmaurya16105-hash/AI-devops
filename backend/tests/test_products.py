from collections.abc import Generator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.seed_products import SAMPLE_PRODUCTS, seed_products
from app.db.session import get_db
from app.main import app
from app.models import Product

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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


def test_product_listing_returns_database_products(client: TestClient) -> None:
    with TestSessionLocal.begin() as db:
        db.add(
            Product(
                slug="sample-notebook",
                name="Sample Notebook",
                description="A test product.",
                price=Decimal("18.25"),
                category="Workspace",
                stock_quantity=7,
                is_sample=True,
            )
        )

    response = client.get("/api/v1/products")

    assert response.status_code == 200
    product = response.json()[0]
    assert product["name"] == "Sample Notebook"
    assert Decimal(product["price"]) == Decimal("18.25")
    assert product["image_url"] is None
    assert product["stock_quantity"] == 7
    assert product["is_sample"] is True
    assert "created_at" in product
    assert "updated_at" in product


def test_product_listing_returns_empty_array_when_no_products(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/products")

    assert response.status_code == 200
    assert response.json() == []


def test_sample_seed_is_idempotent(client: TestClient) -> None:
    with TestSessionLocal.begin() as db:
        assert seed_products(db) == len(SAMPLE_PRODUCTS)
        assert seed_products(db) == 0
        assert len(db.scalars(select(Product)).all()) == len(SAMPLE_PRODUCTS)


def test_product_listing_hides_database_errors(client: TestClient) -> None:
    class FailingSession:
        def scalars(self, statement: object) -> None:
            raise OperationalError(
                "SELECT products",
                {},
                RuntimeError("sensitive connection details"),
            )

    def override_failing_db() -> FailingSession:
        return FailingSession()

    app.dependency_overrides[get_db] = override_failing_db
    response = client.get("/api/v1/products")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Product catalog is temporarily unavailable."
    }
    assert "sensitive connection details" not in response.text


def test_cors_allows_only_the_configured_local_frontend(
    client: TestClient,
) -> None:
    allowed_response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    blocked_response = client.options(
        "/api/v1/products",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed_response.status_code == 200
    assert (
        allowed_response.headers["access-control-allow-origin"]
        == "http://127.0.0.1:5173"
    )
    assert "access-control-allow-origin" not in blocked_response.headers
