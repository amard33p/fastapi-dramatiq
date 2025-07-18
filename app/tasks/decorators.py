import functools
from typing import Callable, Any
from ..db import transactional_worker_session


def with_session(fn: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        with transactional_worker_session() as db:
            return fn(*args, db=db, **kwargs)

    return wrapper
