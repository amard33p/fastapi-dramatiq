import os

from pydantic_settings import BaseSettings
from typing import Dict, Any


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@db:5432/fastapi_dramatiq"
    # rabbitmq_url: str = "amqp://admin:admin@localhost:5672/"
    # redis_url: str = "redis://localhost:6379/0"

    # API settings
    api_title: str = "FastAPI Dramatiq Demo"
    api_version: str = "1.0.0"

    # External API
    jsonplaceholder_url: str = "https://jsonplaceholder.typicode.com/users"

    # Task settings
    min_delay: int = 1
    max_delay: int = 5

    # Dramatiq configuration dictionaries
    DRAMATIQ_PROD_CONFIG: Dict[str, Any] = {
        # Use PostgreSQL as both broker and result backend via dramatiq-pg
        "BROKER": "dramatiq_pg.PostgresBroker",
        "OPTIONS": {"url": "postgresql://postgres:postgres@db:5432/fastapi_dramatiq"},
        "MIDDLEWARE": [
            "dramatiq.middleware.CurrentMessage",
            "dramatiq.middleware.Retries",
            "dramatiq.middleware.TimeLimit",
        ],
    }

    DRAMATIQ_TEST_CONFIG: Dict[str, Any] = {
        "BROKER": "dramatiq.brokers.stub.StubBroker",
        "OPTIONS": {},
        "MIDDLEWARE": [
            "dramatiq.middleware.AgeLimit",
            "dramatiq.middleware.TimeLimit",
            "dramatiq.middleware.Callbacks",
            "dramatiq.middleware.Pipelines",
            "dramatiq.middleware.Retries",
        ],
        "RESULT_BACKEND": {
            "CLASS": "dramatiq.results.backends.StubBackend",
            "KWARGS": {},
        },
    }

    # Flag to switch between prod and test config
    testing: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
