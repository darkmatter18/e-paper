"""Logging configuration using Pydantic settings.

This module provides the default logging configuration dictionary for the application.
Logging level is controlled via Pydantic settings (LOG_LEVEL environment variable).
"""

from settings.settings import get_settings

# Get logging level from Pydantic settings
_settings = get_settings()
LOG_LEVEL = _settings.logging.level

DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "main_formatter": {
            "format": "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d[%(process)d, %(thread)d] - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "main_formatter",
        }
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
        },
        # Keep httpcore at INFO to avoid excessive debug output
        "httpcore": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
