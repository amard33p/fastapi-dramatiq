from pydantic_settings import BaseSettings
from typing import Dict, Any
from typing import Optional


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/fastapi_dramatiq"
    rabbitmq_url: str = "amqp://admin:admin@rabbitmq:5672/"
    redis_url: str = "redis://redis:6379/0"

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
        "BROKER": "dramatiq.brokers.rabbitmq.RabbitmqBroker",
        "OPTIONS": {"url": "amqp://admin:admin@rabbitmq:5672/"},
        "MIDDLEWARE": [
            "dramatiq.middleware.CurrentMessage",
        ],
        "RESULT_BACKEND": {
            "CLASS": "dramatiq.results.backends.RedisBackend",
            "KWARGS": {"url": "redis://redis:6379/0"},
        },
    }

    DRAMATIQ_TEST_CONFIG: Dict[str, Any] = {
        "BROKER": "dramatiq.brokers.stub.StubBroker",
        "OPTIONS": {},
        "MIDDLEWARE": [],
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
