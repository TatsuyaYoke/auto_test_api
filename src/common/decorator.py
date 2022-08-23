import logging
from typing import Any, Callable


def exception(logger: logging.Logger) -> Any:
    def _exception(func: Callable[..., Any]) -> Any:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                response = func(*args, **kwargs)
                return response
            except Exception as error:
                logger.error(error)
                return {"success": False, "error": "Unexpected error. See log for details"}

        return wrapper

    return _exception
