import functools
from typing import Callable, Any
from ..db import transactional_worker_session


def with_session(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Wrap a Dramatiq actor so it receives a SQLAlchemy Session **only if**
    the caller didn't supply one (`db=`).
    Works equally in production and in tests that pass an already‑open
    transactional session.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if "db" in kwargs and kwargs["db"] is not None:
            # Test (or caller) supplied a session → use it verbatim.
            return fn(*args, **kwargs)

        with transactional_worker_session() as db:
            return fn(*args, db=db, **kwargs)

    return wrapper
