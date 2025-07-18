from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from .settings import settings

# Create database engine
engine = create_engine(settings.database_url, echo=False)

# Create declarative base
Base = declarative_base()


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)
