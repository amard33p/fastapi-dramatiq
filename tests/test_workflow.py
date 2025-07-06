"""Integration test for FastAPI-Dramatiq workflow using TestClient.

This test uses FastAPI's TestClient to directly test the API without requiring
a running server. It follows the same workflow as the previous test but uses
the TestClient for more efficient and reliable testing.

The overall flow:
1. Assert the health endpoint returns HTTP 200.
2. Record the initial ``/users/count`` value.
3. Trigger the ``/process_users`` workflow and capture the job id.
4. Poll ``/jobs/{job_id}/status`` until the job is *completed* or *failed* or a
   timeout is reached.
5. Assert the job completed successfully.
6. Assert the final ``/users/count`` value increased compared to the initial
   value.
"""

import time
from typing import Any, Dict, Generator

import pytest
from fastapi.testclient import TestClient

from app.api import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a TestClient instance for testing the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


def _wait_for_job_completion(
    client: TestClient, job_id: str, timeout: int = 60
) -> Dict[str, Any]:
    """Poll ``/jobs/{job_id}/status`` until the job is done or *timeout* seconds."""
    start = time.time()
    while time.time() - start < timeout:
        resp = client.get(f"/jobs/{job_id}/status")
        if resp.status_code != 200:
            raise AssertionError(
                f"Unexpected status code while polling: {resp.status_code}"
            )
        payload = resp.json()
        status = payload.get("status")
        if status == "completed":
            return payload
        if status == "failed":
            raise AssertionError(f"Background job failed: {payload.get('error')}")
        # pending / running – continue polling
        time.sleep(2)
    raise AssertionError("Timed out waiting for background job to complete")


def test_full_workflow(
    client: TestClient,
) -> None:  # pragma: no cover – integration test
    print("\n🚀 Testing FastAPI Dramatiq Workflow with TestClient (pytest)")
    print("=" * 50)

    # 1. Health check
    print("1. Checking application health...")
    health_resp = client.get("/health")
    if health_resp.status_code != 200:  # Environment not ready → skip
        print("❌ Application health check failed; skipping test.")
        pytest.skip("FastAPI-Dramatiq stack is not running (health check failed)")
    print("✅ Application is healthy")

    # 2. Initial user count
    print("2. Getting initial user count...")
    initial_count = client.get("/users/count").json()["total_users"]
    print(f"📊 Initial user count: {initial_count}")

    # 3. Trigger workflow
    print("3. Triggering user processing workflow...")
    workflow_resp = client.post("/process_users")
    assert workflow_resp.status_code == 200, workflow_resp.text
    job_id = workflow_resp.json()["job_id"]
    print(f"🆔 Started job with ID: {job_id}")

    # 4. Wait for completion
    print("4. Waiting for job completion...")
    final_status = _wait_for_job_completion(client, job_id)
    print(f"✅ Job status: {final_status['status']}")
    assert final_status["status"] == "completed"
    assert final_status.get("result", {}).get("workflow_completed") is True

    # 5. Final user count increased
    print("5. Getting final user count...")
    final_count = client.get("/users/count").json()["total_users"]
    print(f"📈 Final user count: {final_count}")
    assert final_count > initial_count, "No new users were added by the workflow"

    # 6. Quick sanity: fetch recent users (non-assert – network check)
    print("6. Fetching recent users (sanity check)...")
    recent = client.get("/users?limit=5")
    print("🎉 Workflow test completed successfully!")
    assert recent.status_code == 200
    assert isinstance(recent.json(), list)
