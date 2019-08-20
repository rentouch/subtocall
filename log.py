import os
import sys
import logging
import coloredlogs
from utils import COLORED_LOGS


def init_logger():
    class CustomLogger(logging.Logger):

        def _log(self, level, msg, args, exc_info=None, extra=None):
            super(CustomLogger, self)._log(level, msg, args, exc_info, extra)

    logging.setLoggerClass(CustomLogger)
    log = logging.getLogger('subtocall')
    log.setLevel(logging.DEBUG)

    format = "%(asctime)s [%(levelname)-8s] %(module)s %(lineno)s %(message)s"
    formatter = logging.Formatter(format)
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(formatter)
    log.addHandler(consoleHandler)

    if COLORED_LOGS:
        coloredlogs.install(
            level='DEBUG', logger=log, stream=sys.stdout, fmt=format)

    # Twisted logger which logs deeper failures
    logt = logging.getLogger('twisted')
    logt.addHandler(consoleHandler)

    return log
