"""Broker configuration using dramatiq-pg.

This follows the pattern used in dramatiq-pg's official example script.
The broker talks to PostgreSQL via a psycopg2 ThreadedConnectionPool that
is built from the DATABASE_URL environment variable (or falls back to the
project's default URL).
"""

import importlib

import dramatiq
from dramatiq.results import Results

from ..settings import settings


def _import(path: str):
    """Import dotted path and return attribute."""
    module_name, attr = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, attr)


# Select configuration (prod vs. tests)
config = (
    settings.DRAMATIQ_TEST_CONFIG if settings.testing else settings.DRAMATIQ_PROD_CONFIG
)

# Instantiate broker
BrokerCls = _import(config["BROKER"])
broker = BrokerCls(**config.get("OPTIONS", {}))

# Attach middleware defined in settings
for mw_path in config.get("MIDDLEWARE", []):
    MWCls = _import(mw_path)
    broker.add_middleware(MWCls())

# Optional results backend
backend_cfg = config.get("RESULT_BACKEND")
if backend_cfg:
    BackendCls = _import(backend_cfg["CLASS"])
    backend = BackendCls(**backend_cfg.get("KWARGS", {}))
    broker.add_middleware(Results(backend=backend))

# Set as default broker
dramatiq.set_broker(broker)
