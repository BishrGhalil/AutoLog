import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


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
    logger.setLevel(logging.DEBUG)  # Allow all levels to be processed

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # Console handler
    if os.environ.get("CONSOLE_LOGGING", "True") == "True":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        debug_mode = os.environ.get("AUTOLOG_DEBUG", "False") == "True"
        console_handler.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        logger.addHandler(console_handler)

    # File handler
    home_dir = Path.home()
    log_file = home_dir / os.environ.get("LOG_FILE", ".autolog.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10485760, backupCount=1
    )  # 10MB per file, keep 5 backups
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
