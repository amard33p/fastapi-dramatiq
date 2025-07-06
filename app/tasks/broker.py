import importlib
import dramatiq

from dramatiq.results import Results


from ..settings import settings

# Dynamically build broker based on settings


# Set as default broker
def _import_from_path(path: str):
    module_name, cls_name = path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, cls_name)


cfg = (
    settings.DRAMATIQ_TEST_CONFIG if settings.testing else settings.DRAMATIQ_PROD_CONFIG
)

BrokerCls = _import_from_path(cfg["BROKER"])

broker = BrokerCls(**cfg.get("OPTIONS", {}))

# add middleware from list
for mw_path in cfg.get("MIDDLEWARE", []):
    MWCls = _import_from_path(mw_path)
    broker.add_middleware(MWCls())

# attach results backend as specified
backend_cfg = cfg.get("RESULT_BACKEND")
if backend_cfg:
    BackendCls = _import_from_path(backend_cfg["CLASS"])
    backend = BackendCls(**backend_cfg.get("KWARGS", {}))
    broker.add_middleware(Results(backend=backend))

dramatiq.set_broker(broker)
