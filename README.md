# FastAPI Dramatiq, Periodiq Demo with PostgreSQL Only

This project demonstrates a FastAPI application integrated with [Dramatiq](https://dramatiq.io/) for background task processing and [Periodiq](https://gitlab.com/bersace/periodiq) for periodic task scheduling. It uses [dramatiq-pg](https://gitlab.com/dalibo/dramatiq-pg), which leverages just PostgreSQL for both the message broker and the results backend, removing the need for RabbitMQ and Redis.

Checkout the branch [redis-rabbitmq](https://github.com/amard33p/fastapi-dramatiq/tree/redis-rabbitmq) if you instead want to use Redis as result backend and RabbitMQ as broker.


## Prerequisites

- Docker
- Python 3.10+

## Getting Started

To build the Docker images and start the FastAPI application, Dramatiq worker, and PostgreSQL database, run:

```bash
docker compose watch
```

This command will watch for file changes and automatically rebuild and restart the services.

## Running a Real Workflow

To test a complete workflow, you can run the `check_real_workflow.py` script. This script will send a task to the Dramatiq worker and print the result.

```bash
python check_real_workflow.py
```

## Running Tests

The project also demonstrates how to test E2E a fastapi + dramatiq (or any other job queue) setup which can be challenging due to async nature of the setup.

```bash
pytest -v tests/test_workflow.py
```

## Project Structure

```
fastapi-dramatiq-demo/
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── app/
    ├── api.py              # FastAPI application
    ├── settings.py         # Configuration settings
    ├── db.py              # Database setup
    ├── models.py          # SQLAlchemy models
    ├── schemas.py         # Pydantic schemas
    ├── crud.py            # Database operations
    └── tasks/
        ├── __init__.py
        ├── broker.py            # Dramatiq broker configuration
        └── jobs.py              # Background tasks
        └── scheduled_jobs.py    # Periodiq scheduled jobs
```

## Dramatiq Workflow Overview

The main workflow (`process_users`) performs the following steps:

1. **Fetch Users**: Makes a GET request to `https://jsonplaceholder.typicode.com/users`
2. **Transform Data**: Converts external API data to internal schema
3. **Simulate Processing**: Adds a random delay (1-5 seconds)
4. **Save to Database**: Stores users in PostgreSQL using SQLAlchemy

Each step is implemented as a separate Dramatiq task, allowing for:
- Individual task monitoring
- Retry logic per step
- Independent scaling
- Better error handling


### Services and Ports

- **FastAPI Backend**: http://localhost:8000
- **PostgreSQL**: localhost:5432

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /process_users` - Start user processing workflow
- `GET /jobs/{job_id}/status` - Get job status
- `GET /jobs` - List all jobs (with pagination)
- `GET /users` - List all users (with pagination)
- `GET /users/count` - Get total user count
