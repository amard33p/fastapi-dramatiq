from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)

    # Address information (stored as JSON for simplicity)
    address = Column(JSON, nullable=True)

    # Company information (stored as JSON for simplicity)
    company = Column(JSON, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobStatus(Base):
    __tablename__ = "job_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String, unique=True, nullable=False, index=True)
    status = Column(
        String, nullable=False, default="pending"
    )  # pending, running, completed, failed
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
