# FastAPI Dramatiq Demo

A demonstration project showcasing FastAPI with Dramatiq for background task processing, featuring a complete workflow that fetches, transforms, and stores user data.

## Architecture

The application consists of several components:

- **FastAPI Backend**: REST API server
- **Dramatiq Workers**: Background task processors
- **PostgreSQL**: Primary database
- **RabbitMQ**: Message broker for task queuing
- **Redis**: Results backend for task results

## Project Structure

```
fastapi-dramatiq-demo/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
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
        ├── broker.py      # Dramatiq broker configuration
        └── jobs.py        # Background tasks
```

## Workflow Overview

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

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### Running with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd fastapi-dramatiq-demo
```

2. Start all services:
```bash
docker-compose up -d
```

3. Check service status:
```bash
docker-compose ps
```

### Services and Ports

- **FastAPI Backend**: http://localhost:8000
- **RabbitMQ Management**: http://localhost:15672 (admin/admin)
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## API Endpoints

### Main Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /process_users` - Start user processing workflow
- `GET /jobs/{job_id}/status` - Get job status
- `GET /jobs` - List all jobs (with pagination)
- `GET /users` - List all users (with pagination)
- `GET /users/count` - Get total user count

### API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Usage Examples

### 1. Start User Processing Workflow

```bash
curl -X POST http://localhost:8000/process_users
```

Response:
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "User processing workflow started successfully"
}
```

### 2. Check Job Status

```bash
curl http://localhost:8000/jobs/123e4567-e89b-12d3-a456-426614174000/status
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "result": {
    "workflow_completed": true,
    "steps_completed": 4,
    "users_fetched": 10,
    "users_transformed": 10,
    "delay_info": "Processed with 3s delay",
    "database_result": {
      "users_created": 10,
      "user_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }
  },
  "error": null,
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-01T12:00:05Z",
  "completed_at": "2025-01-01T12:00:05Z"
}
```

### 3. List Created Users

```bash
curl http://localhost:8000/users
```

### 4. Get User Count

```bash
curl http://localhost:8000/users/count
```

## Job Status Values

- `pending`: Job has been queued but not started
- `running`: Job is currently being processed
- `completed`: Job completed successfully
- `failed`: Job failed with an error

## Configuration

Environment variables can be set in a `.env` file:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_dramatiq
RABBITMQ_URL=amqp://admin:admin@localhost:5672/
REDIS_URL=redis://localhost:6379/0
MIN_DELAY=1
MAX_DELAY=5
```

## Development

### Local Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start external services:
```bash
docker-compose up -d db rabbitmq redis
```

3. Run the FastAPI server:
```bash
uvicorn app.api:app --reload
```

4. In another terminal, start Dramatiq workers:
```bash
dramatiq app.tasks.jobs
```

### Database Migrations

The application automatically creates tables on startup. For production, consider using Alembic for migrations:

```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Monitoring

### RabbitMQ Management

Access the RabbitMQ management interface at http://localhost:15672:
- Username: `admin`
- Password: `admin`

Monitor:
- Queue lengths
- Message rates
- Consumer connections

### Application Logs

View logs for different services:

```bash
# Backend logs
docker-compose logs -f backend

# Worker logs
docker-compose logs -f worker

# All logs
docker-compose logs -f
```

## Production Considerations

### Security

- Change default passwords for RabbitMQ and PostgreSQL
- Use environment variables for sensitive configuration
- Implement API authentication/authorization
- Use HTTPS in production

### Scaling

- Scale workers: `docker-compose up -d --scale worker=4`
- Use a load balancer for multiple backend instances
- Consider using a managed database service
- Implement proper monitoring and alerting

### Error Handling

- Configure retry policies per task type
- Implement dead letter queues for failed tasks
- Add comprehensive logging and monitoring
- Set up health checks for all services

## Testing

### Manual Testing

1. Start the application:
```bash
docker-compose up -d
```

2. Run the workflow:
```bash
curl -X POST http://localhost:8000/process_users
```

3. Monitor the job status until completion

4. Verify users were created:
```bash
curl http://localhost:8000/users/count
```

### Automated Testing

Create a test script:

```python
import requests
import time

# Start workflow
response = requests.post("http://localhost:8000/process_users")
job_id = response.json()["job_id"]

# Poll status
while True:
    status_response = requests.get(f"http://localhost:8000/jobs/{job_id}/status")
    status = status_response.json()["status"]
    
    if status in ["completed", "failed"]:
        print(f"Job {job_id} finished with status: {status}")
        break
    
    time.sleep(1)
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check PostgreSQL container is running
   - Verify DATABASE_URL is correct

2. **RabbitMQ Connection Error**
   - Check RabbitMQ container is running
   - Verify RABBITMQ_URL is correct

3. **Tasks Not Processing**
   - Check worker containers are running
   - Verify tasks are queued in RabbitMQ management interface

4. **External API Timeout**
   - The external API (jsonplaceholder.typicode.com) might be slow
   - Check network connectivity

### Debug Commands

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs worker

# Access database
docker-compose exec db psql -U postgres -d fastapi_dramatiq

# Access RabbitMQ
docker-compose exec rabbitmq rabbitmqctl list_queues
```

## License

This project is for demonstration purposes.