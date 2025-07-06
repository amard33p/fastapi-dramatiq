"""
Pytest fixtures for FastAPI-Dramatiq tests.

This module provides fixtures for testing with transactional database sessions,
ensuring that database changes made during tests are rolled back and not persisted.
"""

from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.api import app
from app.db import get_db
from app.settings import settings


@pytest.fixture(scope="session")
def db_engine() -> Generator[Engine, None, None]:
    """Create a SQLAlchemy engine for the test database session."""
    db_uri = str(settings.database_url)
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


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Provides a TestClient configured to use the same transacted DB session
    as the test function (provided by the 'db' fixture).

    This ensures that all database operations performed through the API
    use the same transaction that will be rolled back after the test.
    """

    def get_db_override() -> Generator[Session, None, None]:
        # Yields the existing, transacted session from the `db` fixture
        yield db  # 'db' here is the session instance from the 'db' fixture

    # Override the get_db dependency to use our test session
    app.dependency_overrides[get_db] = get_db_override

    with TestClient(app) as c:
        yield c

    # Clear the specific override after the client is used
    app.dependency_overrides.pop(get_db, None)
