# app/tasks/broker.py
"""Dramatiq broker configuration with explicit SQLAlchemy‑session middleware."""

import dramatiq
from dramatiq_pg import PostgresBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware import CurrentMessage
from periodiq import PeriodiqMiddleware
from dramatiq.results import Results
from dramatiq.results.backends.stub import StubBackend
from ..settings import settings

# --- production broker ------------------------------------------------------
postgres_broker = PostgresBroker(url=settings.database_url)
postgres_broker.add_middleware(CurrentMessage())
postgres_broker.add_middleware(PeriodiqMiddleware(skip_delay=30))

# --- in‑memory broker for tests ---------------------------------------------
stub_broker = StubBroker()
stub_broker.add_middleware(Results(backend=StubBackend()))
stub_broker.add_middleware(PeriodiqMiddleware(skip_delay=30))

# --- choose at import time ---------------------------------------------------
dramatiq.set_broker(stub_broker if settings.testing else postgres_broker)
