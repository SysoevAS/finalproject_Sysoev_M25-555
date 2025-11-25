import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOGGING_CONFIGURED = False


def configure_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    logfile = logs_dir / "app.log"

    handler = RotatingFileHandler(
        logfile,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )

    fmt = (
        "%(levelname)s %(asctime)s "
        "%(name)s %(funcName)s: %(message)s"
    )
    formatter = logging.Formatter(fmt=fmt, datefmt="%Y-%m-%dT%H:%M:%S")
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    _LOGGING_CONFIGURED = True
