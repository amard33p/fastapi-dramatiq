from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import uuid
import logging
from contextlib import asynccontextmanager

from .db import get_db, create_tables
from .models import User, JobStatus
from .schemas import UserResponse, JobStatusResponse, ProcessUsersResponse
from .crud import get_users, get_job_status, create_job_status
from .tasks.jobs import process_users_pipeline
from .settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    logger.info("Starting up FastAPI application")
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down FastAPI application")


# Initialize FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="A demo application showcasing FastAPI with Dramatiq for background task processing",
    lifespan=lifespan,
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint"""
    return {
        "message": "FastAPI Dramatiq Demo",
        "version": settings.api_version,
        "status": "running",
    }


@app.get("/health", tags=["Health"])
async def health_check_endpoint():
    """Health check endpoint"""
    try:
        # Test database connection
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()

        # Test dramatiq worker (optional - comment out if workers not running)
        # health_check.send()

        return {"status": "healthy", "database": "connected", "dramatiq": "available"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Service unhealthy"
        )


@app.post("/process_users", response_model=ProcessUsersResponse, tags=["Jobs"])
async def process_users(db: Session = Depends(get_db)):
    """
    Process users workflow endpoint

    This endpoint starts a background workflow that:
    1. Fetches users from external API
    2. Transforms the data
    3. Simulates processing delay
    4. Saves users to database

    Returns a job ID for tracking the workflow progress.
    """
    try:
        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Create job status record
        create_job_status(db, job_id, "pending")

        # Start the workflow asynchronously
        process_users_pipeline.send(job_id)

        logger.info(f"Started process_users workflow with job ID: {job_id}")

        return ProcessUsersResponse(
            job_id=job_id, message="User processing workflow started successfully"
        )

    except Exception as e:
        logger.error(f"Error starting process_users workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start user processing workflow",
        )


@app.get("/jobs/{job_id}/status", response_model=JobStatusResponse, tags=["Jobs"])
async def get_job_status_endpoint(job_id: str, db: Session = Depends(get_db)):
    """
    Get job status by job ID

    Returns the current status of a job including:
    - Status (pending, running, completed, failed)
    - Results (if completed)
    - Error information (if failed)
    - Timestamps
    """
    try:
        job_status = get_job_status(db, job_id)

        if not job_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {job_id} not found",
            )

        return JobStatusResponse.model_validate(job_status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job status for {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status",
        )


@app.get("/jobs", tags=["Jobs"])
async def list_jobs(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    List all jobs with pagination
    """
    try:
        jobs = db.query(JobStatus).offset(skip).limit(limit).all()
        return [JobStatusResponse.model_validate(job) for job in jobs]
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs",
        )


@app.get("/users", response_model=List[UserResponse], tags=["Users"])
async def list_users(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    List all users with pagination
    """
    try:
        users = get_users(db, skip=skip, limit=limit)
        return [UserResponse.model_validate(user) for user in users]
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users",
        )


@app.get("/users/count", tags=["Users"])
async def count_users(db: Session = Depends(get_db)):
    """
    Get total count of users
    """
    try:
        count = db.query(User).count()
        return {"total_users": count}
    except Exception as e:
        logger.error(f"Error counting users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to count users",
        )


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": "Resource not found"})


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
