"""logs.py

Initialize loggers
"""

from typing import List, Any
import logging

from terracotta import get_settings


class TraceLogger(logging.getLoggerClass()):  # type: ignore
    TRACE = 5

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        logging.addLevelName(TraceLogger.TRACE, 'TRACE')

    def trace(self, msg: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(TraceLogger.TRACE):
            self._log(TraceLogger.TRACE, msg, args, **kwargs)


logging.setLoggerClass(TraceLogger)


LOG_COLORS = {
    'TRACE': 'purple',
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'red,bg_white',
}


def set_logger(level: str = None, logfile: str = None) -> List[logging.Logger]:
    """Initialize loggers"""
    try:
        import colorlog
        use_colors = True
    except ImportError:
        use_colors = False

    settings = get_settings()

    if level is None:
        level = settings.LOGLEVEL

    package_logger = logging.getLogger('terracotta')
    package_logger.setLevel(level.upper())

    # stream
    ch = logging.StreamHandler()
    if use_colors:
        fmt = '  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s'
        ch_fmt = colorlog.ColoredFormatter(fmt, log_colors=LOG_COLORS)
    else:
        fmt = ' %(levelname)-8s | %(message)s'
        ch_fmt = logging.Formatter(fmt)
    ch.setFormatter(ch_fmt)

    # remember all relevant dependencies
    external = [
        logging.getLogger('rasterio')
    ]

    for logger in external:
        logger.setLevel('ERROR')

    all_loggers = [package_logger, *external]
    for logger in all_loggers:
        logger.handlers = [h for h in logger.handlers if not isinstance(h, logging.StreamHandler)]
        logger.handlers.append(ch)

    if logfile is None:
        logfile = settings.LOGFILE

    if logfile:
        fh = logging.FileHandler(logfile)
        fh.setLevel(level.upper())
        fh_fmt = logging.Formatter('%(name)s - %(levelname)-8s | %(message)s')
        fh.setFormatter(fh_fmt)

        for logger in all_loggers:
            logger.addHandler(fh)

    return all_loggers
