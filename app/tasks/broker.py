"""Broker configuration using dramatiq-pg."""

import dramatiq

from dramatiq_pg import PostgresBroker
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware import CurrentMessage
from dramatiq.results import Results
from dramatiq.results.backends.stub import StubBackend

from ..settings import settings

# Production broker: Postgres-backed broker with CurrentMessage middleware and Postgres results backend
postgres_broker = PostgresBroker(url=settings.database_url)
postgres_broker.add_middleware(CurrentMessage())

# Test broker: in-memory StubBroker with StubBackend for results
stub_broker = StubBroker()
stub_broker.add_middleware(Results(backend=StubBackend()))

# Decide which broker should be the default depending on the execution mode
broker = stub_broker if settings.testing else postgres_broker

dramatiq.set_broker(broker)
