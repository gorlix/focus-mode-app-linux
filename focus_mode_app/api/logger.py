"""
Dedicated logging handler for the Backend API.

Keeps HTTP access and error logs completely segregated from the main
application's daemon loop outputs.
"""

import logging
from logging.handlers import RotatingFileHandler
from focus_mode_app.api.config import API_LOG_FILE


def get_api_logger() -> logging.Logger:
    """
    Initialize and return a configured logger specifically for the API.

    Ensures that logs are written to the dedicated API_LOG_FILE without
    interfering with the application console stdout. Creates the logs
    directory if it doesn't already exist.

    Returns:
        logging.Logger: The initialized API logger instance.
    """
    logger = logging.getLogger("focus_mode_api")

    # Avoid duplicating logs if get_api_logger is called multiple times
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    API_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        str(API_LOG_FILE), maxBytes=1048576 * 5, backupCount=3  # 5 MB per file
    )

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.propagate = False  # Prevent logs from polluting root console loggers

    return logger

api_logger = get_api_logger()
