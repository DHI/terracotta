"""profile.py

Decorators for performance tracing
"""

from typing import Callable, Any, Optional, TypeVar, ClassVar, cast
import logging
import functools
import inspect
import os

import wakati

from terracotta import get_settings
from terracotta.logs import TraceLogger

T = TypeVar('T')


class TraceContext:
    """Tracing context manager that can also be used as a decorator.

    If trace logging is enabled, creates log messages like

        +     0.14ms   drivers/base.py:283 (get_metadata)
        +     0.15ms   drivers/base.py:283 (get_metadata)
        ++    97.32μs  drivers/base.py:248 (get_datasets)
        ++    17.42ms  drivers/raster_base.py:232 (_get_raster_tile)
        ++    23.54ms  drivers/raster_base.py:157 (_calculate_default_transform)
        ++    18.06ms  drivers/raster_base.py:286 (_get_raster_tile)
        +     0.27s    drivers/raster_base.py:294 (get_raster_tile)
        +     1.70ms   image.py:101 (contrast_stretch)
        +     2.08ms   image.py:19 (array_to_png)
              0.29s    handlers/singleband.py:15 (singleband)
    """
    __stacklevel__: ClassVar[int] = 0  # stores current stack level, not thread-safe

    def __init__(self) -> None:
        self._close_xray: bool = False
        self._close_timer: bool = False
        self._description: Optional[str] = None

    @staticmethod
    def _get_package_basename(path: str) -> str:
        """Get relative path in Terracotta module from absolute path"""
        split_path = os.path.normpath(path).split(os.sep)
        try:
            cutoff = split_path[::-1].index('terracotta')
        except ValueError as exc:
            raise ValueError('Wrapped function is not from Terracotta '
                             '(@trace must be innermost decorator)') from exc
        return os.path.join(*split_path[-cutoff:])

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator mode"""
        # scrape information from wrapped function
        short_filename = self._get_package_basename(inspect.getfile(func))
        lineno = inspect.getsourcelines(func)[-1]
        self._description = f'{short_filename}:{lineno} ({func.__name__})'

        @functools.wraps(func)
        def inner(*args: Any, **kwargs: Any) -> T:
            with self:
                return func(*args, **kwargs)

        return inner

    def __enter__(self) -> None:
        stacklevel = TraceContext.__stacklevel__ = TraceContext.__stacklevel__ + 1

        if self._description is None:
            # this is not being used as a decorator, so inspect call stack instead
            caller = inspect.getframeinfo(inspect.stack()[1][0])
            short_filename = self._get_package_basename(caller.filename)
            self._description = f'{short_filename}:{caller.lineno} ({caller.function})'

        # initialize XRAY
        settings = get_settings()
        if settings.XRAY_PROFILE:
            from aws_xray_sdk.core import xray_recorder
            xray_recorder.begin_subsegment(self._description)
            self._close_xray = True

        # initialize log timer
        logger = cast(TraceLogger, logging.getLogger(__name__))
        if logger.isEnabledFor(logger.TRACE):
            self._timer = wakati.Timer(self._description, report_to=logger.trace,
                                       message='{stack_prefix:<5} {elapsed:<8} {name}')
            self._timer.stack_prefix = '+' * (stacklevel - 1)
            self._timer.__enter__()
            self._close_timer = True

    def __exit__(self, *exc: Any) -> bool:
        TraceContext.__stacklevel__ -= 1

        if self._close_timer:
            self._timer.__exit__(*exc)

        if self._close_xray:
            from aws_xray_sdk.core import xray_recorder
            xray_recorder.end_subsegment()

        return False


trace = TraceContext
