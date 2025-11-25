import functools
import logging
from datetime import datetime
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def log_action(action: str, verbose: bool = False) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            timestamp = datetime.utcnow().isoformat()
            username = kwargs.get("username") or kwargs.get("current_username")
            msg_prefix = (
                f"{action} ts={timestamp} user={username if username else '-'}"
            )
            logger.info("%s started", msg_prefix)
            try:
                result = func(*args, **kwargs)
                if verbose and isinstance(result, dict):
                    logger.info("%s OK details=%s", msg_prefix, result)
                else:
                    logger.info("%s OK", msg_prefix)
                return result
            except Exception as exc:
                logger.error(
                    "%s ERROR type=%s msg=%s",
                    msg_prefix,
                    type(exc).__name__,
                    str(exc),
                )
                raise

        return wrapper

    return decorator
