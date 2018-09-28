"""logs.py

Initialize loggers
"""

from typing import Any
import logging
import logging.handlers

try:
    import colorlog
    use_colors = True
except ImportError:
    use_colors = False


LEVEL_PREFIX = {
    'DEBUG': 'd',
    'INFO': '+',
    'WARNING': '!',
    'ERROR': '-',
    'CRITICAL': 'x'
}

LOG_COLORS = {
    'DEBUG': 'white,bold',
    'INFO': 'green,bold',
    'WARNING': 'yellow,bold',
    'ERROR': 'red,bold',
    'CRITICAL': 'red,bold,bg_white',
}


def set_logger(level: str, logfile: str = None,
               catch_warnings: bool = False) -> logging.Logger:
    """Initialize loggers"""
    package_logger = logging.getLogger('terracotta')
    package_logger.setLevel(level.upper())

    # stream handler
    ch = logging.StreamHandler()
    ch_fmt: logging.Formatter

    if use_colors:
        fmt = ' {log_color!s}[{levelname!s}]{reset!s} {message!s}'

        class ColoredPrefixFormatter(colorlog.ColoredFormatter):
            def format(self, record: Any, *args: Any) -> Any:
                record.levelname = LEVEL_PREFIX[record.levelname]
                return super().format(record, *args)

        ch_fmt = ColoredPrefixFormatter(fmt, log_colors=LOG_COLORS, style='{')
    else:
        fmt = ' [{levelname!s}] {message!s}'

        class PrefixFormatter(logging.Formatter):
            def format(self, record: Any) -> Any:
                record.levelname = LEVEL_PREFIX[record.levelname]
                return super().format(record)

        ch_fmt = PrefixFormatter(fmt, style='{')

    ch.setFormatter(ch_fmt)
    package_logger.handlers.append(ch)

    # file handler
    if logfile:
        fh = logging.handlers.RotatingFileHandler(
            logfile, maxBytes=10 * 1024 * 1024, backupCount=10
        )
        fh.setLevel(level.upper())
        fh_fmt = logging.Formatter('{asctime} [{levelname!s}] {message!s}',
                                   datefmt='%Y-%m-%d %H:%M:%S', style='{')
        fh.setFormatter(fh_fmt)
        package_logger.handlers.append(fh)

    logging.captureWarnings(catch_warnings)

    return package_logger
