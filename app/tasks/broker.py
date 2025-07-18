"""Dramatiq broker configuration with explicit SQLAlchemy‑session middleware and fastapi-injectable setup."""

import dramatiq
import logging
from dramatiq_pg import PostgresBroker
from dramatiq.middleware import CurrentMessage
from periodiq import PeriodiqMiddleware
from fastapi_injectable import setup_graceful_shutdown
from fastapi_injectable.concurrency import loop_manager

from ..settings import settings

# Configure fastapi-injectable to use background_thread loop strategy
# This allows async code to run from any thread without blocking
# Perfect for Dramatiq's thread-based worker environment
loop_manager.set_loop_strategy("background_thread")

# Configure logging
logger = logging.getLogger(__name__)

# --- production broker ------------------------------------------------------
postgres_broker = PostgresBroker(url=settings.database_url)
postgres_broker.add_middleware(CurrentMessage())
postgres_broker.add_middleware(PeriodiqMiddleware(skip_delay=30))

# --- choose at import time ---------------------------------------------------
dramatiq.set_broker(postgres_broker)

# --- fastapi-injectable setup ------------------------------------------------
# Setup graceful shutdown to clean up resources when the application exits
# This will handle SIGTERM and SIGINT signals and clean up resources automatically
setup_graceful_shutdown()
