from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    db_user: str = Field(..., alias="POSTGRES_USER")
    db_password: str = Field(..., alias="POSTGRES_PASSWORD")
    db_host: str = Field(
        default="db", alias="POSTGRES_HOST"
    )  # default hostname inside Docker network
    db_port: int = Field(..., alias="POSTGRES_PORT")
    db_name: str = Field(..., alias="POSTGRES_DB")

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


settings = Settings()
