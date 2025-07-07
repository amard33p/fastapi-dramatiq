from typing import Generator
from contextlib import contextmanager


from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from .settings import settings

# Create database engine
engine = create_engine(settings.database_url, echo=False)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


@contextmanager
def transactional_worker_session() -> Generator[Session]:
    """Session used by background workers; commits or rolls back appropriately."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # noqa: BLE001 – bubble original error
        session.rollback()
        raise
    finally:
        session.close()
