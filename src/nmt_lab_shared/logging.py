from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from .monitoring import Clock, get_clock, stop

_LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _resolve_logger(logger: logging.Logger | str) -> logging.Logger:
    return logging.getLogger(logger) if isinstance(logger, str) else logger


def close_logger(logger: logging.Logger | str) -> None:
    resolved_logger = _resolve_logger(logger)
    for handler in resolved_logger.handlers[:]:
        resolved_logger.removeHandler(handler)
        handler.close()


def get_logger(name: str, *, log_path: str | Path | None = None, stream: bool = False) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    close_logger(logger)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)

    if stream:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    if log_path is not None:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_calls(
    logger: logging.Logger | str,
    *,
    level: int = logging.INFO,
    clock: Clock | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    resolved_logger = _resolve_logger(logger)

    def decorate(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            active_clock = clock or get_clock(func.__name__)
            resolved_logger.log(level, "Start %s", func.__name__)
            try:
                return func(*args, **kwargs)
            finally:
                duration = stop(active_clock)
                resolved_logger.log(level, "Finished %s in %.3fs", func.__name__, duration or 0.0)

        return wrapper

    return decorate
