from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from . import models, schemas


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Create a new user"""
    db_user = models.User(
        name=user.name,
        username=user.username,
        email=user.email,
        phone=user.phone,
        website=user.website,
        address=user.address.dict() if user.address else None,
        company=user.company.dict() if user.company else None,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Get all users with pagination"""
    return db.query(models.User).offset(skip).limit(limit).all()


def create_job_status(
    db: Session, job_id: str, status: str = "pending"
) -> models.JobStatus:
    """Create a new job status record"""
    db_job_status = models.JobStatus(
        job_id=job_id,
        status=status,
    )
    db.add(db_job_status)
    db.commit()
    db.refresh(db_job_status)
    return db_job_status


def update_job_status(
    db: Session,
    job_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> Optional[models.JobStatus]:
    """Update job status"""
    db_job_status = (
        db.query(models.JobStatus).filter(models.JobStatus.job_id == job_id).first()
    )
    if db_job_status:
        db_job_status.status = status
        db_job_status.updated_at = datetime.utcnow()

        if result is not None:
            db_job_status.result = result

        if error is not None:
            db_job_status.error = error

        if status in ["completed", "failed"]:
            db_job_status.completed_at = datetime.utcnow()

        db.commit()
        db.refresh(db_job_status)
    return db_job_status


def get_job_status(db: Session, job_id: str) -> Optional[models.JobStatus]:
    """Get job status by job_id"""
    return db.query(models.JobStatus).filter(models.JobStatus.job_id == job_id).first()


def bulk_create_users(
    db: Session, users: List[schemas.UserCreate]
) -> List[models.User]:
    """Create multiple users efficiently"""
    db_users = []
    for user in users:
        db_user = models.User(
            name=user.name,
            username=user.username,
            email=user.email,
            phone=user.phone,
            website=user.website,
            address=user.address.dict() if user.address else None,
            company=user.company.dict() if user.company else None,
        )
        db_users.append(db_user)

    db.add_all(db_users)
    db.commit()

    # Refresh all objects to get their IDs
    for db_user in db_users:
        db.refresh(db_user)

    return db_users
