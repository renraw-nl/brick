"""
Debug Helpers

These will slow down production code, but may be useful still.
"""
import time
from collections.abc import Callable
from functools import partial, wraps
from typing import Any

from . import log


def callable_name(func: Callable) -> str:
    """
    Attempt to find the name of the given callable.

    Checks, `__qualname__`, `__name__` or "unknown name"
    """
    if hasattr(func, "__qualname__"):
        return func.__qualname__
    elif hasattr(func, "__name__"):
        return func.__name__

    return "unknown name"


def timeit(func: Callable = None, *, logger: log.LoggerType = None) -> Callable:
    """
    Log the duration passed to call a method.

    Logging is done to debug level.

    Optionally pass a specific logger to log to.
    """

    # @log_data(logger=logger) results in two calls to this method, one to register the
    # logger, directly followed by the actual decorating call. @...() is a method call,
    # but the `func` tool is not yet passed at this point. Hence a decorated method is
    # returned to handle the optional `logger` registration.
    if func is None:
        return partial(timeit, logger=logger)

    elif not callable(func):
        raise TypeError(
            "`func` is not Callable, was this timeit-decorator called with non-keyword"
            " arguments?",
        )

    name = callable_name(func)

    if not logger or not isinstance(logger, log.LoggerType):
        logger = log.logger(name)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper method"""

        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        logger.debug(
            "Method timed",
            name=name,
            duration=(time.perf_counter() - start_time),
            start_time=start_time,
        )
        return result

    return wrapper


def log_data(func: Callable = None, *, logger: log.LoggerType = None) -> Callable:
    """
    Log arguments and result of the decorated function.

    Logging is done to debug level.

    Optionally pass a specific logger to log to.
    """

    if func is None:
        return partial(log_data, logger=logger)

    elif not callable(func):
        raise TypeError(
            "`func` is not Callable, was this log_data-decorator called with "
            "non-keyword arguments?",
        )

    name = callable_name(func)

    if not logger or not isinstance(logger, log.LoggerType):
        logger = log.logger(name)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Wrapper method"""

        logger.debug(
            "Decorated method called, input logged", name=name, args=args, kwargs=kwargs
        )
        result = func(*args, **kwargs)
        logger.debug("Decorated method results logged", name=name, result=result)
        return result

    return wrapper
