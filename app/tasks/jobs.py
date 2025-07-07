import time
import random
import logging
from typing import List, Dict, Any

import dramatiq
import httpx
from sqlalchemy.orm import Session
from dramatiq import pipeline


from ..schemas import UserCreate, ExternalUser
from ..crud import bulk_create_users, update_job_status
from ..settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dramatiq.actor(store_results=True, max_retries=3)
def fetch_users_from_api() -> List[Dict[str, Any]]:
    """Step 1: Fetch users from external API"""
    logger.info("Starting to fetch users from external API")
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(settings.jsonplaceholder_url)
            response.raise_for_status()
            users_data = response.json()
        logger.info(f"Successfully fetched {len(users_data)} users")
        return users_data
    except httpx.RequestError as e:
        logger.error(f"Error fetching users from API: {e}")
        raise


@dramatiq.actor(store_results=True, max_retries=3)
def transform_users_data(users_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Step 2: Transform external API data to internal schema"""
    logger.info(f"Starting to transform {len(users_data)} users")
    transformed_users = []
    for user_data in users_data:
        external_user = ExternalUser(**user_data)
        user_create = UserCreate(
            name=external_user.name,
            username=external_user.username,
            email=external_user.email,
            phone=external_user.phone,
            website=external_user.website,
            address=external_user.address,
            company=external_user.company,
        )
        transformed_users.append(user_create.model_dump())
    logger.info(f"Successfully transformed {len(transformed_users)} users")
    return transformed_users


@dramatiq.actor(store_results=True, max_retries=3)
def simulate_processing_delay() -> str:
    """Step 3: Simulate random processing delay"""
    delay = random.randint(settings.min_delay, settings.max_delay)
    logger.info(f"Simulating processing delay of {delay} seconds")

    time.sleep(delay)

    logger.info(f"Processing delay of {delay} seconds completed")
    return f"Processed with {delay}s delay"


@dramatiq.actor(store_results=True, max_retries=3)
def save_users_to_database(users_data: List[Dict[str, Any]], *, db: Session):
    """Step 4: Save users to database (session injected by middleware)"""
    logger.info(f"Starting to save {len(users_data)} users to database")
    users_to_create = [UserCreate(**data) for data in users_data]
    created_users = bulk_create_users(db, users_to_create)
    result = {
        "users_created": len(created_users),
        "user_ids": [user.id for user in created_users],
    }
    logger.info(f"Successfully saved {len(created_users)} users to database")
    return result


@dramatiq.actor(store_results=True, max_retries=3, time_limit=60_000)
def update_job_status_task(
    job_id: str,
    status: str,
    result: Dict[str, Any] = None,
    error: str = None,
    *,
    db: Session,
):
    """Helper task to update job status (session injected by middleware)"""
    logger.info(f"Updating job status for job {job_id} to {status}")
    update_job_status(db, job_id, status, result, error)
    logger.info(f"Successfully updated job status for job {job_id}")


@dramatiq.actor(store_results=True, max_retries=0)
def finalize_workflow(save_result: Dict[str, Any], *, job_id: str):
    """Final step in the pipeline to mark the job 'completed'."""
    logger.info(f"Workflow for job {job_id} completed successfully.")
    final_result = {
        "workflow_completed": True,
        "database_result": save_result,
    }
    # This task will also get a db session from the middleware automatically.
    update_job_status_task.send(job_id, "completed", result=final_result)


@dramatiq.actor(store_results=True)
def handle_workflow_failure(message_data, job_id: str):
    """Error callback for the pipeline. Updates job status to 'failed'."""
    try:
        # The exception is stored in the message data under the 'exception' key
        exception = message_data.get("exception", {})
        error_msg = f"Workflow failed for job {job_id}: {exception.get('message', 'Unknown error')}"
        logger.error(error_msg)
        update_job_status_task.send(job_id, "failed", error=error_msg)
    except Exception as e:
        logger.error(f"Critical error in failure handler for job {job_id}: {e}")


@dramatiq.actor(max_retries=0)  # Retries should be handled by individual tasks
def process_users_pipeline(job_id: str):
    """Main workflow orchestrator that STARTS the pipeline."""
    logger.info(f"Starting process_users_pipeline for job {job_id}")

    # Set initial job status to running
    update_job_status_task.send(job_id, "running")

    # Define the pipeline
    workflow_pipeline = pipeline(
        [
            # Step 1: Fetch users. The result is piped to the next task.
            fetch_users_from_api.message(),
            # Step 2: Transform users. The result is piped to the next task.
            transform_users_data.message(),
            # Step 3:
            # 
            # 
            # \\ Save to DB. The result is piped to the finalization task.
            # The `simulate_processing_delay` task was removed as it's not part of the data flow.
            # If a delay is truly needed, it can be part of another task.
            save_users_to_database.message(),
            # Step 4: Finalize. We pass the original job_id as an additional argument.
            finalize_workflow.message(job_id=job_id),
        ]
    ).on_failure(handle_workflow_failure.message(job_id=job_id))

    # Run the pipeline
    workflow_pipeline.run()


# Health check task for monitoring
@dramatiq.actor(store_results=True)
def health_check():
    """Simple health check task."""
    return {"status": "healthy", "timestamp": time.time()}
