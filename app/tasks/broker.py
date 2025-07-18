# app/tasks/broker.py
"""Dramatiq broker configuration with explicit SQLAlchemy‑session middleware."""

import dramatiq
from dramatiq_pg import PostgresBroker
from dramatiq.middleware import CurrentMessage
from periodiq import PeriodiqMiddleware

from ..settings import settings

# --- production broker ------------------------------------------------------
postgres_broker = PostgresBroker(url=settings.database_url)
postgres_broker.add_middleware(CurrentMessage())
postgres_broker.add_middleware(PeriodiqMiddleware(skip_delay=30))


# --- choose at import time ---------------------------------------------------
dramatiq.set_broker(postgres_broker)
