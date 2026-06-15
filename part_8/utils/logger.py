import logging
import sys

from config import get_config

LOG_FORMAT = "%(asctime)s L:%(lineno)d - %(name)s - %(levelname)s -\n   %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """Return a logger that writes formatted records to stdout.

    The logger is configured only once per name, so repeated calls reuse the
    same instance instead of attaching duplicate handlers.
    """
    logger = logging.getLogger(name)

    # logging caches loggers by name, so an existing handler means this logger
    # was already configured by an earlier call.
    if not logger.handlers:
        logger.setLevel(get_config().log_level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT))
        logger.addHandler(handler)

    return logger
