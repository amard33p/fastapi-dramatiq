#!/usr/bin/env python3
"""
Simple test script to verify the FastAPI Dramatiq workflow
"""

import requests
import time
import json


def test_workflow(base_url: str = "http://localhost:8000") -> None:
    """Test the complete workflow"""

    print("🚀 Testing FastAPI Dramatiq Workflow")
    print("=" * 50)

    # 1. Check health
    print("\n1. Checking application health...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Application is healthy")
        else:
            print("❌ Application health check failed")
            return
    except requests.RequestException as e:
        print(f"❌ Failed to connect to application: {e}")
        return

    # 2. Get initial user count
    print("\n2. Getting initial user count...")
    try:
        response = requests.get(f"{base_url}/users/count")
        initial_count = response.json()["total_users"]
        print(f"📊 Initial user count: {initial_count}")
    except Exception as e:
        print(f"❌ Failed to get initial user count: {e}")
        return

    # 3. Start workflow
    print("\n3. Starting user processing workflow...")
    try:
        response = requests.post(f"{base_url}/process_users")
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✅ Workflow started successfully")
            print(f"📋 Job ID: {job_id}")
        else:
            print(f"❌ Failed to start workflow: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Failed to start workflow: {e}")
        return

    # 4. Poll job status
    print("\n4. Monitoring job progress...")
    start_time = time.time()
    max_wait_time = 60  # 1 minute max wait

    while True:
        try:
            response = requests.get(f"{base_url}/jobs/{job_id}/status")
            if response.status_code == 200:
                job_status = response.json()
                status = job_status["status"]

                print(f"📊 Job status: {status}")

                if status == "completed":
                    print("✅ Job completed successfully!")
                    print("\n📋 Job Results:")
                    result = job_status.get("result", {})
                    print(json.dumps(result, indent=2))
                    break
                elif status == "failed":
                    print("❌ Job failed!")
                    error = job_status.get("error")
                    if error:
                        print(f"Error: {error}")
                    break
                elif status in ["pending", "running"]:
                    print(f"⏳ Job is {status}...")
                    time.sleep(2)
                else:
                    print(f"❓ Unknown status: {status}")
                    break
            else:
                print(f"❌ Failed to get job status: {response.status_code}")
                break

        except Exception as e:
            print(f"❌ Error polling job status: {e}")
            break

        # Check timeout
        if time.time() - start_time > max_wait_time:
            print("⏰ Timeout waiting for job completion")
            break

    # 5. Get final user count
    print("\n5. Getting final user count...")
    try:
        response = requests.get(f"{base_url}/users/count")
        final_count = response.json()["total_users"]
        print(f"📊 Final user count: {final_count}")

        users_added = final_count - initial_count
        if users_added > 0:
            print(f"✅ Successfully added {users_added} users!")
        else:
            print("❌ No users were added")
    except Exception as e:
        print(f"❌ Failed to get final user count: {e}")

    # 6. Show recent users
    print("\n6. Showing recent users...")
    try:
        response = requests.get(f"{base_url}/users?limit=5")
        if response.status_code == 200:
            users = response.json()
            print(f"📋 Recent users (showing first 5):")
            for user in users[:5]:
                print(f"  - {user['name']} ({user['email']})")
        else:
            print(f"❌ Failed to get users: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to get users: {e}")

    print("\n" + "=" * 50)
    print("🎉 Workflow test completed!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test FastAPI Dramatiq workflow")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the FastAPI application",
    )

    args = parser.parse_args()
    test_workflow(args.url)
