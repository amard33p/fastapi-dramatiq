import time
import random
import logging
from typing import List, Dict, Any

import dramatiq
import httpx
from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..schemas import UserCreate, ExternalUser
from ..crud import bulk_create_users, update_job_status
from ..settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dramatiq.actor(store_results=True, max_retries=3)
def fetch_users_from_api() -> List[Dict[str, Any]]:
    """
    Step 1: Fetch users from external API
    """
    logger.info("Starting to fetch users from external API")

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(settings.jsonplaceholder_url)
            response.raise_for_status()
            users_data = response.json()

        logger.info(f"Successfully fetched {len(users_data)} users from external API")
        return users_data

    except httpx.RequestError as e:
        logger.error(f"Error fetching users from API: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching users: {e}")
        raise


@dramatiq.actor(store_results=True, max_retries=3)
def transform_users_data(users_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Step 2: Transform external API data to internal schema
    """
    logger.info(f"Starting to transform {len(users_data)} users")

    try:
        transformed_users = []

        for user_data in users_data:
            # Validate and transform each user
            external_user = ExternalUser(**user_data)

            # Convert to internal schema
            user_create = UserCreate(
                name=external_user.name,
                username=external_user.username,
                email=external_user.email,
                phone=external_user.phone,
                website=external_user.website,
                address=external_user.address,
                company=external_user.company,
            )

            transformed_users.append(user_create.dict())

        logger.info(f"Successfully transformed {len(transformed_users)} users")
        return transformed_users

    except Exception as e:
        logger.error(f"Error transforming users data: {e}")
        raise


@dramatiq.actor(store_results=True, max_retries=3)
def simulate_processing_delay() -> str:
    """
    Step 3: Simulate random processing delay
    """
    delay = random.randint(settings.min_delay, settings.max_delay)
    logger.info(f"Simulating processing delay of {delay} seconds")

    time.sleep(delay)

    logger.info(f"Processing delay of {delay} seconds completed")
    return f"Processed with {delay}s delay"


@dramatiq.actor(store_results=True, max_retries=3)
def save_users_to_database(users_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Step 4: Save users to database
    """
    logger.info(f"Starting to save {len(users_data)} users to database")

    db: Session = SessionLocal()
    try:
        # Convert dict data back to UserCreate objects
        users_to_create = []
        for user_data in users_data:
            user_create = UserCreate(**user_data)
            users_to_create.append(user_create)

        # Bulk create users
        created_users = bulk_create_users(db, users_to_create)

        result = {
            "users_created": len(created_users),
            "user_ids": [user.id for user in created_users],
        }

        logger.info(f"Successfully saved {len(created_users)} users to database")
        return result

    except Exception as e:
        logger.error(f"Error saving users to database: {e}")
        raise
    finally:
        db.close()


@dramatiq.actor(store_results=True, max_retries=3)
def update_job_status_task(
    job_id: str, status: str, result: Dict[str, Any] = None, error: str = None
):
    """
    Helper task to update job status in database
    """
    logger.info(f"Updating job status for job {job_id} to {status}")

    db: Session = SessionLocal()
    try:
        update_job_status(db, job_id, status, result, error)
        logger.info(f"Successfully updated job status for job {job_id}")
    except Exception as e:
        logger.error(f"Error updating job status for job {job_id}: {e}")
        raise
    finally:
        db.close()


@dramatiq.actor(store_results=True, max_retries=1)
def process_users_workflow(job_id: str):
    """
    Main workflow orchestrator that chains all tasks together
    """
    logger.info(f"Starting process_users_workflow for job {job_id}")

    try:
        # Update job status to running
        update_job_status_task.send(job_id, "running")

        # Step 1: Fetch users from external API
        logger.info(f"Job {job_id}: Starting step 1 - Fetching users from API")
        users_data = fetch_users_from_api()

        # Step 2: Transform users data
        logger.info(f"Job {job_id}: Starting step 2 - Transforming users data")
        transformed_users = transform_users_data(users_data)

        # Step 3: Simulate processing delay
        logger.info(f"Job {job_id}: Starting step 3 - Simulating processing delay")
        delay_result = simulate_processing_delay()

        # Step 4: Save users to database
        logger.info(f"Job {job_id}: Starting step 4 - Saving users to database")
        save_result = save_users_to_database(transformed_users)

        # Combine results
        final_result = {
            "workflow_completed": True,
            "steps_completed": 4,
            "users_fetched": len(users_data),
            "users_transformed": len(transformed_users),
            "delay_info": delay_result,
            "database_result": save_result,
        }

        # Update job status to completed
        update_job_status_task.send(job_id, "completed", final_result)

        logger.info(f"Successfully completed process_users_workflow for job {job_id}")
        return final_result

    except Exception as e:
        error_msg = f"Workflow failed for job {job_id}: {str(e)}"
        logger.error(error_msg)

        # Update job status to failed
        update_job_status_task.send(job_id, "failed", None, error_msg)

        raise


# Health check task for monitoring
@dramatiq.actor(store_results=True)
def health_check():
    """Simple health check task"""
    return {"status": "healthy", "timestamp": time.time()}
