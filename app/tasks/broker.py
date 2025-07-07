"""Broker configuration using dramatiq-pg."""

import dramatiq

from dramatiq_pg import PostgresBroker
from dramatiq_pg.results import PostgresBackend
from dramatiq.brokers.stub import StubBroker
from dramatiq.middleware import CurrentMessage, Middleware
from dramatiq.results import Results
from dramatiq.results.backends.stub import StubBackend

from ..settings import settings

import inspect

from ..db import SessionLocal


class SQLAlchemyMiddleware(Middleware):
    def before_process_message(self, broker, message):
        """Inject a SQLAlchemy session only when the actor expects a ``db`` kwarg."""
        if "db" in inspect.signature(message.actor.fn).parameters:
            session = SessionLocal()
            message.kwargs["db"] = session
            # Remember to clean up later
            message.options["_db_session"] = session

    def after_process_message(self, broker, message, *, result=None, exception=None):
        db = message.kwargs.get("db")
        if db:
            if exception:
                db.rollback()
            else:
                db.commit()
            db.close()


# Production broker: Postgres-backed broker with CurrentMessage middleware and Postgres results backend
postgres_broker = PostgresBroker(url=settings.database_url)
postgres_broker.add_middleware(CurrentMessage())

postgres_broker.add_middleware(SQLAlchemyMiddleware())

# Test broker: in-memory StubBroker with StubBackend for results
stub_broker = StubBroker()
stub_broker.add_middleware(Results(backend=StubBackend()))
stub_broker.add_middleware(SQLAlchemyMiddleware())

# Decide which broker should be the default depending on the execution mode
broker = stub_broker if settings.testing else postgres_broker

dramatiq.set_broker(broker)
