import os

DEBUG = os.getenv("ENV", "TEST") in ["TEST", "LOCAL"]

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
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "main_formatter",
        }
    },
    "loggers": {
        "": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
        },
        # # Remove all pymongo.* loggers
        "httpcore": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        # "fastapi": {
        #     "handlers": ["console"],
        #     "level": "DEBUG" if DEBUG else "INFO",
        # },
        # "uvicorn": {
        #     "handlers": ["console"],
        #     "level": "DEBUG" if DEBUG else "INFO",
        # },
        # "gunicorn.error": {
        #     "handlers": ["console"],
        #     "level": "DEBUG" if DEBUG else "INFO",
        # },
    },
}
