"""Logging and redaction helpers."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Iterable

SENSITIVE_VALUE = "[redacted]"
LOG_FILE_NAME = "qrwatch.log"
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def redact(value: str | None) -> str:
    """Return a redacted marker for non-empty sensitive values."""

    if not value:
        return ""
    return SENSITIVE_VALUE


def redact_text(value: str, secrets: Iterable[str | None] = ()) -> str:
    """Replace configured secret values in a string."""

    redacted = value
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, SENSITIVE_VALUE)
    return redacted


def redact_error(error: BaseException, secrets: Iterable[str | None] = ()) -> str:
    """Return a redacted error message suitable for logs."""

    return redact_text(str(error), secrets)


def configure_logging(
    log_dir: str | Path,
    *,
    level: str = "INFO",
    console: bool = True,
) -> Path:
    """Configure QR Watch file logging and return the active log path."""

    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    log_path = path / LOG_FILE_NAME
    log_level = getattr(logging, level.upper(), logging.INFO)
    formatter = logging.Formatter(LOG_FORMAT)

    logger = logging.getLogger("qrwatch")
    logger.setLevel(log_level)
    logger.propagate = False

    for handler in tuple(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return log_path
