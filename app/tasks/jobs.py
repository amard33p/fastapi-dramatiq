import time
import random
import logging
from typing import List, Dict, Any

import dramatiq
import httpx
from sqlalchemy.orm import Session
from fastapi_injectable import injectable

from ..schemas import UserCreate, ExternalUser
from ..crud import bulk_create_users, update_job_status
from ..settings import settings
from ..deps import SessionDep

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# pure I/O actors (no DB) ----------------------------------------------------
# --------------------------------------------------------------------------- #
@dramatiq.actor(store_results=True, max_retries=3)
def fetch_users_from_api() -> List[Dict[str, Any]]:
    with httpx.Client(timeout=30.0) as c:
        r = c.get(settings.jsonplaceholder_url)
        r.raise_for_status()
    return r.json()


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


# --------------------------------------------------------------------------- #
# DB actors ------------------------------------------------------------------
# --------------------------------------------------------------------------- #
@dramatiq.actor(store_results=True, max_retries=3)
@injectable
def save_users_to_database(users_data: List[Dict[str, Any]], db: SessionDep):
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
@injectable
def update_job_status_task(
    job_id: str,
    status: str,
    db: SessionDep,
    result: Dict[str, Any] = None,
    error: str = None,
):
    """Helper task to update job status (session injected by middleware)"""
    logger.info(f"Updating job status for job {job_id} to {status}")
    update_job_status(db, job_id, status, result, error)
    logger.info(f"Successfully updated job status for job {job_id}")


# --------------------------------------------------------------------------- #
# pipeline orchestration -----------------------------------------------------
# --------------------------------------------------------------------------- #
@dramatiq.actor(store_results=True, max_retries=0)
def finalize_workflow(save_result: Dict[str, Any], *, job_id: str):
    """Final step in the pipeline to mark the job 'completed'."""
    logger.info(f"Workflow for job {job_id} completed successfully.")
    final_result = {
        "workflow_completed": True,
        "database_result": save_result,
    }
    update_job_status_task.send(job_id, "completed", result=final_result)


@dramatiq.actor(store_results=True)
def handle_workflow_failure(message_data, exception_data):
    """Runs whenever *any* pipeline step fails."""
    job_id = message_data["options"].get("job_id")
    if not job_id:
        logger.error("No job_id found in failed message: %s", message_data)
        return

    err = f"Workflow failed for job {job_id}: {exception_data['message']}"
    logger.error(err)
    update_job_status_task.send(job_id, "failed", error=err)


@dramatiq.actor(max_retries=0)
def process_users_pipeline(job_id: str):
    logger.info("Starting pipeline for job %s", job_id)

    # mark the job "running"
    update_job_status_task.send(job_id, "running")

    # convenience dict so we don’t repeat ourselves
    cb_opts = dict(
        on_failure=handle_workflow_failure.actor_name,
        job_id=job_id,
    )

    pipe = (
        fetch_users_from_api.message_with_options(**cb_opts)
        | transform_users_data.message_with_options(**cb_opts)
        | save_users_to_database.message_with_options(**cb_opts)
        | finalize_workflow.message(job_id=job_id)
    ).run()


# Health check task for monitoring
@dramatiq.actor(store_results=True)
def health_check():
    """Simple health check task."""
    return {"status": "healthy", "timestamp": time.time()}
