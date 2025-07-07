from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database connection components – assembled dynamically
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_name: str = "fastapi_dramatiq"
    db_port: int = 5432
    db_host: str = "db"  # default hostname inside Docker network
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

    # Flag to switch between prod and test config
    testing: bool = False

    @property
    def database_url(self) -> str:  # noqa: D401 – simple property
        """Return SQLAlchemy database URL.

        If *testing* is set to **True** (patched in *tests/conftest.py*), use
        ``localhost`` so that pytest (running on the host) can connect to the
        Postgres instance published by Docker Compose. Otherwise default to the
        in-network service name ``db`` which resolves inside the Docker
        network.
        """
        host = "localhost" if self.testing else self.db_host
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{host}:{self.db_port}/{self.db_name}"
        )

    class Config:
        env_file = ".env"


settings = Settings()
