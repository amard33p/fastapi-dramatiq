from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/fastapi_dramatiq"
    rabbitmq_url: str = "amqp://admin:admin@localhost:5672/"
    redis_url: str = "redis://localhost:6379/0"

    # API settings
    api_title: str = "FastAPI Dramatiq Demo"
    api_version: str = "1.0.0"

    # External API
    jsonplaceholder_url: str = "https://jsonplaceholder.typicode.com/users"

    # Task settings
    min_delay: int = 1
    max_delay: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
