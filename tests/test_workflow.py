"""Integration test for FastAPI-Dramatiq workflow.

This test mimics the manual steps from the previous ``test_workflow.py`` script but
uses **pytest** assertions instead of ``print`` statements.  It communicates with
an already-running instance of the application (e.g. started via
``docker compose up``).  If the API is not reachable, the test will be skipped
so that unit-test workflows do not fail unexpectedly on CI environments where
the stack is not running.

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

import os
import time
from typing import Any, Dict

import pytest
import requests

DEFAULT_BASE_URL = "http://localhost:8000"


def _get_base_url() -> str:
    """Return base url, honouring ``FASTAPI_DRAMATIQ_BASE_URL`` env var for CI."""
    return os.getenv("FASTAPI_DRAMATIQ_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _wait_for_job_completion(
    base_url: str, job_id: str, timeout: int = 60
) -> Dict[str, Any]:
    """Poll ``/jobs/{job_id}/status`` until the job is done or *timeout* seconds."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"{base_url}/jobs/{job_id}/status", timeout=5)
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


def test_full_workflow() -> None:  # pragma: no cover – integration test
    base_url = _get_base_url()
    print("\n🚀 Testing FastAPI Dramatiq Workflow (pytest)")
    print("=" * 50)

    # 1. Health check
    print("1. Checking application health...")
    health_resp = requests.get(f"{base_url}/health", timeout=5)
    if health_resp.status_code != 200:  # Environment not ready → skip
        print("❌ Application health check failed; skipping test.")
        pytest.skip("FastAPI-Dramatiq stack is not running (health check failed)")
    print("✅ Application is healthy")

    # 2. Initial user count
    print("2. Getting initial user count...")
    initial_count = requests.get(f"{base_url}/users/count", timeout=5).json()[
        "total_users"
    ]
    print(f"📊 Initial user count: {initial_count}")

    # 3. Trigger workflow
    print("3. Triggering user processing workflow...")
    workflow_resp = requests.post(f"{base_url}/process_users", timeout=5)
    assert workflow_resp.status_code == 200, workflow_resp.text
    job_id = workflow_resp.json()["job_id"]
    print(f"🆔 Started job with ID: {job_id}")

    # 4. Wait for completion
    print("4. Waiting for job completion...")
    final_status = _wait_for_job_completion(base_url, job_id)
    print(f"✅ Job status: {final_status['status']}")
    assert final_status["status"] == "completed"
    assert final_status.get("result", {}).get("workflow_completed") is True

    # 5. Final user count increased
    print("5. Getting final user count...")
    final_count = requests.get(f"{base_url}/users/count", timeout=5).json()[
        "total_users"
    ]
    print(f"📈 Final user count: {final_count}")
    assert final_count > initial_count, "No new users were added by the workflow"

    # 6. Quick sanity: fetch recent users (non-assert – network check)
    print("6. Fetching recent users (sanity check)...")
    recent = requests.get(f"{base_url}/users?limit=5", timeout=5)
    print("🎉 Workflow test completed successfully!")
    assert recent.status_code == 200
    assert isinstance(recent.json(), list)
