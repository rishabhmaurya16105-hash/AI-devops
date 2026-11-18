from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import get_db
from app.main import app

client = TestClient(app)
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def clear_database_dependency_override() -> Generator[None, None, None]:
    app.dependency_overrides.pop(get_db, None)
    yield
    app.dependency_overrides.pop(get_db, None)


def override_get_db() -> Generator[Session, None, None]:
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_database_health_returns_healthy_when_query_succeeds() -> None:
    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_database_health_hides_database_errors() -> None:
    class FailingSession:
        def execute(self, statement: object) -> None:
            raise OperationalError(
                "SELECT 1",
                {},
                RuntimeError("sensitive connection details"),
            )

    def override_failing_db() -> FailingSession:
        return FailingSession()

    app.dependency_overrides[get_db] = override_failing_db

    response = client.get("/health/db")

    assert response.status_code == 503
    assert response.json() == {"status": "unhealthy"}
    assert "sensitive connection details" not in response.text


def test_existing_health_endpoint_is_unchanged() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
