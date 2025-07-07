"""
Pytest fixtures for FastAPI-Dramatiq tests.

This module provides fixtures for testing with transactional database sessions,
ensuring that database changes made during tests are rolled back and not persisted.
"""

from typing import Generator

import dramatiq
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.settings import settings

# Switch to test mode **before** importing any project modules that build
# database engines or Dramatiq brokers so they see the correct hostname
# ("localhost" instead of "db").
settings.testing = True

# Import broker module so that stub_broker is registered
import app.tasks.broker


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """Create a SQLAlchemy engine for the test database session."""
    db_uri = settings.database_url
    engine = create_engine(db_uri)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db(db_engine: Engine) -> Generator[Session, None, None]:
    """
    Create a transactional database session for a test.

    This fixture creates a new database connection and transaction for each test.
    After the test completes, the transaction is rolled back, ensuring that
    database changes are not persisted between tests.
    """
    # Standard behavior: transaction per test, rollback at the end
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="session")
def broker() -> Generator[dramatiq.Broker, None, None]:
    """Configure StubBroker via settings and return it."""

    yield dramatiq.get_broker()


@pytest.fixture(scope="function")
def worker(broker: dramatiq.Broker) -> Generator[dramatiq.Worker, None, None]:
    """Start an in-process Dramatiq worker that executes tasks synchronously."""
    worker = dramatiq.Worker(broker, worker_timeout=100)
    worker.start()
    yield worker
    worker.stop()


@pytest.fixture(scope="function")
def client(
    db: Session, broker: dramatiq.Broker, monkeypatch
) -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient + Dramatiq worker that use *exactly the same*
    transactional session as the test itself.
    """
    from app.db import get_db
    from app.api import app
    import app.db as dbmodule

    # -- 1. FastAPI depends on this session -------------------------------
    def get_db_override():
        yield db

    app.dependency_overrides[get_db] = get_db_override

    # -- 2. Dramatiq depends on SessionLocal ------------------------------
    monkeypatch.setattr(dbmodule, "SessionLocal", lambda: db, raising=True)

    # -- 3. Run the test --------------------------------------------------
    with TestClient(app) as c:
        yield c

    # -- 4. Cleanup -------------------------------------------------------
    app.dependency_overrides.pop(get_db, None)
