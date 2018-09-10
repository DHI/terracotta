"""profile.py

Decorators for performance tracing
"""

from typing import Callable, Dict, Any, Optional, TypeVar, ClassVar, cast, Union
import logging
import functools
import inspect
import os
import re
import threading
from threading import Lock

import wakati

from terracotta import get_settings
from terracotta.logs import TraceLogger

T = TypeVar('T')


_lock = threading.Lock()


def trace_context_factory(initial_stacklevel=0):
    class TraceContextBase:
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

        NOTE: This class is not thread-safe
        """
        __stacklevel__ = initial_stacklevel

        def __init__(self, description, lineno=None, parent_function=None, filename=None) -> None:
            if not (bool(lineno) == bool(parent_function) == bool(filename)):
                raise ValueError()

            if description is not None and not re.match(r'\w+', description):
                raise ValueError()

            self._description: str = description
            self._lineno = lineno
            self._parent_function = parent_function
            self._filename = filename

        @staticmethod
        def _get_package_basename(path: str) -> str:
            """Get relative path in Terracotta module from absolute path"""
            path_norm = os.path.realpath(path)
            base_path = os.path.realpath(os.path.dirname(__file__))
            if not path_norm.startswith(base_path):
                raise ValueError('Wrapped function is not from Terracotta '
                                 '(@trace must be innermost decorator)') from exc
            return '/'.join(os.path.relpath(path_norm, base_path).split(os.sep))

        def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
            """Decorator mode"""
            # scrape information from wrapped function
            filename = self._get_package_basename(inspect.getfile(func))
            lineno = inspect.getsourcelines(func)[-1]
            parent_function = func.__name__

            @functools.wraps(func)
            def inner(*args: Any, **kwargs: Any) -> T:
                with self.__class__(description=self._description, filename=filename, 
                                    lineno=lineno, parent_function=parent_function):
                    return func(*args, **kwargs)

            return inner

        def __enter__(self) -> None:
            # increment stacklevel
            with _lock:
                stacklevel = self.__class__.__stacklevel__ = self.__class__.__stacklevel__ + 1

            if self._parent_function is None:
                # this is not being used as a decorator, so inspect call stack instead
                caller = inspect.getframeinfo(inspect.stack()[1][0])
                self._parent_function = caller.function
                self._lineno = caller.lineno
                self._filename = self._get_package_basename(caller.filename)
                full_description = f'context {self._description} @ {self._filename}:{self._lineno} ({self._parent_function})'
                short_id = self._description
            else:
                full_description = f'function {self._parent_function} @ {self._filename}:{self._lineno}'
                short_id = self._parent_function

            # initialize XRAY
            settings = get_settings()
            self._use_xray = settings.XRAY_PROFILE
            if self._use_xray:
                from aws_xray_sdk.core import xray_recorder
                xray_recorder.begin_subsegment(short_id)

            # initialize log timer
            logger = cast(TraceLogger, logging.getLogger(__name__))
            if logger.isEnabledFor(logger.TRACE):
                self._timer = wakati.Timer(full_description, report_to=logger.trace,
                                           message='{stack_prefix:<5} {elapsed:.3f}s {name}',
                                           auto_unit=False)
                self._timer.stack_prefix = '+' * (stacklevel - 1)
                self._timer.__enter__()
                self._close_timer = True
            else:
                self._close_timer = False

        def __exit__(self, *exc: Any) -> bool:
            # decrement stacklevel
            with _lock:
                self.__class__.__stacklevel__ -= 1

            # close subcontexts
            if self._close_timer:
                self._timer.__exit__(*exc)

            if self._use_xray:
                from aws_xray_sdk.core import xray_recorder
                xray_recorder.end_subsegment()

            return False

    return TraceContextBase


_trace_type_pool = {threading.main_thread().ident: trace_context_factory()}


def trace(description=None):
    thread_id = threading.get_ident()
    with _lock:
        if thread_id not in _trace_type_pool:
            main_stacklevel = _trace_type_pool[threading.main_thread().ident].__stacklevel__
            _trace_type_pool[thread_id] = trace_context_factory(initial_stacklevel=main_stacklevel)

    return _trace_type_pool[thread_id](description)
