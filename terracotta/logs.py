"""logs.py

Provides logging utilities.
"""

from typing import Any
import logging
import logging.handlers

try:
    import colorlog
    use_colors = True
except ImportError:  # pragma: no cover
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
    'CRITICAL': 'red,bold',
}


def set_logger(level: str, catch_warnings: bool = False) -> logging.Logger:
    """Initialize loggers"""
    level = level.upper()

    package_logger = logging.getLogger('terracotta')
    package_logger.setLevel(level)

    # stream handler
    ch = logging.StreamHandler()
    ch_fmt: logging.Formatter

    if use_colors:
        fmt = ' {log_color!s}[{levelshortname!s}]{reset!s} {message!s}'

        class ColoredPrefixFormatter(colorlog.ColoredFormatter):
            def format(self, record: Any, *args: Any) -> Any:
                record.levelshortname = LEVEL_PREFIX[record.levelname]
                return super().format(record, *args)

        ch_fmt = ColoredPrefixFormatter(fmt, log_colors=LOG_COLORS, style='{')
    else:
        fmt = ' [{levelshortname!s}] {message!s}'

        class PrefixFormatter(logging.Formatter):
            def format(self, record: Any) -> Any:
                record.levelshortname = LEVEL_PREFIX[record.levelname]
                return super().format(record)

        ch_fmt = PrefixFormatter(fmt, style='{')

    ch.setFormatter(ch_fmt)
    package_logger.handlers = [ch]

    if catch_warnings:
        logging.captureWarnings(True)
        warnings_logger = logging.getLogger('py.warnings')
        warnings_logger.handlers = [ch]
        warnings_logger.setLevel(level)

    return package_logger
