import logging
import logging.config

from settings.log import DEFAULT_LOGGING


def configure_logging():
    logging.config.dictConfig(DEFAULT_LOGGING)
