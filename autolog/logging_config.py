import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGGING_FILE = Path.home() / os.environ.get("LOG_FILE", ".autolog.log")


def setup_logging():
    """
    Configure the logging for the application.

    This sets up a root logger with two handlers:
    - A console handler that logs to stdout,
      with level DEBUG if AUTOLOG_DEBUG is True, else INFO.
    - A rotating file handler that logs to the file
      specified by LOG_FILE environment variable,
      or 'application.log' by default, with level INFO.

    The console handler is only added
    if CONSOLE_LOGGING environment variable is 'True' (default).
    """
    logger = logging.getLogger()

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    debug_mode = os.environ.get("AUTOLOG_DEBUG", "False") == "True"
    log_level = logging.DEBUG if debug_mode else logging.INFO
    logger.setLevel(log_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)

    # File handler
    log_file = LOGGING_FILE
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10485760, backupCount=1
    )  # 10MB per file, keep 1 backup
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    logger.addHandler(file_handler)
