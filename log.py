import os
import sys
import logging
import logstash

import coloredlogs


def init_logger(use_logstash=True):
    class CustomLogger(logging.Logger):

        def _log(self, level, msg, args, exc_info=None, extra=None):
            super(CustomLogger, self)._log(level, msg, args, exc_info, extra)

    logging.setLoggerClass(CustomLogger)
    log = logging.getLogger('subtocall')
    log.setLevel(logging.DEBUG)
    if use_logstash:
        log.addHandler(logstash.TCPLogstashHandler('bla.com', 5000,
                                                   version=1))

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(module)s%(lineno)-3s %(message)s")
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(formatter)
    log.addHandler(consoleHandler)
    coloredlogs.install(
        level='DEBUG', logger=log,
        stream=sys.stdout,
        fmt="%(asctime)s [%(levelname)-8s] %(module)-10s %(lineno)-3s %(message)s")

    # Twisted logger which logs deeper failures
    logt = logging.getLogger('twisted')
    logt.addHandler(consoleHandler)

    return log
